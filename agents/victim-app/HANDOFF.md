# victim-app — HANDOFF

**Receives from:** core-engine — running API + `API_NOTES.md` (`victim_prompt` variants: `verify`, `retry`, `protected`, `ncrp_guide`, `released`, `done`). Human (H3): phone connected, USB debugging authorised.

**Delivers to:**
- `demo-director`: the exact phone steps and which voices were available on the test phone.
- Human: a list of Android settings needed (TTS engine + Hindi/Telugu voice data, Chrome mic permission).

**Must not:** store transcripts in localStorage; call any URL other than this server, `tel:1930` and `https://cybercrime.gov.in`; edit files outside `web/victim/` and `scripts/android.sh`.

**Exit report (≤120 words):** files, which steps verified by screenshot, voices found, any API gap ("API GAP: …").

**Pitfalls:**
- Android Chrome speech recognition needs network (it uses Google's service); if offline, hide the mic and keep buttons.
- `speechSynthesis.getVoices()` is empty until the `voiceschanged` event fires.
- SSE on mobile can drop when the screen locks; on `visibilitychange` re-fetch `/pending`.
- Service worker must not cache API responses — cache only the static shell.
