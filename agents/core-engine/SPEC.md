# core-engine — SPEC (Phase 1, Sonnet)

## Goal
The Guardian engine: API, case state machine, policy tiers, tools, runtime roles, audit chain,
event stream and metrics. This is the heart of the demo — correctness over features.

## Owns
`app/**` **except** `app/brain/**`, `app/contracts.py`, `app/schema.sql`.
Tests: `tests/test_core_*.py`. Read: `SPEC.md` §3–§10, `app/contracts.py`, `config/*.yaml`.

## Build (suggested files)
| File | Responsibility |
|---|---|
| `app/repo.py` | `LedgerRepo` over SQLite (txns, profile, device timeline, payee fan-in count) |
| `app/store.py` | Case / Decision / EvidencePack persistence (JSON column = full pydantic model) |
| `app/audit.py` | `append(case_id, type, actor, tier, payload) -> CaseEvent` with hash chain: `hash = sha256(prev_hash + canonical_json(event_without_hash))`, canonical = `sort_keys=True, separators=(",",":"), default=str`; `verify(case_id) -> {ok, length, broken_at}` |
| `app/bus.py` | In-process pub/sub (asyncio queues): global channel for the console, per-user channel for the victim app; `publish(StreamMessage)` |
| `app/policy.py` | `check(action, case, actor, decision_id=None) -> PolicyResult(allowed, tier, reason)`. Tier 3 → always deny + `POLICY_BLOCKED`. Tier 2 → deny unless `decision_id` refers to an APPROVED decision for this case and action. `RELEASE_HOLD_TRUSTED` denied if `SIM_CHANGE_72H` in signals or channel ≠ trusted. `EXTEND_HOLD` needed past `hold.max_without_officer_minutes`. |
| `app/tools.py` | The **only** place that calls `mocks.partners`. Each tool: `policy.check` → partner call → `audit.append` → `bus.publish`. One function per `Action` that has a side effect. Tier-3 actions have functions that only raise `PolicyBlocked` (so red-team tests can call them). |
| `app/fsm.py` | Whitelist `TRANSITIONS: dict[CaseState, set[CaseState]]` per SPEC §6. `transition(case, to, actor, reason)` validates, sets the matching `t_*`, saves, logs `STATE_CHANGED`, publishes `case`. Illegal → raise `IllegalTransition` + log. |
| `app/agents/sentinel.py` | Recompute signals from the repo (new device, SIM change ≤72 h, first-time payee, payee fan-in ≥20 in 60 min, ≥3 txns in 10 min, geo jump, amount > 5× user median, 00:00–05:00 IST). Score = `max(alert.score, 1 − Π(1 − wᵢ))`. Path per `config/policy.yaml`. Pick channel (trusted device unless only voice possible). Ask brain for `explain_risk`. |
| `app/agents/shield.py` | Tier-1 containment: temp hold (auto-expire task), revoke the suspicious device session, suppress marketing (Conductor-lite). Expiry task releases the hold unless state is CONFIRMED_FRAUD or later. |
| `app/agents/voice.py` | Build the victim prompt from `brain.verification_messages`, publish `victim_prompt` on the user channel, store it for `GET /victim/{user_id}/pending`; start timeout task; on reply: buttons map directly, transcripts go through `brain.classify_reply`. `UNSURE` → 1 retry; `ASKS_REFUND`/`DISTRESS`/`OTHER` → OFFICER_CALLBACK decision, no auto action. |
| `app/agents/scribe.py` | Build `EvidencePack` (masking: name → `R*** K***`, mobile → `90******21`), NCRP field map (category, sub-category "UPI related", txn IDs, amounts, timestamps IST, suspect VPAs, short description), narratives via brain; then publish the guidance prompt (`brain.ncrp_guidance`) to the victim. NCRP field names are approximations — label them "demo field map". |
| `app/agents/desk.py` | Create Tier-2 decisions with `brain.decision_rationale`: on CONFIRMED_FRAUD → RAISE_DISPUTE, EXTEND_HOLD, SHARE_EVIDENCE_WITH_BANK; on untrusted YES_MINE → RELEASE_HOLD_UNTRUSTED; callbacks as above. `apply(decision_id, OfficerDecisionIn)` runs the tool with the decision id. Close the case when no PENDING decisions remain. |
| `app/orchestrator.py` | Async pipeline per case using `asyncio.create_task`; idempotent on `alert_id`; never blocks request handlers. |
| `app/metrics.py` | `MetricsSummary` per SPEC §10; baseline sums from `config/baseline.yaml`. |
| `app/routes/*.py` | All endpoints in SPEC §7, incl. SSE (`sse-starlette`, 15 s heartbeat) and `/sim/scenario/{name}?auto_reply=true&delay=4` (posts the scenario's `scripted_reply` after `delay` s for unattended demos). Include routers in `app/main.py` before the static mounts. `/health` reports `llm: up|fallback` (ask brain). |

## Rules
- After every brain call, if `brain.last_used_fallback` → `audit.append(LLM_FALLBACK_USED)`.
- The LLM output never chooses a transition or an action; only enums from `classify_reply` feed the FSM, through fixed mappings.
- Victim-report origin: create case → `CONFIRMED_FRAUD` directly (SPEC §6).
- All money stays in paise; format `₹24,999` only at the edges (brain/templates/UI).
- The queued marketing push from the `ato` scenario must be sent via `partners.send_push` 20 s after injection (it should come back SUPPRESSED).

## Tests (`tests/test_core_*.py`, run with `GUARDIAN_LLM_MODEL=none`)
policy: every Tier-3 tool raises and logs; Tier-2 without/with wrong/with approved decision · fsm: illegal transitions raise · audit: chain verifies, tampering one row breaks it at that seq · flow: `ato` + NOT_ME → AWAITING_OFFICER with 3 decisions; approve all → CLOSED; `genuine` + YES_MINE → RELEASED; `injection` transcript → OFFICER_CALLBACK decision and no hold release; victim-report → CONFIRMED_FRAUD path · metrics: T_protect computed.

## Done when
`pytest -q tests/test_core_*.py` passes and `make sim s=ato` followed by a NOT_ME reply produces
the SPEC §9 path visible in `GET /cases/{id}`.
