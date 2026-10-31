# scaffolder — SPEC (Phase 0, run in the MAIN session, Sonnet)

## Goal
Create the empty-but-runnable skeleton so three agents can build in parallel without touching
each other's files. Do **not** implement business logic.

## Already exists — do not modify
`app/contracts.py`, `app/schema.sql`, `config/policy.yaml`, `config/baseline.yaml`,
`config/settings.yaml`, `requirements.txt`, `Makefile`, all `*.md` docs, `.claude/`, `agents/`,
`scripts/preflight.sh`, `scripts/android.sh`.

## Create
| File | Content |
|---|---|
| `.gitignore` | `.venv/`, `__pycache__/`, `data/*.db*`, `*.mp4`, `.pytest_cache/` |
| `app/__init__.py`, `app/agents/__init__.py`, `app/routes/__init__.py`, `mocks/__init__.py`, `scripts/__init__.py`, `tests/__init__.py` | empty |
| `app/config.py` | Load the three YAML files once into plain dicts: `SETTINGS`, `POLICY`, `BASELINE`. Env var `GUARDIAN_DB` overrides `app.db_path`. Env var `GUARDIAN_LLM_MODEL` overrides `llm.model` (tests set it to `none`). |
| `app/db.py` | `connect() -> sqlite3.Connection` (row_factory=Row, `check_same_thread=False`), `init_db(reset: bool=False)` executes `app/schema.sql`; creates `data/` dir. |
| `app/main.py` | FastAPI `app`; `GET /health` → `{"ok": true, "llm": "unknown"}`; mount `web/officer` at `/officer` and `web/victim` at `/victim` with `StaticFiles(html=True)`; on startup call `init_db()`; leave a clearly marked block where routers from `app/routes/*` get included (core-engine fills it). |
| `app/brain/__init__.py`, `app/brain/api.py` | **Stub** class `Brain` implementing every method of `BrainAPI` with one-line English templates (no LLM), `last_used_fallback = True`; module-level `brain = Brain()`. Brain agent will replace internals, keeping names. |
| `mocks/partners.py` | **Stub** class `MockPartners` implementing every `PartnerGateway` method: insert a row in `partner_calls`, return a fake id where needed. Module-level `partners = MockPartners()`. |
| `mocks/seed.py` | **Stub** CLI: `python -m mocks.seed --reset` → `init_db(reset=True)` + insert one user `usr_ravi` with one device. Mockworld replaces it. |
| `mocks/scenarios.py` | **Stub** `inject(conn, name: str) -> dict` raising `NotImplementedError`. |
| `web/officer/index.html`, `web/victim/index.html` | Placeholder pages with the text "PROTOTYPE — SIMULATED DATA". |
| `tests/conftest.py` | Fixture `client`: sets `GUARDIAN_DB` to a tmp file and `GUARDIAN_LLM_MODEL=none`, runs `mocks.seed` reset, yields `fastapi.testclient.TestClient(app)`. |
| `tests/test_smoke.py` | `/health` returns ok; `ACTION_TIERS` covers all actions; every Tier-3 action is in the forbidden set. |
| `scripts/demo.sh` | Placeholder `echo "demo-director fills this"`. |

## Done when
`make install && make check && make test-fast` all pass, and `make run` serves `/health`,
`/officer`, `/victim`. Show the command output. Commit `phase 0: scaffold`.
