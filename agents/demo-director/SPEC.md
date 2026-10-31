# demo-director — SPEC (Phase 3, Haiku)

## Goal
Make the demo repeatable and the pitch tight: a one-command demo run, a 3-minute stage script,
and slide content that only uses verified numbers.

## Owns
`scripts/demo.sh`, `DEMO.md`, `PITCH.md`. Read: SPEC §9, §10, §12, `RESEARCH.md`, `REVIEW.md` (Judge Q&A),
exit notes from officer-console and victim-app (element IDs, phone steps), `scripts/bench_llm.py` output if available.

## Write
1. **`scripts/demo.sh`** — checks server `/health`; `POST /sim/reset`; runs `ato`, `genuine`, `injection` with `?auto_reply=true`; approves pending decisions for `ato` via API; prints a table: scenario · final state · T_protect · T_ready · fallback used?; then prints `/metrics/summary` vs baseline. Exit non-zero on any unexpected state.
2. **`DEMO.md`** — 3-minute script with timestamps: who speaks, what to click (element IDs), what judges see on the projector and on the phone (scrcpy). Include: **Plan B** (Ollama down → templates; phone disconnect → `auto_reply`; total failure → backup video `demo.mp4`), pre-show checklist (charger, `adb devices`, `make seed`, TTS voice, brightness, Do Not Disturb), and reset steps between judge groups.
3. **`PITCH.md`** — content for 5 slides: (1) problem with numbers from RESEARCH.md §1 (cite source on slide), (2) what the teammate does (alert → protected → evidence → human decides), (3) live demo, (4) safety tiers + compliance mapping (SPEC §11) and "what we don't do", (5) measured results vs simulated baseline + fit with Paytm Pi (fraud-ops module for banks/PAs) + honest limits. Then the Judge Q&A from REVIEW.md.

## Rules
Use only numbers from RESEARCH.md (with source) or measured by `demo.sh`/bench. Always call the
baseline "simulated manual baseline (assumptions)". Never say "freezes money".

## Done when
`bash scripts/demo.sh` passes end-to-end and prints the table; DEMO.md fits 3 minutes read aloud.
