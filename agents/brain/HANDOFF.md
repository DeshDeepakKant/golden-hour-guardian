# brain — HANDOFF

**Receives from:** scaffolder stub `app/brain/api.py` (method names fixed by `BrainAPI`), frozen contracts, configs.

**Delivers to:**
- `core-engine`: `from app.brain.api import brain` — same names as the stub, plus `brain.is_up()` for `/health`. Core logs `LLM_FALLBACK_USED` when `brain.last_used_fallback` is True.
- `demo-director`: bench numbers from `scripts/bench_llm.py` for the pitch.
- Human (H5): the Hindi/Telugu templates need a native-speaker read-through — list the file and line range in your report.

**Must not:** import from `app/` except `app.contracts` and `app.config`; call tools/partners; store victim text anywhere.

**Exit report (≤120 words):** files, test result, model used, measured latency if Ollama was available, template lines that need a native-speaker check.

**Pitfalls:**
- qwen3 may emit reasoning text if thinking isn't disabled — strip anything outside the JSON object before parsing.
- JSON-schema `format` needs a recent Ollama; fall back to `format: "json"` if rejected.
- TTS reads digits oddly in hi/te: code should format amounts as `₹24,999` and the app will speak them; don't spell numbers in words.
