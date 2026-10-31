# victim-app — SPEC (Phase 2, Sonnet)

## Goal
The customer's phone experience, shown live on a real Android phone (mirrored with scrcpy):
a verified security check that speaks in their language, a calm "you're protected" screen, and
step-by-step 1930/NCRP guidance with a copyable summary.

## Owns
`web/victim/**` (`index.html`, `app.js`, `style.css`, `manifest.webmanifest`, `sw.js`), `scripts/android.sh`.
Read only: `API_NOTES.md`, `app/contracts.py`, SPEC §5, §9, §12.

## Hard constraints
- Plain HTML/CSS/vanilla JS, no CDN/npm. Served at `/victim?user=usr_ravi` (user via query param).
- Opened on the phone as `http://localhost:8000/...` through `adb reverse` → it's a secure context, so microphone and service worker work.
- Neutral "Guardian" branding, "PROTOTYPE — SIMULATED DATA" label, and a permanent safety line: "Guardian will never ask for your OTP, PIN or password." (in the selected language).
- Never show "frozen", "refund guaranteed", police branding, or any link except `tel:1930` and `https://cybercrime.gov.in`.

## Screens (driven by `victim_prompt` SSE on `/victim/{user}/events`, with `GET /victim/{user}/pending` on load)
1. **Setup / unlock** — first load shows "Tap to enable security alerts". This tap unlocks audio and vibration (mobile browsers block TTS/vibrate without a prior user gesture): speak a short silent utterance, call `navigator.vibrate(1)`.
2. **Home** — "Your account is monitored", language picker (English / हिन्दी / తెలుగు), last status.
3. **Security check** (`verify`, `retry`) — full screen, vibrate pattern, TTS reads the lines (`speechSynthesis`, voice chosen by `lang`: en-IN / hi-IN / te-IN, fall back to text if no voice), three big buttons: "Yes, I made it" · "No, it wasn't me" · "Not sure", plus a mic button (`webkitSpeechRecognition`, same lang) that posts a transcript. → `POST /victim/respond`.
4. **Protected** (`protected`) — what was done ("outgoing payments paused for now", "suspicious phone signed out") in plain words, no promises.
5. **Report now** (`ncrp_guide`) — numbered steps from the server, summary text box with Copy button, "Call 1930" (`tel:1930`) and "Open cybercrime.gov.in" buttons, field for the acknowledgement number → `POST /victim/ncrp-ack`.
6. **Released** / **Done** — friendly close.

## `scripts/android.sh` (already provided — improve only if needed)
Checks adb + authorised device, `adb reverse tcp:8000 tcp:8000`, keeps screen on while on USB,
opens the app in Chrome, starts `scrcpy` if installed.

## Done when
On the phone: unlock → launch `ato` from the console → within 5 s the phone vibrates and speaks
(at least in English; hi/te if voices are installed) → "No, it wasn't me" → protected → guidance
with copyable summary → entering an ack number shows Done. Verify with
`adb exec-out screencap -p > /tmp/phone_<step>.png` and read the screenshots.
