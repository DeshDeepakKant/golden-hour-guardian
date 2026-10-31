# PITCH — 5 slides

One line: **from fraud alert to victim protected and evidence ready, in minutes, with a human officer making every money decision.**

Rules used for every number here: only figures from RESEARCH.md (with source) or measured by `scripts/demo.sh`. The manual baseline is always called "simulated manual baseline (assumptions)". The product never "freezes money"; it places a temporary hold on the victim's own outgoing payments.

---

## Slide 1 — The problem

**Headline:** Fraud money moves in minutes. The victim's report takes much longer.

- **UPI fraud incidents:** 4.07 lakh (FY22) → 13.42 lakh (FY24) → 12.64 lakh (FY25); 10.64 lakh in FY26 up to November. Amount involved FY24: ₹1,087 cr.
  *Source: Lok Sabha answer AU2481 (Dec 2025); IANS, Dec 2025 (FY26 till Nov).*
- **About 1 in 5 UPI users** had faced fraud, and **roughly half of victims never reported it.**
  *Source: LocalCircles survey, reported by Business Standard (mid-2025).*
- **Account takeover is the dominant pattern:** about 55% of fraud cases in India (vendor estimate, indicative).
  *Source: BioCatch India report (2024), via The Statesman.*
- **The golden hour is police-led:** victims report on 1930 or cybercrime.gov.in and a police operator acts on the ticket. Speed matters because mule chains move money within minutes.
  *Source: CFCFRMS / I4C, Vikaspedia and IMPRI.*

**Speaker note:** do not put the RBI annual-report fraud count on the same slide as the UPI series (different definitions since the July 2024 directions).

---

## Slide 2 — What the teammate does

**Headline:** Alert → protected → evidence → human decides.

1. **Alert:** a fraud model flags a payment. Guardian scores it and picks a path (dismiss, verify, or hold and verify).
2. **Protected:** a temporary hold on the victim's **own** outgoing payments (auto-expires), the suspicious device signed out, marketing paused. The victim is asked "Did you make this payment?" on the **trusted device**.
3. **Evidence:** an evidence pack (money trail, device timeline, signals) and 1930/NCRP guidance with a summary the victim can paste. **The victim files; we don't.**
4. **Human decides:** every refund, dispute, hold extension, bank share or access restore is a Tier-2 decision that an officer approves or rejects. The audit log is hash-chained.

**Speaker note:** we don't freeze anyone. The agent shortens the gap between alert and a complete, correct victim report.

---

## Slide 3 — Live demo (about 3 minutes)

**Headline:** Three runs on the same screen.

- **Account takeover:** a takeover is flagged; the phone rings; the victim taps "No, it wasn't me"; the case is contained; the evidence pack and 1930 steps appear; the officer approves the dispute.
- **Genuine payment:** the victim taps "Yes, I made it"; the hold is released; the friction is shown.
- **Injection:** the victim's text tries to order a refund; nothing is done automatically; an officer callback appears.

Full timed script with element IDs: `DEMO.md`. Backup: `demo.mp4` and screenshots (not yet recorded).

---

## Slide 4 — Safety tiers, compliance mapping, what we don't do

**Headline:** The agent acts alone only where it is reversible and on the victim's own account.

| Tier | Examples | Who |
|---|---|---|
| **Tier 1** | Read ledger, score risk, temporary hold on the victim's own outgoing payments, release on a trusted-device "yes", revoke a suspicious session, build evidence, show 1930 guidance | Agent alone |
| **Tier 2** | Raise dispute, extend hold beyond policy, release hold on an untrusted channel, share evidence with the bank, any refund or credit, restore access, officer callback | Agent prepares, officer approves |
| **Tier 3** | Freeze a beneficiary or third-party account, file a police complaint for the victim, ask for OTP/PIN, promise a refund, contact the payee | **Blocked in code** (`POLICY_BLOCKED` event) |

**Compliance mapping (SPEC §11)**

| Concern | How the design handles it |
|---|---|
| CFCFRMS / 1930 freezes are police-initiated | We never freeze; we guide the victim to 1930/NCRP with a prefilled summary |
| RBI customer liability (report fast) | Fast reporting supported; liability and refund decisions are Tier-2, human only |
| RBI FREE-AI: human oversight, auditability | Tier table in code, officer approvals, hash-chained audit log, logged AI fallbacks |
| DPDP Act: purpose limitation, minimisation | Only a masked fact sheet (and, for reply classification, the victim's reply with digits redacted) goes to the Claude API; no raw names, numbers, VPAs, amounts or IDs; digits redacted before audit; production needs a DPA / data-residency review |
| Impersonation scams | Never asks for OTP or PIN; in-app verified channel; output guard blocks risky phrases |

**What we don't do:** freeze a third-party account; file a complaint for the victim; ask for OTP, PIN or password; promise a refund or a timeline; contact the payee; decide liability.

---

## Slide 5 — Results, fit, and honest limits

**Headline:** Measured on synthetic runs against a simulated manual baseline.

**Measured (two rehearsal runs of `scripts/demo.sh`, 31 Oct 2026, template wording, scripted replies):**

| Metric | Ours (measured, run 1 / run 2) | Simulated manual baseline (assumptions) |
|---|---|---|
| Median T_protect (alert → contained) | 5.0 s / 4.5 s | 2,100 s (35 min) |
| Median T_ready (alert → evidence and 1930 guidance) | 5.2 s / 4.7 s | 3,900 s (65 min) |
| Genuine-user friction (alert → released) | 4.9 s / 4.2 s | not modelled |

The baseline is a sum of assumed steps in `config/baseline.yaml` (queue wait 900 s, analyst review 420 s, outbound calls 600 s, manual hold 180 s, evidence compilation 1,500 s, customer told about 1930 300 s). It is not measured data. Rerun `bash scripts/demo.sh` before the talk and use its numbers.

**Speaker note:** our times are server timestamps where the victim's reply is scripted to arrive 4 s after launch. They show the orchestration overhead, not field performance.

**Fit with Paytm Pi:** banks, payment aggregators and wallets are the buyers (RESEARCH §4). Guardian could sit as a fraud-ops module next to Pi's fraud detection: Pi finds the mule, Guardian handles the response. **No integration exists today.** The build mocks the bank hold, session revoke and dispute channels.

**Honest limits (say these first):**
- Paytm and banks already run fraud ops. Our edge is response speed, victim-side guidance and auditability, not a better fraud model.
- False positives hit genuine users. We measure friction and release on a trusted-device "yes".
- Voice calls can be spoofed, so verification is in-app on the trusted device; we never ask for secrets.
- The automatic hold before confirmation is a policy a real partner must approve.
- Claude API latency is **not measured** yet: run `make bench` (`scripts/bench_llm.py`) with `ANTHROPIC_API_KEY` set before quoting it. The numbers above are template wording. Wording needs internet; without it the demo runs on templates.
- Masked facts and redacted replies leave the machine to Anthropic's API. A real deployment needs a DPA / data-residency review with the partner.
- Telugu and Hindi wording still needs native-speaker review.

---

## Judge Q&A

Source: REVIEW.md (Judge Q&A). Answers 2 and 3 are updated to the fix status (M2 and M3 fixed).

1. **"Who stops anyone from approving a Tier-2 decision?"**
   In the prototype, nothing beyond binding to 127.0.0.1: the officer name is sent by the browser. Policy still refuses any Tier-2 side effect unless a persisted APPROVED decision exists for the same case and action. In production that approval would sit behind the partner's SSO with maker-checker.

2. **"Isn't holding a customer's payments before they confirm risky for you?"**
   We never freeze anyone else's money. At a score of 0.85 or more we place a temporary hold on the customer's own outgoing payments only. It is configurable, and RESEARCH §5.5 lists it as a policy choice the partner must approve. The hold expires on its own; holding beyond the policy limit needs an officer's approval, and a rejected extension releases the hold at once.

3. **"What if the scammer has the victim's phone number or the new device?"**
   After a SIM change within 72 h, a "yes" is never trusted: it becomes a Tier-2 decision, and Guardian never asks for OTP or PIN. The server decides the trusted device by checking the device header against the customer's registered trusted device. The prototype's device ID is a demo value. A real deployment must bind verification to the payment provider's device-bound session.

4. **"Can prompt injection make the AI release money or promise a refund?"**
   Victim text only reaches `classify_reply`, whose output is an enum. Instruction-like text maps to OTHER or ASKS_REFUND, which goes to an officer callback. Generation prompts never see victim text, and every text output passes the guard. The guard is regex-based and misses paraphrases, which is why all victim-facing fallbacks are fixed templates.

5. **"Where do your speed-up numbers against the baseline come from?"**
   Our times are server timestamps on synthetic scenarios where a presenter taps within seconds, so they show the orchestration overhead, not field performance. The baseline is a sum of assumptions in `config/baseline.yaml`, labelled "simulated" in the UI. A real comparison needs a partner's numbers.

6. **"Paytm already has fraud ops. What's new?"**
   We don't claim a better fraud model (RESEARCH §5.1). The edge is response speed: the victim's own account is protected, a correct 1930/NCRP report is ready in their language, and every officer decision comes with a prepared evidence pack and an audit trail.

7. **"Your hash chain is in the same SQLite file. Can an insider rewrite it?"**
   Yes. A full rewrite with recomputed hashes would pass, so today it only detects partial or accidental tampering. In production, chain heads would be anchored periodically to WORM storage or the bank's SIEM.

8. **"Does this really work in Hindi and Telugu?"**
   Templates and reply rules exist for en, hi and te, and the fallback path works without the model. Native-speaker review is still a TODO (`app/texts.py:2`), and Claude's Hindi/Telugu wording has not been reviewed by a native speaker either.

9. **"Does customer data go to an external AI?"**
   Yes, a minimised slice. Wording and reply classification call the Claude API. It gets a masked fact sheet (signal codes, a masked name like "R*** K***") and, for classification, the victim's reply with digit runs redacted. Names, mobile numbers, VPAs, amounts and IDs never go in; code fills them into placeholders. With no key or no network, everything runs on templates. Production would need a DPA and data-residency review with the partner.
