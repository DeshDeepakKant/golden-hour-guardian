# Golden Hour Guardian — build kit

An AI teammate for fraud response: **fraud alert → victim protected + evidence ready in minutes,
with a human officer approving every money decision.** Built for the Paytm Build for India AI
Hackathon (Track 3: Autonomous AI Teammates), on top of the idea of Paytm Pi's fraud detection.

## What's in this kit

| File | Read it when |
|---|---|
| `README.md` | now |
| `RESEARCH.md` | before you pitch — is it real, rules it follows, honest limits, sources |
| `SPEC.md` | product + technical spec (the agents build from this) |
| `HANDOFF.md` | master build plan: sessions, agents, models, human checkpoints, progress log |
| `PROMPTS.md` | copy-paste prompts for both Claude Code sessions, in order |
| `CLAUDE.md` | project memory Claude Code loads automatically (kept short on purpose) |
| `agents/<name>/SPEC.md` + `HANDOFF.md` | per-agent: what to build / inputs, outputs, exit report |
| `.claude/agents/*.md` | Claude Code subagent definitions (model per agent) |
| `.claude/settings.json` | pre-approved routine commands so background agents don't stall |
| `app/contracts.py`, `app/schema.sql`, `config/*.yaml` | **frozen contracts, already validated** |
| `scripts/preflight.sh`, `scripts/android.sh` | setup check, phone connection |

## Start (on your Linux PC)

```bash
unzip golden-hour-guardian-kit.zip && cd golden-hour-guardian
bash scripts/preflight.sh          # fix anything red
export ANTHROPIC_API_KEY=...       # optional: Claude wording; without it the demo runs on templates
claude                              # then: /model sonnet
```
Then paste **P0** from `PROMPTS.md` and follow the prompts in order.

## Model plan (why it fits in 2 sessions)

| Work | Model |
|---|---|
| Main session, core engine, LLM layer, both UIs | Sonnet |
| Synthetic data, tests, demo script | Haiku |
| One independent compliance review | Opus (once) |

Subagents spend from the same usage limit as your main session, so the kit keeps Opus to a single
focused run and pushes repetitive work to Haiku.
