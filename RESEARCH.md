# RESEARCH — is Golden Hour Guardian real and practical?

Researched 31 Oct 2026. Figures are from the sources linked at the bottom; check them again
before putting a number on a slide. Where sources disagree, both are noted.

## 1. Is the problem real? Yes — and big.

**UPI fraud volume (Finance Ministry answer in Lok Sabha, Dec 2025):**

| Financial year | UPI fraud incidents | Amount involved |
|---|---|---|
| 2021-22 | 4.07 lakh | ₹242 cr |
| 2022-23 | 7.25 lakh | ₹573 cr |
| 2023-24 | 13.42 lakh | ₹1,087 cr |
| 2024-25 | 12.64 lakh | ₹981 cr |
| 2025-26 (till Nov) | 10.64 lakh | ₹805 cr |

**Caution on other numbers:** the RBI annual report shows card/internet/digital-payment fraud
cases collapsing in 2025-26 (to a few hundred cases). That reflects how banks classify and report
fraud after RBI's revised fraud-risk master directions of July 2024, not that fraud vanished.
Don't mix the two series on one slide.

**Under-reporting:** a LocalCircles survey (reported by Business Standard, mid-2025) found about
1 in 5 UPI users had faced fraud and roughly half of victims never reported it. Reporting friction
is exactly what this product attacks.

**Account takeover is the dominant pattern:** BioCatch's India data (2024, vendor report — treat as
indicative) put third-party account takeover at about 55% of fraud cases, with heavy mule-account use.

## 2. Does the "golden hour" mechanism exist? Yes — but it's police-led.

- **CFCFRMS** (Citizen Financial Cyber Fraud Reporting and Management System) under I4C, Ministry
  of Home Affairs, was launched in 2021. Victims report on **1930** or **cybercrime.gov.in**; a police
  operator raises a ticket; banks, payment aggregators and wallets act on it to hold funds still in
  the system.
- A July 2026 government update (via secondary coverage) credited CFCFRMS 2.0 with saving over
  ₹11,158 crore across about 32.8 lakh complaints. A **Money Restoration Module** now helps victims
  claim back frozen or recovered funds.
- Speed matters because mule chains move money across accounts within minutes.

**Design consequence:** our agent does not freeze anything. It shortens the gap between alert and
a complete, correct victim report — and protects the victim's own account meanwhile.

## 3. Rules the design follows

| Rule | What it means for us |
|---|---|
| RBI customer-protection (limited liability) circular, 2017 | Customer has zero liability for third-party fraud if reported within 3 working days; bank shadow-credits within 10 working days. → Fast reporting helps the customer; refund/liability decisions stay with humans (Tier 2). |
| CFCFRMS / NCRP process | Freezes come through the police-led system. → We guide the victim; we never file or freeze. |
| RBI FREE-AI framework (Aug 2025) | Human oversight for autonomous/high-risk AI, auditability, AI incident reporting. → Tier table in code, officer approvals, hash-chained audit, logged fallbacks. |
| RBI authentication directions (in force 1 Apr 2026) | Stronger per-transaction authentication. → Never ask for or handle OTP/PIN. |
| DPDP Act 2023 | Purpose limitation, data minimisation, consent. → Only a masked fact sheet and digit-redacted replies go to the Claude API (no raw names, numbers, VPAs, amounts or IDs); production needs a DPA / data-residency review; synthetic data in the demo. |

## 4. Who would actually use it?

- **Buyer:** banks, payment aggregators and wallets — exactly the institutions Paytm's Pi is sold to.
  It's a natural "fraud-ops teammate" module on top of Pi's fraud detection.
- **Users:** fraud-ops officers (approve decisions faster with a ready evidence pack) and victims
  (clear steps, in their language, while panicking).
- **Ecosystem fit:** RBI Innovation Hub's MuleHunter.AI flags around 20,000 mule accounts a month
  across 20+ banks, and I4C and RBIH signed an MoU in May 2026 to share suspect-registry
  intelligence. Detection is improving; **the response workflow** is the gap we fill.

## 5. Honest limits (say these before the judges do)

1. Paytm and banks already run fraud ops. Our edge is orchestration speed, victim-side guidance
   and auditability — not a better fraud model.
2. False positives inconvenience genuine users → we measure friction and auto-release on a trusted
   channel.
3. Voice calls can be spoofed by scammers → we prefer in-app verification on the trusted device and
   never ask for secrets.
4. Real integration needs partner bank channels, the PA's own dispute systems and policy sign-off.
   The hackathon build mocks all of these.
5. The auto-hold before confirmation is a policy choice a real partner must approve.
6. The manual baseline in the demo is a **simulated assumption**; ask a mentor for real numbers.

## 6. Questions to ask Paytm mentors at the venue

1. Today, how long from a fraud-model alert to the customer being contacted? Who does it?
2. Can a temporary hold be placed on a customer's own outgoing UPI without their confirmation?
3. Which channel do you trust for verification after a SIM change?
4. Do you help customers file on 1930/NCRP today, or just tell them to?
5. Which fraud-ops step would you most like an agent to take off your team?

## 7. What's real vs mocked in our build

| Real | Mocked |
|---|---|
| State machine, policy tiers, audit chain, metrics | Bank/PSP hold, session revoke, dispute APIs |
| Claude API wording + classification (masked facts), template fallbacks | Fraud model (alerts come from the scenario injector) |
| Android phone UI, TTS/STT, adb | Calls/SMS (in-app prompt instead) |
| Evidence pack + NCRP field mapping | Filing on NCRP (victim does it; we record the ack number) |

## Sources
- [Lok Sabha answer: UPI fraud by year (AU2481)](https://eparlib.sansad.in/bitstream/123456789/3018042/1/AU2481_5bIzKk.pdf)
- [IANS: UPI frauds ₹805 cr till Nov FY26](https://ianslive.in/upi-frauds-worth-rs-805-crore-witnessed-this-fiscal-so-far-minister--20251215175703)
- [Outlook Business: RBI annual report FY26 fraud data](https://www.outlookbusiness.com/news/financial-institutions-report-over-10000-cases-of-fraud-involving-48000-cr-in-fy26-rbi-data)
- [ThePrint: digital payment fraud series and July 2024 directions](https://theprint.in/india/banks-reported-rs-4457-cr-worth-of-digital-payment-fraud-over-11-yrs-close-to-half-of-it-was-in-2023-24/3004402/)
- [Business Standard: 1 in 5 UPI users faced fraud](https://www.business-standard.com/finance/news/upi-transaction-fraud-india-survey-one-in-five-users-hit-localcircles-125062601141_1.html)
- [The Statesman: BioCatch — ATO ~55% of fraud in India](https://www.thestatesman.com/business/third-party-account-takeover-results-in-nearly-55-of-all-fraud-in-india-report-1503272751.html)
- [Vikaspedia: CFCFRMS and 1930](https://en.vikaspedia.in/e-governance/citizen-services/citizen-financial-cyber-fraud-reporting-and-management-system)
- [IMPRI: how CFCFRMS works](https://www.impriindia.com/?p=74595)
- [SuperKalam (PIB summary): CFCFRMS 2.0 savings](https://superkalam.com/current-affairs/29-07-2026/cfcfrms-2-0-platform-27181ced-b1eb-4f42-acee-14b9c920682f)
- [Moneylife: Money Restoration Module](https://www.moneylife.in/article/1-lakh-citizens-benefit-from-cyber-fraud-refund-system-as-mha-moves-to-speed-up-restoration-of-lost-money/80811.html)
- [Millennium Post: RBI limited-liability rules](https://www.millenniumpost.in/business/business-251065)
- [Drishti IAS: RBI FREE-AI report](https://www.drishtiias.com/daily-updates/daily-news-analysis/rbi-s-free-ai-committee-report/print_manually)
- [Business Standard: MuleHunter.AI ~20,000 mule accounts/month](https://www.business-standard.com/amp/opinion/columns/indians-find-shield-against-fraud-second-bank-account-for-daily-use-125120700734_1.html)
- [AMLegals: I4C–RBIH MoU, MuleHunter adoption](https://amlegals.com/?p=59600)
- [Free Press Journal: Paytm Intelligence (Pi)](https://www.freepressjournal.in/focused-view/paytm-intelligence-vijay-shekhar-sharmas-plan-to-turn-payments-scale-into-an-ai-business)
