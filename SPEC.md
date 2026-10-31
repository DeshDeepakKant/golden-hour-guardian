# SPEC — Golden Hour Guardian

> One line: **from fraud alert to victim protected and evidence ready — in minutes, with a human officer making every money decision.**
>
> Do **not** say "money frozen". The agent never freezes anyone else's account (see §4, Tier 3).

## 1. Problem

When a UPI account is taken over, money moves through mule accounts within minutes. The national
cyber-fraud system (1930 / NCRP / CFCFRMS) can stop funds that are still in the system, but only
if the victim reports fast and with the right details. Today, between a fraud model raising an
alert and the victim actually filing, there are queues, missed calls, manual evidence gathering
and confused victims. Details and sources: RESEARCH.md.

## 2. What we build (scope)

A backend "AI teammate" plus two front ends:

| Part | Who uses it | What it does |
|---|---|---|
| Guardian engine (FastAPI) | system | Receives fraud alerts / victim reports, runs the case state machine, calls tools, enforces policy tiers, writes a hash-chained audit log, streams events |
| Victim app (PWA on Android) | the customer | Verified "was this you?" prompt with voice (TTS) + tap/speak answer, protection status, step-by-step 1930/NCRP guidance with a prefilled summary, records the acknowledgement number |
| Officer console (web) | fraud officer | Live queue with golden-hour clocks, case timeline, money trail, evidence pack, Tier-2 approve/reject, audit chain check, live metrics vs baseline, scenario launcher |

**Out of scope (say so on stage):** real bank/NPCI/CFCFRMS integration, real calls/SMS, real
customer data, credit or claims decisions, freezing third-party accounts, filing complaints for the victim.

## 3. Runtime roles (the "teammates" inside the engine)

These are logical roles implemented as modules, not separate LLM agents. The LLM is used only
for wording, classification and summaries; all decisions are code + policy.

| Role | Module | Job |
|---|---|---|
| **Sentinel** | `app/agents/sentinel.py` | Triage: score + signals → path (dismiss / verify / hold+verify). Picks trusted channel. |
| **Shield** | `app/agents/shield.py` | Tier-1 containment on the victim's own account: temp hold, revoke suspicious session, suppress marketing. |
| **Voice** | `app/agents/voice.py` | Verification dialogue in en/hi/te via the victim app; classifies replies; never asks for OTP/PIN. |
| **Scribe** | `app/agents/scribe.py` | Builds the evidence pack: money trail, device timeline, signals, NCRP-ready fields, narratives. |
| **Desk** | `app/agents/desk.py` | Creates Tier-2 decisions with rationale, tracks officer SLA, applies approved actions. |
| **Conductor-lite** | inside `shield.py` | Holds marketing/cross-sell messages to this customer while the case is open. |

## 4. Action tiers (enforced by `app/policy.py`, table in `app/contracts.py::ACTION_TIERS`)

**Tier 1 — agent acts alone** (reversible, victim-side, informational)
read ledger · score risk · temporary hold on the victim's **own** outgoing payments (auto-expires) ·
release that hold when the victim confirms on a **trusted** channel · revoke a suspicious session/device ·
notify/verify the victim · build evidence pack · show 1930/NCRP guidance + prefilled summary ·
suppress marketing · request an officer decision.

**Tier 2 — agent prepares, human officer approves**
raise dispute via the partner bank channel · extend a hold beyond policy limit · release a hold when
the channel is untrusted (e.g. recent SIM change) · share evidence with the bank nodal officer ·
any refund/credit/liability decision · restore access · flag a payee internally ·
officer callback to the victim (refund requests, distress, unclear answers).

**Tier 3 — impossible in code**
freeze a beneficiary/third-party account · file a police complaint on the victim's behalf ·
ask for OTP/PIN/CVV/password · promise a refund · contact the payee.

Policy engine contract: `policy.check(action, case, actor) -> PolicyResult(allowed, tier, reason)`.
Tier 3 → always blocked + `POLICY_BLOCKED` event. Tier 2 → blocked unless called with an
`APPROVED` decision id. Every check is logged.

**Assumption to verify with a real partner:** an automatic temporary hold on a customer's own
outgoing payments at very high risk (≥0.85) before they confirm. Configurable in `config/policy.yaml`.

## 5. Trusted channel rule (important realism point)

In an account takeover the attacker may control the new device and, after a SIM swap, the phone
number. So verification goes to the **previously trusted device** (in-app). If `SIM_CHANGE_72H` is
present, a voice answer to the registered number is **not** trusted: a "yes it was me" on that
channel cannot release the hold automatically — it becomes a Tier-2 decision.

## 6. Case state machine (`app/fsm.py`)

```
NEW ─► TRIAGED ─┬─► DISMISSED ───────────────────────────────► CLOSED
                ├─► VERIFYING ──────────┐
                └─► HELD_PENDING_VERIFY ┤
                                        ├─► CONFIRMED_GENUINE ─► RELEASED ─► CLOSED
                                        ├─► CONFIRMED_FRAUD ─► CONTAINED ─► EVIDENCE_READY ─► AWAITING_OFFICER ─► CLOSED
                                        └─► NO_RESPONSE_ESCALATED ─► AWAITING_OFFICER
```
- Transitions are a whitelist table; anything else raises and logs.
- `UNSURE` → one retry with simpler wording, then treat as `NO_RESPONSE_ESCALATED`.
- `ASKS_REFUND` / `DISTRESS` / `OTHER` → never auto-acts; adds an officer callback decision.
- Victim-report origin (`POST /webhooks/victim-report`) skips verification: the victim has already said "not me", so go to `CONFIRMED_FRAUD` (still on the trusted-channel rule for any release).
- Victim guidance (1930/NCRP) runs as soon as `CONFIRMED_FRAUD`, in parallel with evidence building.
- Every state change sets the matching `t_*` timestamp on the case (used by metrics).

## 7. API (owned by core-engine; all JSON; models in contracts.py)

| Method & path | Body → Response | Notes |
|---|---|---|
| `POST /webhooks/fraud-alert` | `FraudAlert` → `{case_id}` 202 | idempotent on `alert_id` |
| `POST /webhooks/victim-report` | `VictimReport` → `{case_id}` 202 | inbound "paise kat gaye" |
| `GET /cases` | → `[Case]` | `?state=` filter |
| `GET /cases/{id}` | → `{case, events, decisions, evidence}` | |
| `GET /officer/queue` | → pending `Decision`s with case summary + SLA age | |
| `POST /decisions/{id}` | `OfficerDecisionIn` → `Decision` | applies the Tier-2 action if approved |
| `GET /victim/{user_id}/pending` | → current prompt for the victim app or `null` | |
| `POST /victim/respond` | `VictimResponse` → `{state}` | button or transcript |
| `POST /victim/ncrp-ack` | `NcrpAck` → `{ok}` | |
| `GET /events` | SSE of `StreamMessage` | officer console |
| `GET /victim/{user_id}/events` | SSE of `StreamMessage` | victim app |
| `GET /metrics/summary` | → `MetricsSummary` | |
| `GET /audit/{case_id}/verify` | → `{ok, length, broken_at}` | recomputes hash chain |
| `POST /sim/scenario/{name}` | → `{case_id}` | `ato`, `genuine`, `inbound`, `noresponse`, `injection` |
| `POST /sim/reset` | → `{ok}` | reseed DB |
| `GET /officer`, `GET /victim` | static pages | served from `web/` |
| `GET /health` | → `{ok, llm: "up"/"fallback"}` | |

Mock partner calls are in-process (`mocks/partners.py`) and recorded in `partner_calls`.

## 8. LLM layer (`app/brain/`, owned by brain)

- Anthropic Claude API via the official `anthropic` Python SDK, model `claude-opus-5-5` at effort `low` (config: `config/settings.yaml` `llm.model` / `llm.effort`; `llm.model: none` forces templates). Needs `ANTHROPIC_API_KEY` and internet access. JSON output, 8 s budget per call (`llm.timeout_s`), no retries.
- No key / no network / timeout / refusal / bad JSON / guard failure → deterministic en/hi/te template + `LLM_FALLBACK_USED`.
- Uses: `explain_risk`, `verification_messages`, `classify_reply`, `evidence_narratives`, `decision_rationale` (signatures in `BrainAPI`).
- **Facts come from code.** Prompts receive a small, masked fact sheet (signal codes/phrases, masked name like `R*** K***`; no raw names, mobile numbers, VPAs, amounts or IDs). Outputs use placeholders like `{amount}` that code fills.
- **Privacy:** this data is sent to Anthropic's API — the masked fact sheet and, for `classify_reply`, the victim's reply with digit runs redacted. Production needs a DPA / data-residency review with the partner.
- **Guard** (`app/brain/guard.py`): schema check + banned patterns from `config/policy.yaml`. Fail → deterministic template + `LLM_FALLBACK_USED` event.
- **Prompt injection:** victim text is wrapped as data (`<victim_text>…</victim_text>`), output is only an enum + confidence for `classify_reply`. The LLM has no tool access.
- **Fallback-first:** the whole demo must work with `llm.model: none` (templates only).
- **Bench:** `scripts/bench_llm.py` prints Claude API p50/p95 latency and fallback rate per function — show it on a slide.

## 9. Data (owned by mockworld)

Synthetic users (Hyderabad + other cities), devices, 30 days of normal transactions, mule payees
with fan-in spikes. All names/numbers obviously fake. Scenarios:

| Name | Story | Expected path |
|---|---|---|
| `ato` | New device in another city + SIM change 2 h ago, 3 rapid transfers to first-time payees that received from 40+ new senders in the last hour | score ≈0.93 → hold → verify on trusted device → NOT_ME → contained → evidence → guidance → officer approves dispute |
| `genuine` | Big festive purchase from known device to a new merchant | score ≈0.55 → verify → YES_MINE → released (measures friction) |
| `inbound` | Victim reports in Hindi: money deducted, didn't do it | victim-report path → confirmed fraud → same as `ato` |
| `noresponse` | High risk, victim never answers | hold stays within limit → escalated to officer |
| `injection` | Victim text tries to order a refund / override rules | classified `ASKS_REFUND`, nothing auto-done, officer callback decision, `POLICY_BLOCKED` if anything tries Tier 3 |

## 10. Metrics (`app/metrics.py`)

- **T_protect** = `t_contained − t_alert` (headline). **T_ready** = `max(t_evidence_ready, t_guided_1930) − t_alert`.
- % fraud cases protected under 10 min · genuine-user friction (`t_released − t_alert`) · Tier-1 actions vs Tier-2 decisions vs Tier-3 blocks.
- Baseline from `config/baseline.yaml` — **labelled "simulated manual baseline (assumptions)" in the UI.**

## 11. Compliance mapping (show as one slide)

| Concern | How the design handles it |
|---|---|
| CFCFRMS/1930 freezes are police-initiated | We never freeze; we guide the victim to 1930/NCRP with a prefilled summary; victim files |
| RBI customer liability (report fast) | Fast reporting supported; liability/refund decisions are Tier-2 human only |
| RBI FREE-AI: human oversight, auditability | Tier table in code, officer approvals, hash-chained audit log, AI fallback logged |
| DPDP Act: purpose limitation, minimisation | Masked fact sheet + digit-redacted replies are the only data sent to the Claude API (no raw names, numbers, VPAs, amounts, IDs); production needs a DPA / data-residency review; retention note |
| Impersonation scams | Never asks OTP/PIN; in-app verified channel; guard blocks risky phrases |

## 12. Demo acceptance (end-to-end check)

1. `make seed && make run`, phone connected with `make android`.
2. Officer console → launch `ato`. Phone rings (vibrate + TTS) within 5 s.
3. Tap "No, not me" → console shows CONTAINED with T_protect < 60 s; evidence pack visible; phone shows 1930 guidance with copyable summary.
4. Officer approves the dispute decision → decision APPROVED, partner call logged, audit chain verifies.
5. Launch `genuine` → "Yes, it was me" → released; friction time shown.
6. Launch `injection` → nothing auto-done; officer callback appears.
7. Metrics header shows our medians vs the simulated baseline.
8. Unset `ANTHROPIC_API_KEY` (or set `llm.model: none`) → repeat step 2 → still works on templates (`LLM_FALLBACK_USED` visible).
