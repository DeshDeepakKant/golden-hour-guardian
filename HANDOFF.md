# HANDOFF — master build plan

Read this first in every session. Product spec: `SPEC.md`. Copy-paste prompts: `PROMPTS.md`.

## 0. The budget: 2 Claude Code sessions

Each session has a usage limit, and **subagents spend from the same limit** as the main
conversation. So: the main session stays on **Sonnet**, cheap work goes to **Haiku**, and
**Opus** is used exactly once (the reviewer). The contracts (`app/contracts.py`, `app/schema.sql`,
`config/*.yaml`) are **already written and validated** — that saves the expensive design step.

| Session | Phases | Goal at the end |
|---|---|---|
| **1** | 0 → 1 → integration | Engine runs end-to-end on the `ato` scenario from curl; tests green; LLM + fallbacks work |
| **2** | 2 → 3 → rehearsal | Phone + officer console demo works; review fixes in; demo script + pitch notes ready |

If Session 1 finishes early, start Phase 2 in it.

## 1. Agent roster

| Agent | Model | Phase | Owns (may edit) | Why this model |
|---|---|---|---|---|
| main session (you + Claude) | **sonnet** | all | contracts (only via change rule), integration fixes, HANDOFF progress log | orchestration needs judgment, not Opus price |
| `scaffolder` (run **in main session**, not as a subagent) | sonnet | 0 | skeleton + stubs listed in `agents/scaffolder/SPEC.md` | small, needs full context |
| `mockworld` | **haiku** | 1 | `mocks/**`, `tests/test_mocks.py` | synthetic data + simple mocks |
| `core-engine` | **sonnet** | 1 | `app/**` except `app/brain/**`, `contracts.py`, `schema.sql`; `tests/test_core_*.py` | the hardest code: FSM, policy, audit, SSE |
| `brain` | **sonnet** | 1 | `app/brain/**`, `scripts/bench_llm.py`, `tests/test_brain_*.py` | prompts + guard + multilingual templates |
| `officer-console` | sonnet | 2 | `web/officer/**` | UI with live SSE |
| `victim-app` | sonnet | 2 | `web/victim/**`, `scripts/android.sh` | PWA + speech APIs + adb |
| `qa` | **haiku** | 3 | `tests/test_e2e_*.py`, `tests/test_redteam_*.py`, `QA.md` | writes tests, reports bugs, does **not** fix app code |
| `reviewer` | **opus** (once) | 3 | `REVIEW.md` only (read-only otherwise) | independent compliance + architecture review |
| `demo-director` | **haiku** | 3 | `scripts/demo.sh`, `DEMO.md`, `PITCH.md` | scripting + docs |

Each agent's detail: `agents/<name>/SPEC.md` (what to build) and `agents/<name>/HANDOFF.md`
(inputs, outputs, who receives them, exit report). Definitions: `.claude/agents/<name>.md`.

## 2. Dependency graph (what can run in parallel)

```
Phase 0 (main):            scaffolder ──► commit
                                │  contracts frozen, stubs exist
Phase 1 (parallel, bg):  ┌──────┼───────────┐
                         ▼      ▼           ▼
                    mockworld core-engine  brain
                         └──────┬───────────┘
Integration (main):        make test + make sim s=ato  ──► commit
Phase 2 (parallel, bg):     officer-console   victim-app
                                └──────┬──────┘
Phase 3 (sequential):   qa ─► main fixes ─► reviewer (opus) ─► main fixes ─► demo-director
```
Parallel agents never touch the same files (ownership column above), so no worktrees are needed.

## 3. Where the human (you) is needed

| # | When | What you do | Time |
|---|---|---|---|
| H0 | before Session 1 | Install prerequisites, run `bash scripts/preflight.sh`, fix anything red | 20 min |
| H1 | end of Phase 0 | Skim `app/contracts.py` tier table and SPEC §4; say "approved" | 5 min |
| H2 | end of Phase 1 | `make run`, then `make sim s=ato` in another terminal; open `/cases` JSON | 5 min |
| H3 | Phase 2 | Phone: USB debugging on, accept the RSA prompt, `make android`; install Hindi (and Telugu) voice in Android TTS settings; allow microphone in Chrome | 15 min |
| H4 | after reviewer | Read `REVIEW.md`; pick which findings to fix (you have the final say) | 10 min |
| H5 | end | Rehearse with `DEMO.md`; record a backup video with `scrcpy --record demo.mp4`; make 3–5 slides from `PITCH.md` | 60 min |

**In the product**, humans stay in the loop as: the **victim** (confirms fraud, files 1930/NCRP,
enters the acknowledgement number) and the **fraud officer** (approves every Tier-2 action).

## 4. Token-saving rules (follow them)

1. Main session on Sonnet: `/model sonnet`. Never switch the main session to Opus — only the reviewer runs on Opus.
2. `/clear` between phases. Before clearing, append to the progress log below; the next phase restarts from files, not chat history.
3. Subagents read **only** `CLAUDE.md` (auto), their own `agents/<name>/SPEC.md` + `HANDOFF.md`, `app/contracts.py`, and files they own. Never the whole repo.
4. Subagent final report ≤ 120 words. Long logs stay inside the subagent.
5. Tests: `make test-fast` (stops at first failure). Don't paste full logs into the main chat.
6. Use `/btw` for side questions so they don't enter the context.
7. Check what is running and on which model with `/tasks`; check context with `/context`.
8. If a subagent fails twice on the same thing: stop it, fix the spec line that caused it, rerun — don't keep correcting in chat.
9. Pre-approve routine commands (`.claude/settings.json` already allows pytest, make, uvicorn, curl to localhost, adb, git) so background subagents don't stall on prompts.

## 5. Contract change rule

If an agent needs a change to `app/contracts.py` or `app/schema.sql`, it must **not** edit them.
It ends with `CONTRACT CHANGE REQUEST: <what and why>` in its report. The main session decides,
edits the file, runs `make check`, and tells the affected agents (resume them with SendMessage).

## 6. Cut list (if usage runs low, drop from the top)

1. Telugu (keep en + hi)  2. Money-trail graph (keep a table)  3. Audit-chain verify button
4. `noresponse` scenario  5. LLM bench slide  6. Speech input (keep buttons; keep TTS)
Never cut: tier enforcement, fallback templates, the `ato` + `genuine` + `injection` scenarios, metrics vs baseline.

## 7. Definition of done (whole project)

SPEC §12 demo acceptance passes twice in a row, once with Ollama stopped. `make test` green.
`REVIEW.md` has no open "must-fix" items.

---

## 8. Progress log (append at the end of every phase)

<!-- Template:
### <date> <time> — Session N, Phase X — DONE / PARTIAL
- Done:
- Tests: <passed>/<total>, failing: ...
- Decisions made:
- Next step (exact prompt to paste):
-->

### 2026-10-31 — Session 1, Phase 0 — DONE
- Done: scaffold per agents/scaffolder/SPEC.md — .gitignore, package __init__s, app/config.py
  (SETTINGS/POLICY/BASELINE + GUARDIAN_DB / GUARDIAN_LLM_MODEL overrides; `db_path()` re-reads
  GUARDIAN_DB at call time so tests always hit a tmp DB), app/db.py, app/main.py (/health, router
  block, static mounts last), stub app/brain/api.py, stub mocks/{partners,seed,scenarios}.py,
  placeholder web/{officer,victim}/index.html, tests/conftest.py + tests/test_smoke.py, scripts/demo.sh.
- Tests: 5/5 passed (`make test-fast`). `make check`: contracts ok, 24 actions. Server serves
  /health, /officer, /victim (200).
- Decisions made: contracts define no explicit "forbidden set"; the smoke test pins the Tier-3 set
  to the five actions in CLAUDE.md. Contracts/schema/config unchanged.
- Noise only: pytest-asyncio warns `asyncio_default_fixture_loop_scope` unset; starlette warns about httpx.
- Next step: checkpoint H1 (approve contracts), then paste PROMPTS.md → P1.

### 2026-10-31 — Session 1, Phase 1 + integration — DONE
- Done: mockworld (68 users, 1205 txns, 5 scenarios), core-engine (all SPEC §7 endpoints, FSM,
  tiers, audit chain, SSE; API_NOTES.md for UI agents), brain (templates en/hi/te, guard, rules
  classifier, Ollama client, bench script). Integration needed no code fixes.
- Tests: 127/127 (`make test-fast`).
- Live run (GUARDIAN_VERIFY_TIMEOUT_S=15): ato→AWAITING_OFFICER T_protect 4.1 s → approve 3 decisions
  → CLOSED, dispute partner call logged, audit ok; genuine→RELEASED (friction 2.3 s); inbound→
  AWAITING_OFFICER T_protect 0.8 s; noresponse→AWAITING_OFFICER (officer_callback);
  injection→ASKS_REFUND (0.5)→officer_callback, nothing auto-done. All audit chains verify.
- Open: Ollama NOT installed on this machine → every brain call uses templates; live SLM path
  untested. Verify prompts held in memory (lost on restart). Genuine stays RELEASED (no CLOSED).
  Escalations reuse state NO_RESPONSE_ESCALATED (no other escalation state in frozen contract).
  Hindi/Telugu strings in app/brain/templates.py need a native-speaker check (H5).
- Next step: PROMPTS.md → P2.

### 2026-10-31 — Session 1, Phase 2 + phone check — DONE
- Done: officer console (web/officer/*, headless-Chrome checked light+dark), victim PWA
  (web/victim/*, checked on a moto g64 5G with en/hi/te voices).
- Phone check (P2.5): victim app loads via `make android`; ato verify prompt (Telugu, usr_ravi)
  visible 3.4 s after launch; "No, not me" → protected screen; case AWAITING_OFFICER.
- Note: running two UI agents on one server/usr_ravi cross-contaminated their manual tests —
  for demos, `/sim/reset` first and run one scenario per user at a time.
- Not verified: mic speech input, vibration.
- Next step: PROMPTS.md → P3a.

### 2026-10-31 — Session 1, Phase 3a/3b + review fixes — DONE
- QA: 102 new e2e/red-team tests; 6 guard gaps found and fixed (QA.md).
- Review (REVIEW.md): 4 must / 6 should / 6 nice. Human chose all must + should + N5; all fixed
  (status table at the end of REVIEW.md). N1–N4, N6 deferred.
- Tests: 272/272 (`make test`). Live rerun of all 5 scenarios: same expected end states; ato
  T_protect 4.0 s; rejecting EXTEND_HOLD now releases the hold.
- New behaviour to know: `/victim/respond` needs header `X-Guardian-Device: dev_<name>_phone` to
  count as trusted (API_NOTES.md); only button taps can be YES_MINE. Env: GUARDIAN_HOLD_MAX_S,
  GUARDIAN_HOLD_EXTEND_S. Use `make demo-run` on stage.
- Open: Ollama not installed → M4 bench + §12 step 8 can't be meaningfully run here.
- Next step: PROMPTS.md → P3c.
