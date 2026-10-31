# reviewer — SPEC (Phase 3, Opus — the only Opus run, keep it focused)

## Goal
An independent, skeptical review before the demo: would a Paytm fraud-ops lead or an RBI-minded
judge find a hole? You did not write this code; judge it on its own terms.

## Owns
`REVIEW.md` only. Read-only everywhere else. You may run `make test` and `grep`.

## Read (in this order, stop when you have enough)
`SPEC.md` §4, §5, §6, §8, §11 → `RESEARCH.md` §3, §5 → `app/policy.py`, `app/tools.py`, `app/fsm.py`,
`app/agents/*.py`, `app/brain/guard.py`, `app/brain/api.py` → `web/victim/app.js` (copy text) →
`web/officer/app.js` (labels) → `QA.md`. Skip CSS, mocks, and tests' internals.

## Check
1. **Tier integrity** — any path where a Tier-2/3 side effect can run without `policy.check` passing (direct partner calls, missing decision check, wrong case id accepted).
2. **LLM authority** — can model output change state, pick an action, or inject numbers/links that reach the victim unguarded?
3. **Trusted-channel rule** — can a "yes" from an untrusted channel release a hold?
4. **Privacy** — raw names/mobiles/VPAs/amounts/IDs in prompts sent to the Claude API, or in logs, SSE or the evidence pack beyond masking.
5. **Victim copy** — any promise ("you'll get your money back"), "frozen", fear language, unclear 1930 steps, wrong links.
6. **Branding/impersonation** — anything that looks like Paytm or a bank.
7. **Demo robustness** — Claude API down / no key, Wi-Fi down, phone screen lock, TTS autoplay, SSE reconnect.
8. **Claims** — every number in the UI/docs traceable to RESEARCH.md or a measured metric; baseline labelled as simulated.

## Output — `REVIEW.md`
- **Must-fix** (blocks the demo or breaks a safety claim), **Should-fix**, **Nice** — max 25 items total, each: file:line, problem, concrete fix (≤3 lines).
- **Judge Q&A** — 8 hard questions a judge may ask, each with a 2-sentence honest answer.
