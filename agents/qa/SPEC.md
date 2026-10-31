# qa — SPEC (Phase 3, Haiku)

## Goal
Prove the safety claims and the five scenarios with automated tests. Find bugs; **don't fix app code**.

## Owns
`tests/test_e2e_*.py`, `tests/test_redteam_*.py`, `QA.md`. Read: SPEC §4–§6, §9, §12, `app/contracts.py`, `API_NOTES.md`, `tests/conftest.py`.

## Write
1. `tests/test_e2e_scenarios.py` — via `TestClient`, `GUARDIAN_LLM_MODEL=none`: each of the 5 scenarios reaches the SPEC §9 end state (send scripted replies through `/victim/respond`; approve decisions through `/decisions/{id}`); `T_protect` is set for fraud cases; audit chain verifies for every case.
2. `tests/test_redteam_policy.py` — call every Tier-3 function in `app.tools` → raises + `POLICY_BLOCKED` logged; every Tier-2 tool without a decision, with a REJECTED decision, with another case's APPROVED decision → blocked; `RELEASE_HOLD_TRUSTED` after SIM change → blocked.
3. `tests/test_redteam_llm.py` — 20 adversarial "LLM outputs" fed to `app.brain.guard.check` (OTP asks, refund promises, links, digits, police impersonation, Hinglish variants) → all rejected; 10 injection transcripts to `brain.classify_reply` → never YES_MINE/NOT_ME.
4. `tests/test_e2e_stream.py` — SSE `/events` yields at least one `case` message after a scenario (use a short read with timeout).

## Output
`QA.md`: table of failures — test, expected, actual, likely file:line. Then the pass/fail count.

## Done when
All tests written and run; QA.md lists every failure (or "none").
