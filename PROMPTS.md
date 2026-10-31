# PROMPTS — copy-paste, in order

Start every session from the repo root with `claude`, then `/model sonnet`.

---

## SESSION 1

### P0 — scaffold (main session does it, no subagents)
```
Read CLAUDE.md, HANDOFF.md and agents/scaffolder/SPEC.md. Do Phase 0 yourself in this session,
no subagents. app/contracts.py, app/schema.sql and config/*.yaml already exist and are validated:
do not change them. When done run `make install && make check && make test-fast` and show the output.
Then git init (if needed), commit "phase 0: scaffold", and append a Phase 0 entry to the progress
log in HANDOFF.md. Stop and wait for my approval of the contracts (checkpoint H1).
```

### P1 — build the three engines in parallel
```
Approved. Start Phase 1: launch the mockworld, core-engine and brain subagents in parallel in the
background. Give each only this instruction: "Read agents/<your-name>/SPEC.md and
agents/<your-name>/HANDOFF.md, then build exactly that. Edit only the files you own."
While they run, do nothing else. When all three report back, summarise their reports in 10 lines,
list any CONTRACT CHANGE REQUESTs, and wait for me.
```

### P1.5 — integrate
```
Run `make seed && make test-fast`. Fix integration failures in the smallest possible way
(you may edit any file except contracts.py/schema.sql; if a contract change is truly needed,
propose it to me first). Then start the server in the background, run each scenario
(`make sim s=ato`, genuine, inbound, noresponse, injection), and check each case reaches the
state in SPEC §9. For ato also simulate the victim reply with
curl -X POST localhost:8000/victim/respond -H 'content-type: application/json' -d '{"case_id":"<id>","answer":"NOT_ME"}'
Show me a 5-line table: scenario, final state, T_protect. Commit "phase 1: engine",
append to the progress log, then stop.
```

### End of Session 1 (if usage is getting low at any point)
```
Stop work. Append an honest progress entry to HANDOFF.md (done, failing tests, the exact next
prompt to paste), commit with message "wip: <phase>", and stop.
```

---

## SESSION 2

### P2 — front ends in parallel
```
Read the progress log at the bottom of HANDOFF.md. Start Phase 2: launch the officer-console and
victim-app subagents in parallel in the background, each with the instruction "Read
agents/<your-name>/SPEC.md and agents/<your-name>/HANDOFF.md, then build exactly that.
Edit only the files you own." Make sure the server is running for them (make run in background).
When both report, summarise in 8 lines and wait for me.
```

### P2.5 — phone check (you do H3 first: USB debugging + `make android`)
```
The phone is connected. Run `adb devices` and `make android`. Then take a screenshot with
`adb exec-out screencap -p > /tmp/phone.png`, read it, and check the victim app loaded.
Launch the ato scenario and screenshot again within 5 seconds to confirm the verification
prompt appears. Fix only what's broken. Commit "phase 2: UIs".
```

### P3a — QA (cheap)
```
Run the qa subagent: "Read agents/qa/SPEC.md and agents/qa/HANDOFF.md and do exactly that."
When it reports, fix every failing test it found (app code), rerun `make test`, commit.
```

### P3b — independent review (the only Opus run)
```
Run the reviewer subagent: "Read agents/reviewer/SPEC.md and agents/reviewer/HANDOFF.md and do
exactly that." Do not fix anything yet. Show me the must-fix list from REVIEW.md.
```
Then, after you decide (H4):
```
Fix these REVIEW.md items: <list numbers>. Run make test. Commit "review fixes".
```

### P3c — demo kit
```
Run the demo-director subagent: "Read agents/demo-director/SPEC.md and
agents/demo-director/HANDOFF.md and do exactly that." Then run `make demo` once end-to-end and
tell me the measured T_protect and T_ready vs baseline. Append the final progress entry.
```

### P4 — final acceptance
```
Run the SPEC §12 demo acceptance checklist step by step, including step 8 with Ollama stopped
(`systemctl stop ollama` or kill the process; restart it afterwards). Report pass/fail per step.
```
