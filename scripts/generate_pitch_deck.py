import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="Golden_Hour_Guardian_Pitch_Deck.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    C_DARK_BG = RGBColor(10, 25, 47)        # #0A192F Deep Navy
    C_LIGHT_BG = RGBColor(248, 250, 252)    # #F8FAFC Off-white
    C_WHITE = RGBColor(255, 255, 255)
    C_CARD_BG = RGBColor(255, 255, 255)
    C_CARD_BORDER = RGBColor(226, 232, 240) # #E2E8F0
    C_PAYTM_BLUE = RGBColor(0, 186, 242)    # #00BAF2 Paytm Cyan/Blue
    C_NAVY_HEADING = RGBColor(15, 23, 42)   # #0F172A
    C_TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B
    C_SUCCESS = RGBColor(16, 185, 129)      # #10B981 Emerald
    C_DANGER = RGBColor(239, 68, 68)        # #EF4444 Crimson
    C_WARNING = RGBColor(245, 158, 11)      # #F59E0B Amber
    C_PURPLE = RGBColor(139, 92, 246)       # #8B5CF6

    def set_slide_background(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text, dark=False):
        # Category / Track Pill
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = C_PAYTM_BLUE

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = C_WHITE if dark else C_NAVY_HEADING

    def add_card(slide, left, top, width, height, bg_color=C_CARD_BG, border_color=C_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (Dark)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, C_DARK_BG)

    # Accent decorative bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.2), Inches(0.8), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C_PAYTM_BLUE
    bar.line.fill.background()

    # Track / Event Box
    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(0.5))
    tf_t = t_box.text_frame
    p_t = tf_t.paragraphs[0]
    p_t.text = "PAYTM BUILD FOR INDIA AI HACKATHON  •  TRACK 3: AUTONOMOUS AI TEAMMATES"
    p_t.font.size = Pt(13)
    p_t.font.bold = True
    p_t.font.color.rgb = C_PAYTM_BLUE

    # Main Project Title
    m_box = s1.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(11.7), Inches(1.4))
    tf_m = m_box.text_frame
    tf_m.word_wrap = True
    p_m = tf_m.paragraphs[0]
    p_m.text = "GOLDEN HOUR GUARDIAN"
    p_m.font.size = Pt(44)
    p_m.font.bold = True
    p_m.font.color.rgb = C_WHITE

    # Tagline / Subtitle
    sub_box = s1.shapes.add_textbox(Inches(0.8), Inches(3.5), Inches(11.7), Inches(0.8))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = "The Autonomous AI Teammate for Real-Time UPI Fraud Containment & Victim Protection"
    p_sub.font.size = Pt(20)
    p_sub.font.color.rgb = RGBColor(203, 213, 225)

    # 3 Metric / Feature Highlights at bottom of Title Slide
    h_cards = [
        ("⚡ < 60s Containment", "T_protect: Automatic Tier-1 outgoing hold & session revocation"),
        ("🎙️ Multilingual Voice", "Proactive verification in En/Hi/Te on trusted device without asking OTP/PIN"),
        ("📋 1930 / NCRP Ready", "Pre-fills national cybercrime reporting packet & equips human fraud officers")
    ]
    for idx, (head, desc) in enumerate(h_cards):
        cx = Inches(0.8 + idx * 4.0)
        c = add_card(s1, cx, Inches(4.7), Inches(3.7), Inches(1.5), bg_color=RGBColor(23, 42, 69), border_color=RGBColor(51, 65, 85))
        c_tb = s1.shapes.add_textbox(cx + Inches(0.2), Inches(4.85), Inches(3.3), Inches(1.2))
        c_tf = c_tb.text_frame
        c_tf.word_wrap = True
        p1 = c_tf.paragraphs[0]
        p1.text = head
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = C_PAYTM_BLUE
        p2 = c_tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = RGBColor(148, 163, 184)
        p2.space_before = Pt(6)

    # Footer note
    ft_box = s1.shapes.add_textbox(Inches(0.8), Inches(6.6), Inches(11.7), Inches(0.4))
    ft_tf = ft_box.text_frame
    p_ft = ft_tf.paragraphs[0]
    p_ft.text = "Design Thesis: AI teammates that don't just respond — they get the job done with strict human-in-the-loop governance."
    p_ft.font.size = Pt(11)
    p_ft.font.italic = True
    p_ft.font.color.rgb = RGBColor(100, 116, 139)

    # =========================================================================
    # SLIDE 2: PROBLEM STATEMENT (Light)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, C_LIGHT_BG)
    add_header(s2, "The Critical 60-Minute Crisis in UPI Fraud", "Problem Statement")

    cols_s2 = [
        ("🚨 The Fraud Epidemic in India", C_DANGER, [
            ("₹1,087+ Crore lost in UPI frauds", "Over 13.4 lakh incidents reported in Lok Sabha (FY24-25)."),
            ("55% Account Takeover (ATO)", "BioCatch India data: rapid device takeover & SIM swapping dominate."),
            ("Mule Fan-In Networks", "Stolen funds are moved through multi-layered mule accounts within 5–10 minutes.")
        ]),
        ("⏳ The Broken Manual Response", C_WARNING, [
            ("35+ Min Alert-to-Action Lag", "Alert sits in queue (15m) + analyst triage (7m) + manual call (10m)."),
            ("65+ Min Evidence Compilation", "Analysts manually cross-check transaction ledgers, IPs, and device hashes."),
            ("Missed 'Golden Hour'", "By the time a human officer acts, funds have cleared multiple external banks.")
        ]),
        ("😰 Victim Paralysis & Under-reporting", C_PURPLE, [
            ("50% of Victims Never File", "LocalCircles: Half of victims give up due to panic and complex portals."),
            ("Impersonation Scam Fears", "Victims fear automated calls asking for OTP/PIN, ignoring alerts."),
            ("Genuine User Friction", "Heavy-handed blanket account freezes alienate honest customers.")
        ])
    ]

    for idx, (title, color, items) in enumerate(cols_s2):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s2, cx, Inches(1.8), Inches(3.7), Inches(5.1))
        # Top banner on card
        top_bar = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, Inches(1.8), Inches(3.7), Inches(0.1))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = color
        top_bar.line.fill.background()

        tb = s2.shapes.add_textbox(cx + Inches(0.25), Inches(2.05), Inches(3.2), Inches(4.7))
        tf = tb.text_frame
        tf.word_wrap = True
        p_hd = tf.paragraphs[0]
        p_hd.text = title
        p_hd.font.size = Pt(15)
        p_hd.font.bold = True
        p_hd.font.color.rgb = C_NAVY_HEADING

        for it_title, it_desc in items:
            p_t = tf.add_paragraph()
            p_t.text = "• " + it_title
            p_t.font.size = Pt(12)
            p_t.font.bold = True
            p_t.font.color.rgb = color
            p_t.space_before = Pt(10)

            p_d = tf.add_paragraph()
            p_d.text = it_desc
            p_d.font.size = Pt(11)
            p_d.font.color.rgb = C_NAVY_HEADING
            p_d.space_before = Pt(2)

    # =========================================================================
    # SLIDE 3: PROPOSED SOLUTION (Light)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, C_LIGHT_BG)
    add_header(s3, "Meet Golden Hour Guardian: Autonomous Fraud Teammate", "Proposed Solution")

    # Banner across the top
    sol_bar = add_card(s3, Inches(0.8), Inches(1.7), Inches(11.7), Inches(0.85), bg_color=RGBColor(238, 248, 255), border_color=C_PAYTM_BLUE)
    sb_tb = s3.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(11.3), Inches(0.75))
    sb_tf = sb_tb.text_frame
    sb_tf.word_wrap = True
    p_sb = sb_tf.paragraphs[0]
    p_sb.text = "A purpose-built AI teammate working alongside fraud officers: receives alerts from Paytm Pi, executes instant reversible containment, verifies victims via voice, and compiles 1930/NCRP evidence dossiers."
    p_sb.font.size = Pt(12)
    p_sb.font.color.rgb = C_NAVY_HEADING

    # 4 Modular Teammate Roles
    roles = [
        ("🛡️ SHIELD", "Autonomous Containment", C_PAYTM_BLUE, [
            "Instantly places temporary hold on victim's outgoing UPI (auto-expiring)",
            "Revokes compromised session & rogue device tokens in real-time",
            "Suppresses marketing/cross-sell SMS to prevent victim disorientation"
        ]),
        ("🎙️ VOICE", "Multilingual Victim Dialogue", C_SUCCESS, [
            "Proactive in-app voice/tap outreach in English, Hindi, and Telugu",
            "Zero-Secret Guarantee: Strict guardrails NEVER ask for OTP, PIN, or CVV",
            "Trusted Channel Rule: Validates whether SIM was swapped in last 72 hours"
        ]),
        ("📋 SCRIBE", "Automated Evidence Dossier", C_PURPLE, [
            "Stitches transaction ledger, mule fan-in graphs, and IP/device fingerprints",
            "Pre-fills complete national 1930 / NCRP cybercrime portal complaint",
            "Generates copyable filing packets so panicked victims file in 2 minutes"
        ]),
        ("⚖️ DESK", "Officer Co-Pilot", C_NAVY_HEADING, [
            "Presents pre-computed Tier-2 dispute recommendations with LLM rationale",
            "Tracks Golden-Hour SLA countdown clocks for fraud analyst queue",
            "One-click dispute dispatch to partner banks upon officer approval"
        ])
    ]

    for idx, (role_name, role_sub, col, bullets) in enumerate(roles):
        cx = Inches(0.8 + idx * 3.0)
        add_card(s3, cx, Inches(2.75), Inches(2.8), Inches(4.2))
        
        # Header inside card
        card_hdr = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, Inches(2.75), Inches(2.8), Inches(0.85))
        card_hdr.fill.solid()
        card_hdr.fill.fore_color.rgb = col
        card_hdr.line.fill.background()

        hdr_tb = s3.shapes.add_textbox(cx, Inches(2.8), Inches(2.8), Inches(0.75))
        hdr_tf = hdr_tb.text_frame
        p_rn = hdr_tf.paragraphs[0]
        p_rn.text = role_name
        p_rn.font.size = Pt(14)
        p_rn.font.bold = True
        p_rn.font.color.rgb = C_WHITE
        p_rn.alignment = PP_ALIGN.CENTER
        p_rs = hdr_tf.add_paragraph()
        p_rs.text = role_sub
        p_rs.font.size = Pt(9.5)
        p_rs.font.color.rgb = RGBColor(226, 232, 240)
        p_rs.alignment = PP_ALIGN.CENTER

        b_tb = s3.shapes.add_textbox(cx + Inches(0.15), Inches(3.7), Inches(2.5), Inches(3.1))
        b_tf = b_tb.text_frame
        b_tf.word_wrap = True
        for b_idx, b_text in enumerate(bullets):
            p_b = b_tf.paragraphs[0] if b_idx == 0 else b_tf.add_paragraph()
            p_b.text = "✔ " + b_text
            p_b.font.size = Pt(10.5)
            p_b.font.color.rgb = C_NAVY_HEADING
            p_b.space_before = Pt(8)

    # =========================================================================
    # SLIDE 4: ARCHITECTURE & POLICY TIERS (Light)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, C_LIGHT_BG)
    add_header(s4, "Autonomous Execution with Zero Governance Drift", "System Architecture & Policy Tiers")

    # Left: End-to-End Workflow Pipeline
    add_card(s4, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2))
    w_tb = s4.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(5.2), Inches(4.8))
    w_tf = w_tb.text_frame
    w_tf.word_wrap = True
    p_wh = w_tf.paragraphs[0]
    p_wh.text = "🔄 Autonomous End-to-End Workflow"
    p_wh.font.size = Pt(16)
    p_wh.font.bold = True
    p_wh.font.color.rgb = C_NAVY_HEADING

    steps = [
        ("1. Ingestion (Paytm Pi Alert / User Webhook)", "Receives high-velocity fraud alert (e.g. score >= 0.85, ATO signals)."),
        ("2. Autonomous Tier-1 Containment (0 - 5s)", "Instantly places temporary hold on outgoing funds & revokes rogue session."),
        ("3. Trusted-Channel Verification (5 - 30s)", "Proactive in-app voice prompt on known device. If SIM swap in 72h, voice is untrusted."),
        ("4. Scribe Evidence Assembly (Parallel)", "Synthesizes money trail graph, mule velocity & pre-fills 1930 / NCRP form."),
        ("5. Officer Desk Dispatch & Approval", "Officer reviews dossier with 1-click partner dispute action & audit chain verification.")
    ]
    for s_title, s_desc in steps:
        p_st = w_tf.add_paragraph()
        p_st.text = s_title
        p_st.font.size = Pt(11.5)
        p_st.font.bold = True
        p_st.font.color.rgb = C_PAYTM_BLUE
        p_st.space_before = Pt(8)
        p_sd = w_tf.add_paragraph()
        p_sd.text = s_desc
        p_sd.font.size = Pt(10.5)
        p_sd.font.color.rgb = C_NAVY_HEADING
        p_sd.space_before = Pt(1)

    # Right: Strict 3-Tier Policy Table (Compliance by Design)
    add_card(s4, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2))
    p_tb = s4.shapes.add_textbox(Inches(7.0), Inches(1.9), Inches(5.3), Inches(4.8))
    p_tf = p_tb.text_frame
    p_tf.word_wrap = True
    p_ph = p_tf.paragraphs[0]
    p_ph.text = "🛡️ Hardcoded 3-Tier Action Policy (RBI Aligned)"
    p_ph.font.size = Pt(16)
    p_ph.font.bold = True
    p_ph.font.color.rgb = C_NAVY_HEADING

    tiers = [
        ("TIER 1 — AGENT ACTS ALONE (Reversible & Safe)", C_SUCCESS,
         "• Temporary hold on victim's OWN outgoing UPI (auto-expires in 60m)\n• Revoke suspicious session token\n• Voice/app verification\n• Pre-fill 1930 report & suppress marketing"),
        ("TIER 2 — AGENT PREPARES, HUMAN APPROVES", C_WARNING,
         "• Raise formal dispute via partner bank channel\n• Extend hold beyond 120 mins\n• Release hold after recent SIM swap (untrusted channel)\n• Liability & shadow-credit refund determinations"),
        ("TIER 3 — IMPOSSIBLE IN CODE (Hard Blocked)", C_DANGER,
         "• NEVER freezes 3rd-party/beneficiary accounts (Police only)\n• NEVER files police complaints on victim's behalf\n• NEVER asks for OTP, PIN, password, or CVV\n• NEVER guarantees refunds or promises legal outcomes")
    ]
    for t_name, t_col, t_content in tiers:
        pt_n = p_tf.add_paragraph()
        pt_n.text = t_name
        pt_n.font.size = Pt(11.5)
        pt_n.font.bold = True
        pt_n.font.color.rgb = t_col
        pt_n.space_before = Pt(8)
        pt_c = p_tf.add_paragraph()
        pt_c.text = t_content
        pt_c.font.size = Pt(10)
        pt_c.font.color.rgb = C_NAVY_HEADING
        pt_c.space_before = Pt(1)

    # =========================================================================
    # SLIDE 5: TECHNOLOGY & TECH STACK (Light)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, C_LIGHT_BG)
    add_header(s5, "Robust, Privacy-First Architecture", "Technology & Tech Stack")

    tech_cards = [
        ("🤖 Claude API & Guardrails", C_PAYTM_BLUE, [
            ("Anthropic Claude API (Opus 5.5)", "Claude via the anthropic SDK (effort low) for risk wording & reply classification; 8 s budget per call."),
            ("Masked Facts Only", "Only a masked fact sheet & digit-redacted replies reach the API; no names, numbers, VPAs, amounts or IDs."),
            ("Fail-Safe Regex Guardrails", "Regex scanner intercepts banned tokens (OTP/PIN/fee). Instant fallback to deterministic templates.")
        ]),
        ("⚡ High-Throughput Core Engine", C_NAVY_HEADING, [
            ("Python 3.12 & FastAPI", "Asynchronous, event-driven API engine capable of processing thousands of alerts/sec."),
            ("Deterministic State Machine", "Rigid FSM (NEW -> HELD -> CONTAINED -> EVIDENCE -> CLOSED) prevents invalid states."),
            ("Server-Sent Events (SSE)", "Real-time streaming bus for officer console alerts and mobile victim app updates.")
        ]),
        ("🎙️ Multilingual Voice & Mobile PWA", C_SUCCESS, [
            ("Web Speech STT & TTS", "Interactive speech synthesis & transcription supporting English, Hindi, and Telugu."),
            ("Mobile-First Victim PWA", "Low-bandwidth Progressive Web App running on Android/iOS with push verification."),
            ("Panic-Optimized UX", "Large high-contrast buttons, audio readouts, and 1-tap copyable 1930 summaries.")
        ]),
        ("🔐 Tamper-Evident Auditability", C_PURPLE, [
            ("SHA-256 Hash-Chained Log", "Every state change, tool invocation, and human officer decision is cryptographically linked."),
            ("Instant Verification Tool", "Built-in /audit/verify endpoint detects any historical tampering or retroactive edits."),
            ("RBI FREE-AI Ready", "Comprehensive audit trails adhering to RBI's August 2025 AI governance framework.")
        ])
    ]

    for idx, (t_title, t_col, t_points) in enumerate(tech_cards):
        row = idx // 2
        col = idx % 2
        cx = Inches(0.8 + col * 6.0)
        cy = Inches(1.8 + row * 2.7)

        add_card(s5, cx, cy, Inches(5.7), Inches(2.45))
        # Top color accent
        top_bar = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cy, Inches(5.7), Inches(0.08))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = t_col
        top_bar.line.fill.background()

        tb = s5.shapes.add_textbox(cx + Inches(0.25), cy + Inches(0.15), Inches(5.2), Inches(2.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p_th = tf.paragraphs[0]
        p_th.text = t_title
        p_th.font.size = Pt(14)
        p_th.font.bold = True
        p_th.font.color.rgb = t_col

        for sub, body in t_points:
            p_s = tf.add_paragraph()
            p_s.text = "• " + sub + ": "
            p_s.font.size = Pt(10.5)
            p_s.font.bold = True
            p_s.font.color.rgb = C_NAVY_HEADING
            p_s.space_before = Pt(4)
            p_b = tf.add_paragraph()
            p_b.text = "   " + body
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = C_TEXT_MUTED
            p_b.space_before = Pt(1)

    # =========================================================================
    # SLIDE 6: USP (Light)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, C_LIGHT_BG)
    add_header(s6, "Why Golden Hour Guardian Outperforms", "Unique Selling Proposition (USP)")

    usps = [
        ("⚡", "True Autonomy, Not Just Q&A", "Unlike conventional chatbots that provide static FAQ links while money drains, Guardian executes autonomous Tier-1 containment (session kill, payment hold) in milliseconds."),
        ("🛡️", "SIM-Swap Aware Trust Rail", "Contextual awareness detects if a SIM was changed in the last 72 hours (SIM_CHANGE_72H). If swapped, phone verification is marked untrusted, defeating OTP/call hijacking."),
        ("🔒", "Privacy by Minimisation (DPDP)", "The Claude API sees only a masked fact sheet and digit-redacted replies; raw names, mobile numbers, VPAs, amounts and IDs are filled in by code. Production needs a DPA / data-residency review."),
        ("🤝", "Symbiotic Human-AI Teammate", "Automates 95% of manual evidence gathering and triage, delivering a single-click dispute dossier with SLA countdown timers to human fraud officers."),
        ("📋", "National 1930 / CFCFRMS Bridge", "Transforms panicked victims into effective reporters by auto-generating correctly formatted NCRP complaint fields and acknowledging national complaint numbers.")
    ]

    for idx, (icon, title, desc) in enumerate(usps):
        cy = Inches(1.7 + idx * 1.05)
        add_card(s6, Inches(0.8), cy, Inches(11.7), Inches(0.92))
        
        # Icon badge
        ib = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), cy + Inches(0.12), Inches(0.65), Inches(0.65))
        ib.fill.solid()
        ib.fill.fore_color.rgb = RGBColor(238, 248, 255)
        ib.line.color.rgb = C_PAYTM_BLUE
        ib_tb = s6.shapes.add_textbox(Inches(1.0), cy + Inches(0.12), Inches(0.65), Inches(0.65))
        ib_tf = ib_tb.text_frame
        p_i = ib_tf.paragraphs[0]
        p_i.text = icon
        p_i.font.size = Pt(16)
        p_i.alignment = PP_ALIGN.CENTER

        # Content
        ctb = s6.shapes.add_textbox(Inches(1.85), cy + Inches(0.08), Inches(10.4), Inches(0.75))
        ctf = ctb.text_frame
        ctf.word_wrap = True
        p_ut = ctf.paragraphs[0]
        p_ut.text = title
        p_ut.font.size = Pt(13)
        p_ut.font.bold = True
        p_ut.font.color.rgb = C_NAVY_HEADING

        p_ud = ctf.add_paragraph()
        p_ud.text = desc
        p_ud.font.size = Pt(10.5)
        p_ud.font.color.rgb = C_TEXT_MUTED
        p_ud.space_before = Pt(2)

    # =========================================================================
    # SLIDE 7: IMPACT & BENEFITS (Light)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, C_LIGHT_BG)
    add_header(s7, "Measurable Outcomes for Victims, Officers & Banks", "Impact & Benefits")

    # Big KPI Stat Cards across top
    stats = [
        ("T_protect (Containment)", "35 mins", "< 60 sec", "> 97% Faster", C_SUCCESS),
        ("T_ready (Evidence Dossier)", "65 mins", "< 5 mins", "> 92% Faster", C_PAYTM_BLUE),
        ("Genuine User Friction", "Hours of hold", "< 20 sec", "Instant Release", C_PURPLE),
        ("Officer Case Capacity", "1x Manual", "8x - 10x", "Scale Multiplier", C_WARNING)
    ]

    for idx, (label, before, after, gain, col) in enumerate(stats):
        cx = Inches(0.8 + idx * 3.0)
        add_card(s7, cx, Inches(1.7), Inches(2.8), Inches(1.8))
        
        tb = s7.shapes.add_textbox(cx + Inches(0.1), Inches(1.8), Inches(2.6), Inches(1.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p_lbl = tf.paragraphs[0]
        p_lbl.text = label
        p_lbl.font.size = Pt(11)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = C_NAVY_HEADING

        p_aft = tf.add_paragraph()
        p_aft.text = after
        p_aft.font.size = Pt(22)
        p_aft.font.bold = True
        p_aft.font.color.rgb = col
        p_aft.space_before = Pt(4)

        p_bef = tf.add_paragraph()
        p_bef.text = f"Baseline: {before}  ({gain})"
        p_bef.font.size = Pt(9.5)
        p_bef.font.color.rgb = C_TEXT_MUTED
        p_bef.space_before = Pt(2)

    # Detailed Impact Breakdowns
    detail_impact = [
        ("🛡️ Capital Preservation & 1930 Interception", [
            "Intercepts funds while still in the banking network before mule cash-outs.",
            "CFCFRMS 2.0 has saved ₹11,158 Cr nationwide — Guardian maximizes this window by ensuring complete filings in < 5 minutes instead of hours."
        ]),
        ("👥 Customer Panic Mitigation & Multilingual Inclusivity", [
            "Converts sheer panic into structured, guided action via vernacular voice assistance (Hindi, Telugu, English).",
            "Eliminates fear of phone scams: in-app verified interaction never asks for sensitive financial secrets."
        ]),
        ("🏛️ Zero-Audit Liability (RBI FREE-AI & DPDP Compliance)", [
            "SHA-256 immutable audit chain provides complete transparency for regulatory investigations.",
            "Ensures full compliance with RBI's customer protection circular (zero customer liability on rapid reporting)."
        ])
    ]

    for idx, (title, points) in enumerate(detail_impact):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s7, cx, Inches(3.75), Inches(3.7), Inches(3.2))
        
        tb = s7.shapes.add_textbox(cx + Inches(0.2), Inches(3.9), Inches(3.3), Inches(2.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(12.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY_HEADING

        for pt in points:
            p_p = tf.add_paragraph()
            p_p.text = "• " + pt
            p_p.font.size = Pt(10.5)
            p_p.font.color.rgb = C_NAVY_HEADING
            p_p.space_before = Pt(8)

    # =========================================================================
    # SLIDE 8: BUSINESS MODEL & ECOSYSTEM FIT (Light)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, C_LIGHT_BG)
    add_header(s8, "Commercial Strategy & Value Realization", "Business Model & Paytm Ecosystem Fit")

    bm_cards = [
        ("🎯 Ecosystem Fit: Paytm Pi Add-On", C_PAYTM_BLUE, [
            ("Complementary to Paytm Pi", "Paytm Pi detects fraudulent risk patterns in real-time; Guardian provides the automated execution layer to act on those detections instantly."),
            ("Target Buyers", "Payment Aggregators (Paytm, Razorpay), Sponsor Banks (PPBL, Axis, HDFC), Digital Wallets & NBFCs."),
            ("Fills the Response Vacuum", "While MuleHunter.AI and I4C flag suspect accounts, banks lack rapid automated orchestration to protect victim accounts.")
        ]),
        ("💰 Monetization Streams", C_SUCCESS, [
            ("Tiered Enterprise SaaS", "Monthly subscription fee per active monitored user / per fraud alert volume processed."),
            ("Value-Share Recovery Model", "Contingency success fee (2-5%) on verified fraudulent funds preserved or reclaimed via CFCFRMS."),
            ("Partner Integration License", "Custom deployment in the partner's environment (Claude API under a partner DPA) and core-banking dispute pipeline integration.")
        ]),
        ("📈 ROI & Unit Economics", C_PURPLE, [
            ("Tenfold Cost Offset", "Preventing just 10 account takeovers per month (avg loss ₹50,000) saves ₹5,00,000/month in direct liability."),
            ("Labor Cost Compression", "Automates repetitive triage and evidence compilation, slashing fraud-ops operational overhead by 70%."),
            ("Customer Retention Dividend", "Prevents user churn and brand damage caused by unassisted fraud trauma.")
        ])
    ]

    for idx, (title, col, items) in enumerate(bm_cards):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s8, cx, Inches(1.8), Inches(3.7), Inches(5.1))
        
        top_bar = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, Inches(1.8), Inches(3.7), Inches(0.1))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = col
        top_bar.line.fill.background()

        tb = s8.shapes.add_textbox(cx + Inches(0.25), Inches(2.05), Inches(3.2), Inches(4.7))
        tf = tb.text_frame
        tf.word_wrap = True
        p_hd = tf.paragraphs[0]
        p_hd.text = title
        p_hd.font.size = Pt(14)
        p_hd.font.bold = True
        p_hd.font.color.rgb = C_NAVY_HEADING

        for it_h, it_b in items:
            p_ih = tf.add_paragraph()
            p_ih.text = "• " + it_h
            p_ih.font.size = Pt(11.5)
            p_ih.font.bold = True
            p_ih.font.color.rgb = col
            p_ih.space_before = Pt(10)
            p_ib = tf.add_paragraph()
            p_ib.text = it_b
            p_ib.font.size = Pt(10.5)
            p_ib.font.color.rgb = C_NAVY_HEADING
            p_ib.space_before = Pt(2)

    # =========================================================================
    # SLIDE 9: DEMO SCENARIOS & RESILIENCY (Light)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, C_LIGHT_BG)
    add_header(s9, "Battle-Tested E2E Scenarios (229 Tests Passing)", "Demonstration & Verification")

    scenarios = [
        ("Scenario: 'ato' (Account Takeover)", C_DANGER,
         "New device in distant city + SIM swapped 2h ago + rapid transfers to mule fan-in payee.",
         "Score 0.93 -> Instant Tier-1 outgoing hold -> Voice verification on trusted device -> Victim confirms NOT ME -> Contained in 48s -> Scribe builds evidence -> Officer approves dispute."),
        ("Scenario: 'genuine' (Low Friction)", C_SUCCESS,
         "Legitimate user making high-value festive purchase at a new merchant.",
         "Score 0.55 -> Prompted via trusted in-app voice -> Victim taps 'Yes, it was me' -> Outgoing hold released in < 20s. Zero manual analyst intervention required."),
        ("Scenario: 'injection' (Red Team Attack)", C_PURPLE,
         "Adversary attempts prompt injection to trick LLM into promising refund or bypassing policy.",
         "Regex guardrail & FSM intercept malicious syntax -> Blocked by Policy Engine -> Emits POLICY_BLOCKED event -> Dispatches officer callback."),
        ("Scenario: 'fallback' (Zero-Downtime)", C_NAVY_HEADING,
         "Claude API unreachable, slow, or no API key configured.",
         "8 s budget per call, no retries -> Engine switches to deterministic templates -> Zero service disruption -> Emits LLM_FALLBACK_USED audit event.")
    ]

    for idx, (s_title, s_col, s_story, s_res) in enumerate(scenarios):
        row = idx // 2
        col = idx % 2
        cx = Inches(0.8 + col * 6.0)
        cy = Inches(1.8 + row * 2.7)

        add_card(s9, cx, cy, Inches(5.7), Inches(2.45))
        top_bar = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cy, Inches(5.7), Inches(0.08))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = s_col
        top_bar.line.fill.background()

        tb = s9.shapes.add_textbox(cx + Inches(0.2), cy + Inches(0.15), Inches(5.3), Inches(2.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p_th = tf.paragraphs[0]
        p_th.text = s_title
        p_th.font.size = Pt(13.5)
        p_th.font.bold = True
        p_th.font.color.rgb = s_col

        p_st = tf.add_paragraph()
        p_st.text = "Setup: " + s_story
        p_st.font.size = Pt(10)
        p_st.font.bold = True
        p_st.font.color.rgb = C_NAVY_HEADING
        p_st.space_before = Pt(4)

        p_re = tf.add_paragraph()
        p_re.text = "Outcome: " + s_res
        p_re.font.size = Pt(9.5)
        p_re.font.color.rgb = C_TEXT_MUTED
        p_re.space_before = Pt(2)

    # =========================================================================
    # SLIDE 10: CONCLUSION & SUMMARY (Dark)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, C_DARK_BG)

    # Accent decorative bar
    bar10 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.1), Inches(0.8), Inches(0.08))
    bar10.fill.solid()
    bar10.fill.fore_color.rgb = C_PAYTM_BLUE
    bar10.line.fill.background()

    c10_tb = s10.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.7), Inches(0.4))
    tf10 = c10_tb.text_frame
    p10 = tf10.paragraphs[0]
    p10.text = "CONCLUSION & VISION"
    p10.font.size = Pt(12)
    p10.font.bold = True
    p10.font.color.rgb = C_PAYTM_BLUE

    c10_title = s10.shapes.add_textbox(Inches(0.8), Inches(1.7), Inches(11.7), Inches(1.0))
    tf10_t = c10_title.text_frame
    tf10_t.word_wrap = True
    p10_t = tf10_t.paragraphs[0]
    p10_t.text = "Winning the Golden Hour in Digital Payments"
    p10_t.font.size = Pt(36)
    p10_t.font.bold = True
    p10_t.font.color.rgb = C_WHITE

    # 3 Summary Pillar Cards
    summary_cards = [
        ("Action Over Passive Chat", "Traditional AI answers questions while fraud spreads. Guardian acts: executes holds, revokes sessions, and protects the victim in under 60 seconds."),
        ("Strict Policy Governance", "Enforces a 3-tier action policy in code. Zero hallucinations, zero secret leakage, and 100% auditable via cryptographic SHA-256 hash chains."),
        ("Ready for Paytm & India", "Seamlessly integrates as the autonomous execution teammate on top of Paytm Pi, scaling trust and safety across 350M+ digital payment users.")
    ]
    for idx, (head, desc) in enumerate(summary_cards):
        cx = Inches(0.8 + idx * 4.0)
        c = add_card(s10, cx, Inches(3.0), Inches(3.7), Inches(2.2), bg_color=RGBColor(23, 42, 69), border_color=RGBColor(51, 65, 85))
        c_tb = s10.shapes.add_textbox(cx + Inches(0.2), Inches(3.2), Inches(3.3), Inches(1.8))
        c_tf = c_tb.text_frame
        c_tf.word_wrap = True
        p1 = c_tf.paragraphs[0]
        p1.text = head
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = C_PAYTM_BLUE
        p2 = c_tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = RGBColor(203, 213, 225)
        p2.space_before = Pt(8)

    # Closing banner
    callout = add_card(s10, Inches(0.8), Inches(5.6), Inches(11.7), Inches(1.2), bg_color=RGBColor(15, 33, 64), border_color=C_PAYTM_BLUE)
    co_tb = s10.shapes.add_textbox(Inches(1.0), Inches(5.75), Inches(11.3), Inches(0.9))
    co_tf = co_tb.text_frame
    co_tf.word_wrap = True
    p_co = co_tf.paragraphs[0]
    p_co.text = "“In cyber-fraud, time is the attacker's weapon. Golden Hour Guardian makes time our shield.”"
    p_co.font.size = Pt(16)
    p_co.font.bold = True
    p_co.font.color.rgb = C_WHITE
    p_co.alignment = PP_ALIGN.CENTER
    p_co2 = co_tf.add_paragraph()
    p_co2.text = "Paytm Build for India AI Hackathon • Track 3: Autonomous AI Teammates • Ready for Live Demonstration"
    p_co2.font.size = Pt(11)
    p_co2.font.color.rgb = C_PAYTM_BLUE
    p_co2.alignment = PP_ALIGN.CENTER
    p_co2.space_before = Pt(4)

    prs.save(output_path)
    print(f"Presentation saved successfully to {output_path}")

if __name__ == "__main__":
    create_deck()
