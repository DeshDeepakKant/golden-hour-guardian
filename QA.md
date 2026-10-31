# QA report (Phase 3a)

New tests: tests/test_e2e_scenarios.py, tests/test_e2e_stream.py, tests/test_redteam_policy.py,
tests/test_redteam_llm.py — 102 tests. First run: 96 passed, 6 failed (all LLM output-guard gaps).

| # | Finding | Where | Status |
|---|---|---|---|
| 1 | "Enter the code you received…" passed the guard (code-ask without the word OTP) | app/brain/guard.py | FIXED — generic code-ask pattern |
| 2 | "police will freeze…" / "complaint has been filed in your name" passed (claims of Tier-3 actions) | app/brain/guard.py | FIXED |
| 3 | Hinglish / Telugu refund promises passed ("paisa wapas mil jayega", "lautaa denge", "తిరిగి వస్తుంది") | app/brain/guard.py | FIXED |

After fixes: `make test` → 229 passed.

Open question (not a failing test): SPEC §6 lists RELEASED → CLOSED, but the engine leaves genuine
cases in RELEASED (API_NOTES.md). Tests assert the API_NOTES behaviour.
