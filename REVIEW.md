# REVIEW: independent pre-demo review (Phase 3)

Scope: SPEC §4-6, §8, §11, RESEARCH §3 and §5, policy/tools/fsm, agents, brain guard and api, both web apps, QA.md.
Baseline: `make test` gives **229 passed** (run during this review). The probes cited below ran
`app.brain.rules.classify` and `app.brain.guard.check` directly. The live-LLM path has never run because Ollama is not installed.

Totals: 4 must-fix, 6 should-fix, 6 nice.

## Must-fix (blocks the demo or breaks a safety claim)

**M1. A spoken or typed "okay" releases the hold.** `app/agents/voice.py:122-125,140-149`, `app/brain/rules.py:58-59`
Problem: probe results: `"okay, which payment?"`, `"I did get an SMS"`, `"yes please stop it"`, `"ha"` and `"theek hai batao"` all return YES_MINE at 0.9. That is above MIN_CONF 0.7, so the hold is released and the case is marked genuine. The LLM path also allows YES_MINE up to 0.85, so model output can cause a release (check 2, LLM authority).
Fix: in `handle_response`, `if via == "transcript" and intent == ReplyIntent.YES_MINE: intent = ReplyIntent.UNSURE`. The retry message already says "please tap Yes or No". Also remove the bare `ok|okay|ha|haan|theek hai|sahi hai|సరే` entries from YES_MINE.

**M2. The client declares its own trusted channel.** `app/agents/voice.py:142`, `web/victim/app.js:347`, `app/routes/victim.py:16-28`
Problem: `resp.channel` comes from the request body, and the app hard-codes `APP_TRUSTED_DEVICE`. `/victim/{user_id}/events`, `/pending` and `/respond` accept any user_id or case_id. In a takeover without a SIM swap, the attacker's new device logged into the same account gets the same prompt, taps "Yes", and the hold is released. This breaks the SPEC §5 claim.
Fix: the server decides the channel. The app sends an `X-Guardian-Device` header, set from a `?device=` parameter in `scripts/android.sh`. `handle_response` treats the reply as APP_TRUSTED_DEVICE only if that header equals `profile.trusted_device`. Otherwise it treats it as VOICE_REGISTERED_NO, which goes to Tier 2. No contract change is needed.

**M3. A confirmed-fraud hold never ends, even after the officer says no.** `app/agents/shield.py:49-50`, `app/agents/desk.py:65-71`
Problem: `_hold_expiry` returns as soon as fraud is confirmed. Rejecting EXTEND_HOLD does nothing, so the case closes with `hold_active=True` indefinitely. That breaks two claims: "Tier-1 hold auto-expires" and "holds longer than 120 min need EXTEND_HOLD approval". It also makes the officer's "Reject" button meaningless.
Fix: for fraud cases, sleep until `hold.max_without_officer_minutes`, then call `tools.expire_hold` unless an APPROVED EXTEND_HOLD exists. In `desk.apply`, a rejected EXTEND_HOLD calls `tools.expire_hold(case, actor)`. After an approved extension, re-spawn the expiry task.

**M4. The live-LLM path has never run, and the risk explanation can delay the victim's alert.** `app/orchestrator.py:101-102`, `app/brain_call.py:14,19`
Problem: `_explain` is spawned before `start_verification`, and every brain call goes through one global lock. With an 8 s timeout per call, the phone can ring about 16 s late, or later with two cases at once. SPEC §12 step 2 requires 5 s. RESEARCH §7 lists "Local SLM wording + classification" as *real*, but that is still unverified.
Fix: `await voice.start_verification(case_id)` first, then spawn `_explain`. Warm the model at startup with one tiny chat and `keep_alive`, then run `make bench` on the demo laptop. If p95 is over 3 s, demo with `llm.model: none` and say so.

## Should-fix

**S1. The output guard misses refund promises and spaced-out phone numbers.** `app/brain/guard.py:19-38`
Problem: probes that passed the guard: `"आपका पैसा वापस आ जाएगा।"`, `"Your money will come back soon."`, `"We have recovered your money."`, `"Call our desk on 98 76 54 32 10 now."`. They only come from model hallucination, because victim text never reaches the generation prompts. Even so, SPEC §11 says "guard blocks risky phrases".
Fix: add `वापस (आ|कर) (जा|दे)`, `money (will|would) come back`, `(have|has) (been )?(recovered|returned|refunded)` and `account (is|has been) (blocked|frozen)`. Reject when there are 5 or more digits in any 20-character window (`(?:\d\D{0,3}){5,}`).

**S2. OTPs or mobile numbers the victim speaks are stored forever.** `app/agents/voice.py:129-131`, `app/orchestrator.py:58-60`
Problem: a panicking victim may read out an OTP, PIN or phone number. The transcript and report text go into the append-only hash-chained audit log and are broadcast to the officer console over SSE. That conflicts with the DPDP minimisation claim.
Fix: before writing to the audit log, apply `re.sub(r"\d(?:[\s-]?\d){3,}", "[digits removed]", text)` to `transcript` and `report.text`.

**S3. The "You are protected" headline is shown after the money has already left.** `web/victim/app.js:26,52,78`
Problem: a victim can read it as "my money is safe", which is an implied outcome promise (check 5).
Fix: use "Your account is now secured" / "आपका खाता अब सुरक्षित किया गया" / "మీ ఖాతా ఇప్పుడు భద్రపరచబడింది". The list beneath it already says what was done.

**S4. The "we will call you" message opens a door for impersonators.** `app/texts.py:47-51`
Problem: a promised callback is exactly the opening a scammer uses. The close screen does not tell the victim how to recognise the genuine caller.
Fix: append to each language: "Our caller will never ask for OTP, PIN, to install an app, or to move money. If unsure, hang up and call 1930."

**S5. The officer console rewrites what it displays.** `web/officer/app.js:21-26`
Problem: `clean()` turns "frozen" into "held" in every string, including victim transcripts and audit payloads. The officer then sees something different from what the log holds, and a guard miss is hidden instead of surfaced.
Fix: delete the replacements. If needed, show a red "guard miss" badge when banned words appear.

**S6. The evidence narrative can name the wrong city.** `app/brain/facts.py:105-108`, `app/brain/templates.py:89-90`
Problem: `{city}` comes from the last row of an unordered `SELECT` and may be the victim's home device. "At {time}, {count} payment(s)" also squeezes a spread of payment times into one moment. The victim pastes this summary into a police portal.
Fix: take the city from the first non-trusted device in `device_timeline`, and say "Between {first} and {time}, …", which matches `scribe.build_pack`'s description.

## Nice

**N1.** `app/tools.py:158-160`: `request_decision` accepts any action, including Tier 1 and Tier 3, so a Tier-3 decision could appear in the queue. Approving it then fails with a 500.
Fix: `if ACTION_TIERS[action] != Tier.T2_HUMAN: policy.require(action, case, actor)`, or raise.

**N2.** `app/agents/voice.py:143-144`: an untrusted "Yes" on a medium-risk case with no hold asks the officer to "Release hold" for a hold that does not exist.
Fix: when `not case.hold_active`, escalate with OFFICER_CALLBACK instead.

**N3.** `app/brain/rules.py:50`: bare `fraud`/`scam` patterns mean "is this a fraud call?" is read as NOT_ME. That fails safe, but it signs out devices and triggers the full fraud pipeline.
Fix: require first-person context, e.g. `(this|it) (is|was) (a )?(fraud|scam)`, and let questions ending in `?` go to UNSURE.

**N4.** `app/agents/scribe.py:38-40`: the NCRP "Short description" always says "Reported by the customer via the bank app", even for alert-origin cases and even though Guardian is not a bank app.
Fix: use "Flagged by the payment provider's fraud monitoring and confirmed as unauthorised by the customer" when `case.origin == "alert"`.

**N5.** `Makefile:16`: `make run` uses `--reload`. Any file save during the demo restarts the server and kills the in-memory verify and hold timers.
Fix: add a `make demo-run` target without `--reload` and use it on stage.

**N6.** `web/victim/index.html:103`: the "Open cybercrime.gov.in" link needs internet, but the phone runs over USB with `adb reverse`.
Fix: don't tap it live unless the venue Wi-Fi has been checked; keep a screenshot of the portal ready.

## Judge Q&A

1. **"Who stops anyone from approving a Tier-2 decision?"**
   In the prototype, nothing beyond binding to 127.0.0.1: the officer name is sent by the browser (`officer/app.js:543`). Policy still refuses any Tier-2 side effect unless a persisted APPROVED decision exists for the same case and action. In production that approval would sit behind the partner's SSO with maker-checker.

2. **"Isn't freezing a customer's payments before they confirm risky for you?"**
   We never freeze. At a score of 0.85 or more we place a temporary hold on the customer's own outgoing payments only. It is configurable, and RESEARCH §5.5 lists it as a policy choice the partner must approve. Beyond the limit, extending the hold needs an officer (once M3 is fixed).

3. **"What if the scammer has the victim's phone number or the new device?"**
   After a SIM change within 72 h, a "yes" is never trusted: it becomes a Tier-2 decision, and Guardian never asks for OTP or PIN. Today the trusted device is asserted by the client (M2). A real deployment must bind verification to the PSP's device-bound session.

4. **"Can prompt injection make the AI release money or promise a refund?"**
   Victim text only reaches `classify_reply`, whose output is an enum. Instruction-like text maps to OTHER or ASKS_REFUND, which goes to an officer callback. Generation prompts never see victim text, and every text output passes the guard. The guard is regex-based and misses paraphrases (S1), which is why all victim-facing fallbacks are fixed templates.

5. **"Where do your speed-up numbers against the baseline come from?"**
   Our times are server timestamps on synthetic scenarios where a presenter taps within seconds, so they show the orchestration overhead, not field performance. The baseline is a sum of assumptions in `config/baseline.yaml`, labelled "simulated" in the UI. A real comparison needs a partner's numbers.

6. **"Paytm already has fraud ops. What's new?"**
   We don't claim a better fraud model (RESEARCH §5.1). The edge is response speed: the victim's own account is protected, a correct 1930/NCRP report is ready in their language, and every officer decision comes with a prepared evidence pack and an audit trail.

7. **"Your hash chain is in the same SQLite file. Can an insider rewrite it?"**
   Yes. A full rewrite with recomputed hashes would pass, so today it only detects partial or accidental tampering. In production, chain heads would be anchored periodically to WORM storage or the bank's SIEM.

8. **"Does this really work in Hindi and Telugu?"**
   Templates and reply rules exist for en, hi and te, and the fallback path works without the model. Native-speaker review is still a TODO (`app/texts.py:2`), and the 4B model's Telugu quality has not been measured because it has never run live.

## Fix status (main session, 2026-10-31, H4 decision: all must + should + N5)

| Item | Status | Where |
|---|---|---|
| M1 | FIXED — typed/spoken YES_MINE → UNSURE; bare ok/ha/theek hai no longer YES_MINE | app/agents/voice.py, app/brain/rules.py |
| M2 | FIXED — trust decided server-side from `X-Guardian-Device` == non-revoked trusted_device; body channel ignored | app/agents/voice.py, app/routes/victim.py, app/routes/sim.py, web/victim/app.js, scripts/android.sh |
| M3 | FIXED — fraud hold expires at max_without_officer unless EXTEND_HOLD approved; rejection releases at once (verified live: CLOSED, hold_active=False) | app/agents/shield.py, desk.py, app/tools.py |
| M4 | FIXED in code — victim prompt sent before explain; officer-facing LLM calls on their own lane; startup warm-up. **Still open: `make bench` on the demo laptop once Ollama is installed.** | app/orchestrator.py, app/brain_call.py, app/brain/llm.py, api.py, app/main.py |
| S1 | FIXED — 4 patterns + spaced-digit check | app/brain/guard.py |
| S2 | FIXED — victim transcript/report digits redacted before audit/SSE | app/audit.py, app/orchestrator.py |
| S3 | FIXED — "Your account is now secured" (en/hi/te) | web/victim/* |
| S4 | FIXED — caller-check line on callback/done (en/hi/te) | app/texts.py |
| S5 | FIXED — no rewriting; red "guard miss" badge | web/officer/app.js |
| S6 | FIXED — city from earliest non-trusted device; "Between {first} and {time}" (single-time variant) | app/brain/facts.py, templates.py, api.py |
| N5 | FIXED — `make demo-run` (no --reload) | Makefile |
| N1–N4, N6 | Deferred (not selected) | — |
