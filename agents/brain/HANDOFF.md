# brain — HANDOFF

**Receives from:** scaffolder stub `app/brain/api.py` (method names fixed by `BrainAPI`), frozen contracts, configs.

**Delivers to:**
- `core-engine`: `from app.brain.api import brain` — same names as the stub, plus `brain.is_up()` for `/health`. Core logs `LLM_FALLBACK_USED` when `brain.last_used_fallback` is True.
- `demo-director`: bench numbers from `scripts/bench_llm.py` for the pitch.
- Human (H5): the Hindi/Telugu templates need a native-speaker read-through — list the file and line range in your report.

**Must not:** import from `app/` except `app.contracts` and `app.config`; call tools/partners; store victim text anywhere.

**Exit report (≤120 words):** files, test result, model used, measured Claude API latency if a key was available, template lines that need a native-speaker check.

**Pitfalls:**
- Strip anything outside the JSON object before parsing; treat a refusal, an empty reply or bad JSON as a fallback.
- Structured outputs need closed object schemas (`additionalProperties: false`); keep numeric bounds out of the schema and clamp in code.
- The API needs internet and `ANTHROPIC_API_KEY`; the 8 s budget is per call with no retries, so a slow network means templates, not a stall.
- TTS reads digits oddly in hi/te: code should format amounts as `₹24,999` and the app will speak them; don't spell numbers in words.
