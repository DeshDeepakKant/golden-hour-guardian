# qa — HANDOFF

**Receives from:** the integrated app after Phase 2 (main session), `API_NOTES.md`, conftest fixtures.

**Delivers to:** main session — `QA.md` with failures and likely locations. Main fixes app code, then reruns `make test`.

**Must not:** edit anything under `app/`, `mocks/`, `web/`; weaken an assertion to make a test pass; mark a test `skip` without writing why in QA.md.

**Exit report (≤120 words):** tests written, pass/fail counts, top 3 failures in one line each.

**Pitfalls:** async tasks + TestClient — poll `GET /cases/{id}` up to ~3 s for state changes instead of sleeping fixed times; reset state between tests with `/sim/reset`.
