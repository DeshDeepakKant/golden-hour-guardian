# officer-console — HANDOFF

**Receives from:** core-engine — running API + `API_NOTES.md` (SSE kinds and example payloads).

**Delivers to:**
- `demo-director`: element IDs for the scenario buttons and decision buttons (list them in your report) so DEMO.md can say exactly what to click.
- `qa`: nothing to test automatically beyond "page loads, no console errors".

**Must not:** call mock partners directly, compute metrics in JS (display server values), or edit any file outside `web/officer/`.

**Exit report (≤120 words):** files, screenshot path checked, element IDs for demo, any API gap (as "API GAP: …" for core-engine/main to fix).

**Pitfalls:**
- `EventSource` + reload loops: debounce re-fetches.
- Long timelines: virtualise or cap at last 200 events.
- Clock drift: compute from server `t_alert`, not page load time.
