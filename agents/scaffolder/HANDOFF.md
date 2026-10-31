# scaffolder — HANDOFF

**Receives from:** the kit (contracts, configs, docs already in the repo).

**Delivers to:**
- `mockworld` → `app/db.py`, stub `mocks/seed.py`, `mocks/partners.py`, `mocks/scenarios.py` (mockworld takes ownership of `mocks/**`).
- `core-engine` → `app/main.py`, `app/config.py`, `app/db.py`, empty `app/agents/`, `app/routes/` (core-engine takes ownership).
- `brain` → stub `app/brain/api.py` with the exact `BrainAPI` method names (brain takes ownership of `app/brain/**`).
- `qa` → `tests/conftest.py` fixtures.

**Ownership after Phase 0:** scaffolder owns nothing; files pass to the agents above.

**Exit report (≤120 words):** files created, `make test-fast` result, anything in the contracts that looked inconsistent (report, don't edit).

**Pitfalls:**
- `StaticFiles(html=True)` mounts must be added *after* API routes or they shadow them.
- Tests must never use `data/guardian.db`; always the tmp DB from `GUARDIAN_DB`.
- Keep the stubs import-light: no Claude API/network calls in stubs.
