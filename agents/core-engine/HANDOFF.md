# core-engine — HANDOFF

**Receives from:**
- scaffolder: `app/main.py`, `app/config.py`, `app/db.py`, empty `app/agents/`, `app/routes/`.
- mockworld (built in parallel): `mocks.seed.seed`, `mocks.scenarios.inject`, `mocks.partners.partners`. Until it lands, the scaffolder stubs exist — code against the interface in `app/contracts.py::PartnerGateway`.
- brain (built in parallel): `from app.brain.api import brain` with `BrainAPI` methods + `last_used_fallback`. The stub works now.

**Delivers to:**
- `officer-console` + `victim-app` (Phase 2): every endpoint in SPEC §7 and the SSE `StreamMessage` kinds: `event`, `case`, `decision`, `metrics`, `victim_prompt`. **Write `API_NOTES.md`** (≤60 lines) with one example JSON for each SSE kind and for `victim_prompt` variants (`verify`, `retry`, `protected`, `ncrp_guide`, `released`, `done`). UI agents read only that file plus contracts.
- `qa`: tool functions importable from `app.tools` for red-team tests.

**Exit report (≤120 words):** endpoints done, tests passed/total, any CONTRACT CHANGE REQUEST, known gaps.

**Pitfalls:**
- SQLite + asyncio: one connection per request/task or a lock; WAL is on.
- Tasks must survive test teardown — cancel pending timeout/expiry tasks in a shutdown hook.
- Don't let SSE handlers hold DB connections.
- Make `/sim/reset` cancel all running case tasks before reseeding.
