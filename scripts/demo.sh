#!/usr/bin/env bash
# One-command demo check for Golden Hour Guardian.
# Needs a running server: `make demo-run` (stage) or `make run` (dev). Does not start one.
# Resets the synthetic data, runs ato -> genuine -> injection with scripted victim replies
# (?auto_reply=true posts as the trusted device), approves ato's Tier-2 decisions as the officer,
# verifies each audit chain, then prints a result table and metrics next to the
# simulated manual baseline (assumptions). Exits 1 on any unexpected state.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${GUARDIAN_URL:-http://127.0.0.1:8000}"
TIMEOUT_S="${DEMO_TIMEOUT_S:-60}"
if [ -x "$ROOT/.venv/bin/python" ]; then PY="$ROOT/.venv/bin/python"; else PY="$(command -v python3 || true)"; fi
[ -n "$PY" ] || { echo "python3 not found (run: make install)"; exit 1; }

FAILS=0
fail() { echo "  FAIL: $*"; FAILS=$((FAILS + 1)); }
die()  { echo "FATAL: $*"; exit 1; }
api_get()       { curl -sf -m 10 "$BASE$1"; }
api_post()      { curl -sf -m 10 -X POST "$BASE$1"; }
api_post_json() { curl -sf -m 10 -X POST "$BASE$1" -H 'content-type: application/json' -d "$2"; }
# jf '<expr over d>' : reads JSON on stdin, prints the expression (stdlib only)
jf() { "$PY" -c 'import json,sys; d=json.load(sys.stdin); print(eval(sys.argv[1]))' "$1"; }

echo "== 0. server check"
HEALTH="$(api_get /health)" || die "server not answering at $BASE. Start it with: make demo-run"
[ "$(echo "$HEALTH" | jf 'd["ok"]')" = "True" ] || die "/health not ok: $HEALTH"
LLM_MODE="$(echo "$HEALTH" | jf 'd["llm"]')"
if [ "$LLM_MODE" = "up" ]; then LLM_LABEL="Claude up (Claude API)"; else LLM_LABEL="templates (LLM $LLM_MODE)"; fi
echo "  $BASE ok — wording: $LLM_LABEL"

echo "== 1. reset synthetic data"
api_post /sim/reset >/dev/null || die "POST /sim/reset failed"
echo "  reset ok"

launch() {  # launch <scenario> -> prints case_id
  local out
  out="$(api_post "/sim/scenario/$1?auto_reply=true&delay=4")" || return 1
  echo "$out" | jf 'd["case_id"]'
}

wait_state() {  # wait_state <case_id> <comma-separated states> -> prints last state seen
  local cid="$1" want="$2" t=0 st=""
  while [ "$t" -lt "$TIMEOUT_S" ]; do
    st="$(api_get "/cases/$cid" 2>/dev/null | jf 'd["case"]["state"]' 2>/dev/null)"
    case ",$want," in *",$st,"*) echo "$st"; return 0 ;; esac
    sleep 1; t=$((t + 1))
  done
  echo "${st:-TIMEOUT}"; return 1
}

approve_pending() {  # approve_pending <case_id> -> approves every PENDING decision, prints ids
  local cid="$1" ids id rc=0
  ids="$(api_get "/cases/$cid" | jf '" ".join(x["decision_id"] for x in d["decisions"] if x["status"]=="PENDING")')" || return 1
  for id in $ids; do
    api_post_json "/decisions/$id" "{\"decision_id\":\"$id\",\"approve\":true,\"officer\":\"officer_demo\",\"note\":\"approved by scripts/demo.sh\"}" >/dev/null || { rc=1; }
  done
  echo "$ids"
  return $rc
}

echo "== 2. ato: alert -> hold -> victim taps NOT_ME on trusted phone -> officer approves"
ATO_ID="$(launch ato)" || die "could not launch ato"
echo "  case $ATO_ID; waiting for AWAITING_OFFICER"
ST="$(wait_state "$ATO_ID" AWAITING_OFFICER)"; echo "  state: $ST"
IDS="$(approve_pending "$ATO_ID")" || fail "approving ato decisions failed"
echo "  approved decisions: $IDS"
ST="$(wait_state "$ATO_ID" CLOSED)"; echo "  state: $ST"

echo "== 3. genuine: victim taps YES_MINE on trusted phone -> released"
GEN_ID="$(launch genuine)" || die "could not launch genuine"
ST="$(wait_state "$GEN_ID" RELEASED)"; echo "  state: $ST"

echo "== 4. injection: refund-order text -> nothing auto-done, officer callback"
INJ_ID="$(launch injection)" || die "could not launch injection"
ST="$(wait_state "$INJ_ID" AWAITING_OFFICER)"; echo "  state: $ST"

echo "== 5. result table"
"$PY" - "$BASE" "$LLM_LABEL" "$ATO_ID" "$GEN_ID" "$INJ_ID" <<'PY'
import json, sys, urllib.request
from datetime import datetime

base, llm_label, ids = sys.argv[1], sys.argv[2], sys.argv[3:6]
RUNS = [("ato", "CLOSED"), ("genuine", "RELEASED"), ("injection", "AWAITING_OFFICER")]
TIER3 = {"freeze_beneficiary", "file_police_complaint", "request_otp_pin", "promise_refund", "contact_payee"}


def get(path):
    with urllib.request.urlopen(base + path, timeout=10) as r:
        return json.load(r)


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def secs(a, b):
    return round((b - a).total_seconds(), 1) if a and b else None


def fmt(v):
    return "-" if v is None else f"{v:.1f} s"


fails = 0
rows = []
for (name, want), cid in zip(RUNS, ids):
    d = get(f"/cases/{cid}")
    c, events, decisions = d["case"], d["events"], d["decisions"]
    t_alert = ts(c["t_alert"])
    t_protect = secs(t_alert, ts(c["t_contained"]))
    guided = [ts(c["t_evidence_ready"]), ts(c["t_guided_1930"])]
    t_ready = secs(t_alert, max(guided)) if all(guided) else None
    fallbacks = sum(1 for e in events if e["type"] == "LLM_FALLBACK_USED")
    problems = []
    if c["state"] != want:
        problems.append(f"state {c['state']} != expected {want}")
    audit = get(f"/audit/{cid}/verify")
    if not audit.get("ok"):
        problems.append(f"audit chain broken at {audit.get('broken_at')}")
    if name == "ato" and any(x["status"] != "APPROVED" for x in decisions):
        problems.append("ato has decisions that are not APPROVED")
    if name == "injection" and not any(x["action"] == "officer_callback" for x in decisions):
        problems.append("injection has no officer_callback decision")
    if any(x["action"] in TIER3 for x in decisions):
        problems.append("a Tier-3 action reached the decision queue")
    fails += len(problems)
    rows.append((name, c["state"], t_protect, t_ready, fallbacks, problems))

print(f"  wording: {llm_label}")
print(f"  {'scenario':<10} {'final state':<19} {'T_protect':>10} {'T_ready':>10}  {'fallback used?':<15} check")
for name, st, tp, tr, fb, problems in rows:
    fb_s = f"yes ({fb})" if fb else "no"
    chk = "PASS" if not problems else "FAIL: " + "; ".join(problems)
    print(f"  {name:<10} {st:<19} {fmt(tp):>10} {fmt(tr):>10}  {fb_s:<15} {chk}")

m = get("/metrics/summary")
print()
print("  metrics since reset (simulated manual baseline (assumptions), config/baseline.yaml):")
print(f"    median T_protect   {fmt(m['median_t_protect_s']):>10}   baseline {fmt(m['baseline_median_t_protect_s'])}")
print(f"    median T_ready     {fmt(m['median_t_ready_s']):>10}   baseline {fmt(m['baseline_median_t_ready_s'])}")
pct = m["pct_protected_under_10min"]
print(f"    fraud protected under 10 min: {'-' if pct is None else f'{pct:.1f}%'} ({m['cases_fraud_confirmed']} confirmed of {m['cases_total']} cases)")
print(f"    genuine friction (median)   {fmt(m['median_genuine_friction_s']):>10}")
print(f"    AI actions (Tier 1) {m['t1_actions']} · officer decisions (Tier 2) {m['t2_decisions']} · blocked (Tier 3) {m['t3_blocked']}")
sys.exit(min(fails, 100))
PY
REPORT_RC=$?
FAILS=$((FAILS + REPORT_RC))

echo
if [ "$FAILS" -eq 0 ]; then
  echo "DEMO CHECK PASSED"
  exit 0
fi
echo "DEMO CHECK FAILED ($FAILS problem(s))"
exit 1
