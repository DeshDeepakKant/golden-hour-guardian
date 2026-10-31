# officer-console — SPEC (Phase 2, Sonnet)

## Goal
The fraud officer's screen and the judges' main view on the projector: live cases with
golden-hour clocks, what the AI did by itself, what needs a human, and the metrics.

## Owns
`web/officer/**` (`index.html`, `app.js`, `style.css`). Read only: `API_NOTES.md`, `app/contracts.py`, SPEC §4, §7, §10, §12.

## Hard constraints
- Plain HTML/CSS/vanilla JS, **no CDN, no npm** (venue Wi-Fi is unreliable). Everything served by FastAPI.
- Projector-friendly: base font ≥16 px, high contrast, works at 1280×720; light and dark via `prefers-color-scheme`.
- Neutral "Guardian" branding. Persistent label "PROTOTYPE — SIMULATED DATA". No Paytm/bank logos.
- Times shown in IST; money shown as `₹24,999` (from paise).

## Layout
1. **Header metrics bar** (from `GET /metrics/summary`, refreshed on `metrics` SSE): median T_protect vs baseline, median T_ready vs baseline, % protected < 10 min, genuine friction, counters "AI did: N (Tier 1) · You decided: N (Tier 2) · Blocked: N (Tier 3)". Baseline values carry a "simulated manual baseline" tooltip. LLM status pill from `/health` (green "SLM up" / amber "templates").
2. **Left: case queue** — state badge, user (masked), risk, live clock `mm:ss` since `t_alert` (green < 10 min, amber after), origin icon (alert/report).
3. **Centre: case detail** — timeline of events (actor chip: system / agent:<role> / human / victim; tier chip: T1 green "auto", T2 amber "needs you", T3 red "blocked"); risk explanation; evidence pack (masked) with txn table and NCRP field map; money trail (table first; simple inline SVG user → payees with amounts if time allows).
4. **Right: decisions** — pending Tier-2 decisions with rationale, Approve / Reject + note → `POST /decisions/{id}`; resolved decisions below with who/when. "Verify audit chain" button → `GET /audit/{case_id}/verify` → ✓ length / ✗ broken at.
5. **Scenario launcher** (collapsible footer): buttons for `ato`, `genuine`, `inbound`, `noresponse`, `injection`, an "auto-reply" checkbox, and Reset.

## Behaviour
- One `EventSource('/events')` with auto-reconnect and a "reconnecting…" banner; on reconnect re-fetch `/cases`.
- Selecting a case loads `GET /cases/{id}`; incoming events for it append live (no full reload).
- Partner calls marked `SUPPRESSED` render as "Marketing message held (case open)".
- Never display the words "frozen" or "refund guaranteed" anywhere.

## Done when
With the server running: launching `ato` shows the case within 1 s, the clock ticks, events
stream in, approving the three decisions closes the case, metrics update. Take a screenshot
(headless Chrome if available: `chromium --headless --screenshot=/tmp/officer.png --window-size=1280,720 http://127.0.0.1:8000/officer`) and check it.
