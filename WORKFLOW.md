# Golden Hour Guardian — Application Workflow

This document details the complete end-to-end execution workflow of **Golden Hour Guardian**, traced directly from the codebase.

---

## Workflow Diagram

```mermaid
flowchart TD
    subgraph S0["0. System Boot & Lifespan"]
        A0["app/main.py: lifespan()"] --> A1["init_db() & bus.reset()"]
        A1 --> A2["Thread: brain.warm() (Ollama SLM)"]
    end

    subgraph S1["1. Alert Ingestion & Case Creation"]
        B1["POST /webhooks/fraud-alert<br/>(From Paytm Pi Engine)"] --> B2["orchestrator.create_from_alert()"]
        B3["POST /webhooks/victim-report<br/>(Inbound 'Money Deducted')"] --> B4["orchestrator.create_from_report()"]
        B2 -->|"Idempotent on alert_id"| B5["Case State: NEW<br/>audit.append(ALERT_RECEIVED)"]
        B4 -->|"Floors score >= 0.85"| B6["Case State: CONFIRMED_FRAUD<br/>audit.append(VICTIM_REPORT_RECEIVED)"]
    end

    subgraph S2["2. Sentinel Triage & Channel Selection"]
        B5 --> C1["sentinel.triage()"]
        C1 --> C2["Recompute 8 signals from ledger<br/>combine weights into risk_score"]
        C2 -->|"score < 0.40"| C3["State: TRIAGED ➔ DISMISSED ➔ CLOSED"]
        C2 -->|"0.40 <= score < 0.85"| C4["State: TRIAGED ➔ VERIFYING"]
        C2 -->|"score >= 0.85"| C5["State: TRIAGED ➔ HELD_PENDING_VERIFY"]
        C1 --> C6["sentinel.pick_channel()<br/>Check SIM_CHANGE_72H"]
    end

    subgraph S3["3. Shield Containment & Conductor-lite"]
        C5 --> D1["shield.place_hold() ➔ tools.place_temp_hold()"]
        D1 --> D2["Reversible hold on victim's OWN outgoing UPI<br/>auto-expires in 60m (hold_expiry task)"]
        C4 --> D3["shield.suppress_marketing() (24h)"]
        C5 --> D3
    end

    subgraph S4["4. Voice Verification Dialogue"]
        D3 --> E1["voice.start_verification()"]
        E1 --> E2["brain_call('verification_messages')<br/>Native En/Hi/Te on trusted app"]
        E1 --> E3["tasks.spawn(verify_timeout, 120s)"]
        E1 --> E4["tasks.spawn(_explain) for Officer Console"]
        E2 --> E5["POST /victim/respond<br/>Header: x-guardian-device"]
        E5 -->|"reply_channel() checks device against profile"| E6["Intent Classification (Button vs Audio)"]
        E6 -->|"YES_MINE on Trusted App"| E7["State: CONFIRMED_GENUINE ➔ RELEASED"]
        E6 -->|"YES_MINE on Swapped SIM"| E8["policy.check() BLOCKS ➔ Escalate to Tier-2"]
        E6 -->|"NOT_ME"| E9["State: CONFIRMED_FRAUD ➔ run_fraud_pipeline()"]
        E6 -->|"UNSURE"| E10["Retry once ➔ Else Escalate"]
        E6 -->|"ASKS_REFUND / DISTRESS"| E11["Escalate Callback Decision to Officer"]
    end

    subgraph S5["5. Scribe Evidence & 1930 Guidance"]
        E9 --> F1["shield.contain()"]
        B6 --> F1
        F1 --> F2["tools.revoke_session() on attacker device<br/>State: CONTAINED"]
        F2 --> F3["scribe.run()"]
        F3 --> F4["scribe.build_pack(): Mask PII, graph txns, pre-fill NCRP form"]
        F4 --> F5["brain_call: evidence_narratives & ncrp_guidance"]
        F5 --> F6["State: EVIDENCE_READY<br/>tools.guide_ncrp() pushes 1930 summary to victim"]
    end

    subgraph S6["6. Desk & Human Officer Approvals"]
        F6 --> G1["desk.open_fraud_decisions()"]
        G1 --> G2["Request Tier-2 Decisions with LLM rationale:<br/>RAISE_DISPUTE, EXTEND_HOLD, SHARE_EVIDENCE"]
        G2 --> G3["State: AWAITING_OFFICER<br/>GET /officer/queue (SLA countdown)"]
        G3 --> G4["POST /decisions/{id} (Officer Decision)"]
        G4 --> G5["policy.require(T2_HUMAN)<br/>tools.T2_TOOLS applies bank API action"]
        G5 --> G6["desk.close_if_done()<br/>All decisions resolved ➔ State: CLOSED"]
    end
```

---

## Available Formats

| Format | Path | Best For |
|---|---|---|
| **Mermaid Source (.mmd)** | [`docs/workflow.mmd`](file:///home/anya/Videos/golden-hour-guardian/docs/workflow.mmd) | Version control, diagrams-as-code, and CLI tools |
| **Vector Graphics (.svg)** | [`docs/workflow.svg`](file:///home/anya/Videos/golden-hour-guardian/docs/workflow.svg) | High-resolution scalable viewing, slide embeds, and print |
| **Raster Image (.png)** | [`docs/workflow.png`](file:///home/anya/Videos/golden-hour-guardian/docs/workflow.png) | Presentations, reports, and quick image previews |
| **Standalone Web (.html)** | [`docs/workflow.html`](file:///home/anya/Videos/golden-hour-guardian/docs/workflow.html) | Interactive browser viewer with zoom & pan |

---

## Codebase Reference Map

1. **Subsystem 0: Lifecycle**
   - Startup: [`app/main.py::lifespan()`](file:///home/anya/Videos/golden-hour-guardian/app/main.py#L21-L31)
   - DB Init: [`app/db.py::init_db()`](file:///home/anya/Videos/golden-hour-guardian/app/db.py#L14)
   - Model Warmup: [`app/brain/api.py::Brain.warm()`](file:///home/anya/Videos/golden-hour-guardian/app/brain/api.py#L55-L60)

2. **Subsystem 1: Ingestion**
   - Alert Webhook: [`app/routes/webhooks.py::fraud_alert()`](file:///home/anya/Videos/golden-hour-guardian/app/routes/webhooks.py#L11-L19)
   - Victim Report: [`app/routes/webhooks.py::victim_report()`](file:///home/anya/Videos/golden-hour-guardian/app/routes/webhooks.py#L22-L29)
   - Case Factory: [`app/orchestrator.py::create_from_alert()`](file:///home/anya/Videos/golden-hour-guardian/app/orchestrator.py#L24-L42) & [`create_from_report()`](file:///home/anya/Videos/golden-hour-guardian/app/orchestrator.py#L44-L68)

3. **Subsystem 2: Triage**
   - Signal Recomputation: [`app/agents/sentinel.py::compute_signals()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/sentinel.py#L44-L108)
   - Path Triage: [`app/agents/sentinel.py::triage()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/sentinel.py#L132-L147)
   - Channel Selection: [`app/agents/sentinel.py::pick_channel()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/sentinel.py#L111-L116)

4. **Subsystem 3: Containment**
   - Outgoing Hold: [`app/agents/shield.py::place_hold()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/shield.py#L20-L24)
   - Auto-Expiry Timer: [`app/agents/shield.py::_hold_expiry()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/shield.py#L72-L97)
   - Marketing Hold: [`app/agents/shield.py::suppress_marketing()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/shield.py#L38-L41)

5. **Subsystem 4: Verification**
   - Outreach: [`app/agents/voice.py::start_verification()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/voice.py#L72-L83)
   - Response Handler: [`app/agents/voice.py::handle_response()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/voice.py#L133-L202)
   - Hardware Authentication: [`app/agents/voice.py::reply_channel()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/voice.py#L121-L131)

6. **Subsystem 5: Evidence & Guidance**
   - Containment & Device Revoke: [`app/agents/shield.py::contain()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/shield.py#L43-L59)
   - Pack Construction: [`app/agents/scribe.py::build_pack()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/scribe.py#L32-L60)
   - 1930 Guidance: [`app/agents/scribe.py::run()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/scribe.py#L62-L85)

7. **Subsystem 6: Officer Approvals & Closure**
   - Pending Decisions: [`app/agents/desk.py::open_fraud_decisions()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/desk.py#L32-L37)
   - Queue: [`app/routes/cases.py::officer_queue()`](file:///home/anya/Videos/golden-hour-guardian/app/routes/cases.py#L37-L55)
   - Decision Execution: [`app/agents/desk.py::apply()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/desk.py#L48-L90)
   - Auto-Closure: [`app/agents/desk.py::close_if_done()`](file:///home/anya/Videos/golden-hour-guardian/app/agents/desk.py#L92-L99)
