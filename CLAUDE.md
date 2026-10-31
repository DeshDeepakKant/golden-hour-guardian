# Golden Hour Guardian — project memory

Hackathon prototype (Paytm Build for India AI Hackathon, Track 3). An AI teammate that turns a
fraud alert into a protected victim + a ready evidence pack in minutes, with a human fraud
officer approving every money/status decision. Full spec: SPEC.md. Build plan: HANDOFF.md.

## Stack
Python 3.11+, FastAPI, SQLite (stdlib sqlite3), pydantic v2, SSE (sse-starlette), Ollama (qwen3:4b).
Frontends are plain HTML + vanilla JS (no build step, no npm). Phone = Chrome via `adb reverse`.

## Commands
- `make install` · `make seed` · `make run` (port 8000) · `make test` · `make sim s=ato`
- Officer console: http://127.0.0.1:8000/officer · Victim app: http://127.0.0.1:8000/victim
- Phone: `make android` (adb reverse tcp:8000 tcp:8000, opens the victim app)

## Hard rules (IMPORTANT)
- `app/contracts.py` and `app/schema.sql` are FROZEN. Only the main session may change them.
- Each subagent edits ONLY the paths it owns (see its agents/<name>/SPEC.md).
- Tier-3 actions (freeze beneficiary, file police complaint, ask OTP/PIN, promise refund,
  contact payee) must be impossible in code, not just discouraged in prompts.
- The LLM never produces amounts, IDs or dates; code fills them into templates.
- The LLM never decides state transitions; the FSM in app/fsm.py does.
- Synthetic data only. Neutral "Guardian" branding — never copy Paytm or bank logos/UI.
- Money = integer paise. Time = UTC in storage, IST in UI.

## Working style
- Run `make test-fast` after each change set; show the output, don't claim success.
- Subagent final reports: max 120 words — files changed, checks + results, open issues.
- Keep diffs small. No new dependencies without updating requirements.txt.
- When compacting, preserve: current phase, files changed, failing tests, open decisions.
