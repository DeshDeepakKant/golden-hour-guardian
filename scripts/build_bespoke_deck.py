import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_bespoke_deck(output_path="Golden_Hour_Guardian_Pitch_Deck.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Bespoke Executive Palette (Stripe/Paytm High-End Fintech Design)
    C_OBSIDIAN = RGBColor(8, 14, 26)          # #080E1A Deep Obsidian
    C_SLATE_DARK = RGBColor(15, 23, 42)       # #0F172A
    C_SURFACE_DARK = RGBColor(19, 31, 53)     # #131F35 Terminal / Dark Card
    C_BORDER_DARK = RGBColor(38, 56, 89)      # #263859 Dark Border
    
    C_BG_LIGHT = RGBColor(248, 250, 252)      # #F8FAFC Premium Canvas
    C_CARD_WHITE = RGBColor(255, 255, 255)    # #FFFFFF Crisp Card
    C_BORDER_LIGHT = RGBColor(226, 232, 240)  # #E2E8F0 Subtle Border
    
    C_PAYTM_CYAN = RGBColor(0, 186, 242)      # #00BAF2 Official Brand Cyan
    C_PAYTM_DEEP = RGBColor(0, 46, 110)       # #002E6E Royal Trust Blue
    C_TEXT_PRIMARY = RGBColor(15, 23, 42)     # #0F172A Dark Slate Text
    C_TEXT_MUTED = RGBColor(100, 116, 139)    # #64748B Secondary Slate
    
    C_GREEN = RGBColor(16, 185, 129)          # #10B981 Success / Tier 1
    C_GREEN_TINT = RGBColor(240, 253, 244)    # #F0FDF4
    C_AMBER = RGBColor(217, 119, 6)           # #D97706 Warning / Tier 2
    C_AMBER_TINT = RGBColor(254, 243, 199)    # #FEF3C7
    C_RED = RGBColor(225, 29, 72)             # #E11D48 Danger / Tier 3
    C_RED_TINT = RGBColor(255, 241, 242)      # #FFF1F2
    C_CYAN_TINT = RGBColor(240, 249, 255)     # #F0F9FF

    FONT_FAMILY = "Calibri"

    def set_slide_bg(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_top_nav(slide, category_text, title_text, dark=False):
        # Category Tracker
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(11.7), Inches(0.3))
        tf_cat = cat_box.text_frame
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_c = tf_cat.paragraphs[0]
        p_c.text = category_text.upper()
        p_c.font.name = FONT_FAMILY
        p_c.font.size = Pt(10.5)
        p_c.font.bold = True
        p_c.font.color.rgb = C_PAYTM_CYAN

        # Main Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.65))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_t = tf_title.paragraphs[0]
        p_t.text = title_text
        p_t.font.name = FONT_FAMILY
        p_t.font.size = Pt(24)
        p_t.font.bold = True
        p_t.font.color.rgb = RGBColor(255, 255, 255) if dark else C_TEXT_PRIMARY

    def add_card(slide, left, top, width, height, bg_color=C_CARD_WHITE, border_color=C_BORDER_LIGHT):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.2)
        else:
            card.line.fill.background()
        return card

    def add_tag(slide, left, top, width, height, text, bg_color, text_color):
        tag = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        tag.fill.solid()
        tag.fill.fore_color.rgb = bg_color
        tag.line.fill.background()
        tb = slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_top = tf.margin_left = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = text
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_FAMILY
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = text_color
        return tag

    def set_notes(slide, text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = text.strip()

    # =========================================================================
    # SLIDE 1: BESPOKE TITLE SLIDE (Dark Obsidian & Live Telemetry Mockup)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s1, C_OBSIDIAN)

    # Hackathon Track Badge
    add_tag(s1, Inches(0.8), Inches(1.1), Inches(4.8), Inches(0.35),
            "PAYTM BUILD FOR INDIA  •  TRACK 3: AUTONOMOUS AI TEAMMATES",
            C_SURFACE_DARK, C_PAYTM_CYAN)

    # Main Title
    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.65), Inches(6.8), Inches(1.4))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_top = tf_t.margin_left = tf_t.margin_bottom = tf_t.margin_right = 0
    pt = tf_t.paragraphs[0]
    pt.text = "GOLDEN HOUR GUARDIAN"
    pt.font.name = FONT_FAMILY
    pt.font.size = Pt(40)
    pt.font.bold = True
    pt.font.color.rgb = RGBColor(255, 255, 255)

    # Subtitle
    sub_box = s1.shapes.add_textbox(Inches(0.8), Inches(3.1), Inches(6.8), Inches(1.0))
    sub_tf = sub_box.text_frame
    sub_tf.word_wrap = True
    sub_tf.margin_top = sub_tf.margin_left = sub_tf.margin_bottom = sub_tf.margin_right = 0
    ps = sub_tf.paragraphs[0]
    ps.text = "Autonomous AI Teammate for Real-Time UPI Fraud Containment & Victim Shielding"
    ps.font.name = FONT_FAMILY
    ps.font.size = Pt(18)
    ps.font.color.rgb = RGBColor(203, 213, 225)
    
    ps2 = sub_tf.add_paragraph()
    ps2.text = "From alert to victim protected in under 60 seconds — with human officers approving every monetary decision."
    ps2.font.name = FONT_FAMILY
    ps2.font.size = Pt(13)
    ps2.font.color.rgb = RGBColor(148, 163, 184)
    ps2.space_before = Pt(8)

    # Right: Live Telemetry Terminal Mockup (Gives immediate authentic technical credibility!)
    add_card(s1, Inches(7.8), Inches(1.1), Inches(4.7), Inches(5.1), bg_color=C_SURFACE_DARK, border_color=C_BORDER_DARK)
    
    # Terminal Header Bar
    term_hdr = s1.shapes.add_textbox(Inches(8.1), Inches(1.3), Inches(4.1), Inches(0.4))
    th_tf = term_hdr.text_frame
    th_tf.margin_top = th_tf.margin_left = th_tf.margin_bottom = th_tf.margin_right = 0
    pth = th_tf.paragraphs[0]
    pth.text = "● ● ●   LIVE FRAUD INCIDENT STREAM"
    pth.font.name = "Consolas"
    pth.font.size = Pt(10)
    pth.font.bold = True
    pth.font.color.rgb = C_PAYTM_CYAN

    # Terminal Log Content
    term_log = s1.shapes.add_textbox(Inches(8.1), Inches(1.85), Inches(4.1), Inches(4.1))
    tl_tf = term_log.text_frame
    tl_tf.word_wrap = True
    tl_tf.margin_top = tl_tf.margin_left = tl_tf.margin_bottom = tl_tf.margin_right = 0
    
    telemetry_lines = [
        ("[00:01s] ALERT INGESTED", "Score: 0.93 (Account Takeover Detected)", C_PAYTM_CYAN),
        ("[00:04s] SENTINEL TRIAGE", "Signals: SIM_SWAP_2H, IP_VELOCITY_ANOMALY", RGBColor(226, 232, 240)),
        ("[00:08s] SHIELD CONTAINMENT", "Tier-1 Auto-Hold placed on victim outgoing UPI", C_GREEN),
        ("[00:09s] TOKEN REVOCATION", "Malicious Android device session terminated", C_GREEN),
        ("[00:15s] VOICE ENGAGEMENT", "Native audio prompt initiated on trusted app (Hi/En)", RGBColor(226, 232, 240)),
        ("[00:48s] VICTIM CONFIRMATION", "Reply: 'Not Me' -> State: CONTAINED (T_protect: 48s)", C_GREEN),
        ("[00:52s] SCRIBE DOSSIER", "NCRP 1930 cybercrime filing package pre-filled", RGBColor(226, 232, 240)),
        ("[00:58s] OFFICER QUEUE", "Tier-2 Bank Dispute recommendation dispatched", C_AMBER)
    ]
    for tag_l, desc_l, col_l in telemetry_lines:
        p1 = tl_tf.add_paragraph() if tl_tf.paragraphs[0].text else tl_tf.paragraphs[0]
        p1.text = tag_l
        p1.font.name = "Consolas"
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = col_l
        p1.space_before = Pt(4)
        
        p2 = tl_tf.add_paragraph()
        p2.text = "  " + desc_l
        p2.font.name = "Consolas"
        p2.font.size = Pt(9)
        p2.font.color.rgb = RGBColor(148, 163, 184)
        p2.space_before = Pt(1)

    # Bottom Metric Bar on Left
    metrics_s1 = [
        ("< 60s", "Containment SLA"),
        ("100% Edge AI", "Zero Cloud PII Leak"),
        ("RBI FREE-AI", "Cryptographic Audit Chain")
    ]
    for idx, (m_val, m_lbl) in enumerate(metrics_s1):
        mx = Inches(0.8 + idx * 2.3)
        m_tb = s1.shapes.add_textbox(mx, Inches(5.2), Inches(2.1), Inches(1.0))
        m_tf = m_tb.text_frame
        m_tf.margin_top = m_tf.margin_left = m_tf.margin_bottom = m_tf.margin_right = 0
        p_mv = m_tf.paragraphs[0]
        p_mv.text = m_val
        p_mv.font.name = FONT_FAMILY
        p_mv.font.size = Pt(22)
        p_mv.font.bold = True
        p_mv.font.color.rgb = C_PAYTM_CYAN
        p_ml = m_tf.add_paragraph()
        p_ml.text = m_lbl
        p_ml.font.name = FONT_FAMILY
        p_ml.font.size = Pt(10)
        p_ml.font.color.rgb = RGBColor(148, 163, 184)
        p_ml.space_before = Pt(2)

    set_notes(s1, """
Good morning, judges. In cyber-fraud, the first 60 minutes—the Golden Hour—determines whether stolen money is recovered or permanently lost.
Today, chatbots merely answer questions while money drains into mule networks.
We present Golden Hour Guardian, an autonomous AI teammate designed for Paytm's fraud ecosystem. As shown in our live incident stream on the right, Guardian moves from fraud detection to active containment in under 60 seconds: placing temporary outgoing holds, revoking compromised sessions, engaging the victim in their native language, and assembling complete 1930 evidence dossiers for human fraud officers.
""")

    # =========================================================================
    # SLIDE 2: THE PROBLEM (High-Impact Data Callouts & The 35-Minute Gap)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s2, C_BG_LIGHT)
    add_top_nav(s2, "Problem Statement", "The 35-Minute Fraud Velocity Crisis in India")

    # Left: 3 Massive Graphic Numbers
    left_stats = [
        ("₹1,087 Cr", "Lost to UPI Frauds (FY24-25)", "13.4 Lakh incidents reported to Parliament by the Ministry of Finance. Fraud velocity is accelerating annually."),
        ("55%", "Account Takeover Share", "BioCatch India research confirms credential and device takeovers dominate digital payment attacks."),
        ("< 10 Mins", "Mule Account Velocity", "Attackers disperse stolen funds across 3-4 layers of mule accounts before a human analyst ever opens the alert.")
    ]
    for idx, (stat_n, stat_h, stat_d) in enumerate(left_stats):
        sy = Inches(1.55 + idx * 1.8)
        add_card(s2, Inches(0.8), sy, Inches(5.4), Inches(1.65))
        
        stb = s2.shapes.add_textbox(Inches(1.05), sy + Inches(0.15), Inches(5.0), Inches(1.35))
        stf = stb.text_frame
        stf.word_wrap = True
        stf.margin_top = stf.margin_left = stf.margin_bottom = stf.margin_right = 0
        p_sn = stf.paragraphs[0]
        p_sn.text = stat_n
        p_sn.font.name = FONT_FAMILY
        p_sn.font.size = Pt(28)
        p_sn.font.bold = True
        p_sn.font.color.rgb = C_RED if idx == 0 else (C_AMBER if idx == 1 else C_PAYTM_DEEP)
        
        p_sh = stf.add_paragraph()
        p_sh.text = stat_h
        p_sh.font.name = FONT_FAMILY
        p_sh.font.size = Pt(12)
        p_sh.font.bold = True
        p_sh.font.color.rgb = C_TEXT_PRIMARY
        p_sh.space_before = Pt(2)

        p_sd = stf.add_paragraph()
        p_sd.text = stat_d
        p_sd.font.name = FONT_FAMILY
        p_sd.font.size = Pt(10)
        p_sd.font.color.rgb = C_TEXT_MUTED
        p_sd.space_before = Pt(2)

    # Right: The Broken Response Waterfall Table
    add_card(s2, Inches(6.6), Inches(1.55), Inches(5.9), Inches(5.25))
    
    rtb = s2.shapes.add_textbox(Inches(6.9), Inches(1.8), Inches(5.3), Inches(0.5))
    rtf = rtb.text_frame
    rtf.margin_top = rtf.margin_left = rtf.margin_bottom = rtf.margin_right = 0
    p_rh = rtf.paragraphs[0]
    p_rh.text = "Where The 'Golden Hour' Is Lost (Manual Baseline)"
    p_rh.font.name = FONT_FAMILY
    p_rh.font.size = Pt(14)
    p_rh.font.bold = True
    p_rh.font.color.rgb = C_TEXT_PRIMARY

    waterfall_steps = [
        ("Alert Queue Waiting", "15 mins", "Alert waits for an available tier-1 fraud analyst."),
        ("Analyst Manual Triage", "7 mins", "Analyst cross-checks transaction logs, IP, and device ID."),
        ("Outbound Phone Callback", "10 mins", "Customer ignores call, suspecting a phone scam."),
        ("Manual Hold & Token Revocation", "3 mins", "Analyst executes manual commands across banking tools."),
        ("Manual Evidence Compilation", "25 mins", "Copy-pasting ledger entries and generating dispute forms."),
        ("Customer Guidance for 1930 / NCRP", "5 mins", "Confused victim struggles with national cybercrime portal.")
    ]

    for idx, (w_label, w_time, w_detail) in enumerate(waterfall_steps):
        wy = Inches(2.4 + idx * 0.65)
        # Time badge
        add_tag(s2, Inches(6.9), wy, Inches(1.1), Inches(0.45), w_time, C_AMBER_TINT if idx < 4 else C_RED_TINT, C_AMBER if idx < 4 else C_RED)
        
        wtb = s2.shapes.add_textbox(Inches(8.15), wy, Inches(4.1), Inches(0.48))
        wtf = wtb.text_frame
        wtf.word_wrap = True
        wtf.margin_top = wtf.margin_left = wtf.margin_bottom = wtf.margin_right = 0
        p_wl = wtf.paragraphs[0]
        p_wl.text = w_label
        p_wl.font.name = FONT_FAMILY
        p_wl.font.size = Pt(11)
        p_wl.font.bold = True
        p_wl.font.color.rgb = C_TEXT_PRIMARY
        
        p_wd = wtf.add_paragraph()
        p_wd.text = w_detail
        p_wd.font.name = FONT_FAMILY
        p_wd.font.size = Pt(9.5)
        p_wd.font.color.rgb = C_TEXT_MUTED

    # Total Callout at bottom of table
    add_tag(s2, Inches(6.9), Inches(6.3), Inches(5.3), Inches(0.35),
            "TOTAL TIME ELAPSED: ~65 MINUTES  •  FUNDS PERMANENTLY WITHDRAWN",
            C_RED, RGBColor(255, 255, 255))

    set_notes(s2, """
Let's quantify why digital fraud response is broken in India.
Over ₹1,000 crores are lost annually, with 55% stemming from account takeovers.
When funds are stolen, the money is moved across multiple mule accounts in under 10 minutes.
Yet, as our breakdown on the right shows, manual operations take 35 minutes just to execute a basic hold, and 65 minutes to prepare evidence.
By the time a human officer acts, the money has been withdrawn at an ATM or converted to crypto. The Golden Hour is lost before anyone takes action.
""")

    # =========================================================================
    # SLIDE 3: PROPOSED SOLUTION (The 4 Autonomous Teammates)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s3, C_BG_LIGHT)
    add_top_nav(s3, "Proposed Solution", "Meet Golden Hour Guardian: Autonomous Fraud Teammate")

    # Banner
    add_card(s3, Inches(0.8), Inches(1.5), Inches(11.7), Inches(0.75), bg_color=C_CYAN_TINT, border_color=C_PAYTM_CYAN)
    ov_tb = s3.shapes.add_textbox(Inches(1.05), Inches(1.58), Inches(11.2), Inches(0.6))
    ov_tf = ov_tb.text_frame
    ov_tf.word_wrap = True
    ov_tf.margin_top = ov_tf.margin_left = ov_tf.margin_bottom = ov_tf.margin_right = 0
    p_ov = ov_tf.paragraphs[0]
    p_ov.text = "Architecture Principle: Not an open-ended conversational bot. Guardian is a modular AI teammate running specialized deterministic and SLM roles under strict policy constraints."
    p_ov.font.name = FONT_FAMILY
    p_ov.font.size = Pt(12)
    p_ov.font.bold = True
    p_ov.font.color.rgb = C_PAYTM_DEEP

    # 4 Modular Roles
    roles = [
        ("SENTINEL", "Triage & Context Engine", C_PAYTM_DEEP, [
            ("Risk Evaluation", "Scores alerts (score >= 0.85 -> hold+verify path)."),
            ("SIM Swap Intelligence", "Flags SIM_CHANGE_72H: registered cellular line marked untrusted."),
            ("Channel Routing", "Directs verification to authenticated device, bypassing hijacked SIM.")
        ]),
        ("SHIELD", "Instant Containment", C_PAYTM_CYAN, [
            ("Tier-1 Outgoing Hold", "Halts outbound UPI on victim's own account (auto-expires in 60m)."),
            ("Session Revocation", "Terminates attacker's active tokens and device access in real-time."),
            ("Marketing Suppression", "Halts cross-sell SMS to prevent victim disorientation during crisis.")
        ]),
        ("VOICE", "Zero-Secret Dialogue", C_GREEN, [
            ("Vernacular Audio", "Proactive in-app prompts in English, Hindi, and Telugu on trusted hardware."),
            ("Zero-Secret Guarantee", "Hardcoded regex guardrails never ask for OTP, PIN, password, or CVV."),
            ("Panic-Optimized UX", "Provides 1-tap confirmation or speech input; handles distress gracefully.")
        ]),
        ("SCRIBE & DESK", "Evidence & Human Co-Pilot", C_SLATE_DARK, [
            ("1930 / NCRP Dossier", "Pre-fills national cybercrime reporting form with full transaction graph."),
            ("SLA Countdown Clocks", "Surfaces prioritized queue with active Golden-Hour countdown timers."),
            ("1-Click Dispute Dispatch", "Pre-computes partner bank dispute package for human officer approval.")
        ])
    ]

    for idx, (r_name, r_sub, r_col, r_points) in enumerate(roles):
        cx = Inches(0.8 + idx * 3.0)
        add_card(s3, cx, Inches(2.45), Inches(2.8), Inches(4.5))
        
        # Header Box inside Card
        add_tag(s3, cx + Inches(0.2), Inches(2.65), Inches(2.4), Inches(0.4), r_name, r_col, RGBColor(255, 255, 255))
        
        sub_tb = s3.shapes.add_textbox(cx + Inches(0.2), Inches(3.15), Inches(2.4), Inches(0.4))
        sub_tf = sub_tb.text_frame
        sub_tf.margin_top = sub_tf.margin_left = sub_tf.margin_bottom = sub_tf.margin_right = 0
        p_sub = sub_tf.paragraphs[0]
        p_sub.text = r_sub
        p_sub.alignment = PP_ALIGN.CENTER
        p_sub.font.name = FONT_FAMILY
        p_sub.font.size = Pt(10)
        p_sub.font.bold = True
        p_sub.font.color.rgb = C_TEXT_MUTED

        # Content Points
        b_tb = s3.shapes.add_textbox(cx + Inches(0.2), Inches(3.65), Inches(2.4), Inches(3.1))
        b_tf = b_tb.text_frame
        b_tf.word_wrap = True
        b_tf.margin_top = b_tf.margin_left = b_tf.margin_bottom = b_tf.margin_right = 0
        for p_idx, (p_title, p_desc) in enumerate(r_points):
            p1 = b_tf.paragraphs[0] if p_idx == 0 else b_tf.add_paragraph()
            p1.text = "• " + p_title
            p1.font.name = FONT_FAMILY
            p1.font.size = Pt(11)
            p1.font.bold = True
            p1.font.color.rgb = C_TEXT_PRIMARY
            p1.space_before = Pt(8 if p_idx > 0 else 0)

            p2 = b_tf.add_paragraph()
            p2.text = p_desc
            p2.font.name = FONT_FAMILY
            p2.font.size = Pt(9.5)
            p2.font.color.rgb = C_TEXT_MUTED
            p2.space_before = Pt(1)

    set_notes(s3, """
Here is how Golden Hour Guardian solves this crisis: it is an autonomous AI teammate structured into four logical roles.
Sentinel performs triage: it evaluates risk scores and detects SIM swap anomalies. If a SIM was swapped in the last 72 hours, it knows cellular calls are compromised and routes to the trusted app.
Shield executes immediate containment: placing an auto-expiring hold on the victim's own outgoing payments and killing rogue sessions.
Voice handles dialogue: verified in-app native speech in Hindi, Telugu, and English without ever asking for secrets.
And Scribe & Desk assemble the evidence and pre-fill national 1930 cybercrime reports, delivering 1-click dispute approvals to the human fraud officer.
""")

    # =========================================================================
    # SLIDE 4: ARCHITECTURE & POLICY TIERS (Zero Drift Governance)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s4, C_BG_LIGHT)
    add_top_nav(s4, "System Architecture & Policy Tiers", "Autonomous Execution with Zero Governance Drift")

    # Left: The 5-Step Pipeline Flow
    add_card(s4, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.45))
    
    w_tb = s4.shapes.add_textbox(Inches(1.05), Inches(1.7), Inches(5.1), Inches(0.4))
    w_tf = w_tb.text_frame
    w_tf.margin_top = w_tf.margin_left = w_tf.margin_bottom = w_tf.margin_right = 0
    p_wh = w_tf.paragraphs[0]
    p_wh.text = "Closed-Loop Autonomous Lifecycle"
    p_wh.font.name = FONT_FAMILY
    p_wh.font.size = Pt(14)
    p_wh.font.bold = True
    p_wh.font.color.rgb = C_TEXT_PRIMARY

    steps = [
        ("Step 1: Paytm Pi Alert Ingestion", "Receives high-velocity webhook (score >= 0.85, ATO signals, remote IP)."),
        ("Step 2: Tier-1 Instant Containment (< 5s)", "Shield places reversible hold on victim's outgoing UPI & revokes active sessions."),
        ("Step 3: Trusted Verification (5 - 30s)", "Proactive in-app voice prompt. If SIM swap detected, cellular line is rejected."),
        ("Step 4: Scribe Evidence Compilation", "Auto-assembles transaction graph, mule fan-in velocity, and pre-fills 1930 complaint."),
        ("Step 5: Officer Desk Approval (< 60s)", "Human officer reviews dossier with 1-click partner dispute action & audit verification.")
    ]

    for s_idx, (st_h, st_d) in enumerate(steps):
        sy = Inches(2.2 + s_idx * 0.9)
        add_tag(s4, Inches(1.05), sy, Inches(0.7), Inches(0.35), f"0{s_idx+1}", C_CYAN_TINT, C_PAYTM_DEEP)
        
        stb = s4.shapes.add_textbox(Inches(1.85), sy, Inches(4.3), Inches(0.75))
        stf = stb.text_frame
        stf.word_wrap = True
        stf.margin_top = stf.margin_left = stf.margin_bottom = stf.margin_right = 0
        p1 = stf.paragraphs[0]
        p1.text = st_h
        p1.font.name = FONT_FAMILY
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = C_TEXT_PRIMARY
        p2 = stf.add_paragraph()
        p2.text = st_d
        p2.font.name = FONT_FAMILY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = C_TEXT_MUTED
        p2.space_before = Pt(1)

    # Right: Hardcoded 3-Tier Policy Governance
    add_card(s4, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.45))
    
    ptb = s4.shapes.add_textbox(Inches(7.05), Inches(1.7), Inches(5.2), Inches(0.4))
    ptf = ptb.text_frame
    ptf.margin_top = ptf.margin_left = ptf.margin_bottom = ptf.margin_right = 0
    p_ph = ptf.paragraphs[0]
    p_ph.text = "Hardcoded 3-Tier Action Policy (RBI FREE-AI Aligned)"
    p_ph.font.name = FONT_FAMILY
    p_ph.font.size = Pt(14)
    p_ph.font.bold = True
    p_ph.font.color.rgb = C_TEXT_PRIMARY

    tier_specs = [
        ("TIER 1: AGENT ACTS ALONE (Reversible & Safe)", C_GREEN, C_GREEN_TINT,
         "• Temporary hold on victim's OWN outgoing UPI (auto-expires in 60m)\n• Revoke suspicious session tokens and unauthorized device access\n• Conduct voice/app verification; pre-fill 1930 NCRP complaint\n• Suppress outbound marketing messages to victim"),
        ("TIER 2: AGENT PREPARES, HUMAN APPROVES", C_AMBER, C_AMBER_TINT,
         "• Raise formal interbank dispute via partner bank channel\n• Extend hold beyond policy limit (>120 mins)\n• Release hold when verification arrives on untrusted SIM channel\n• Customer shadow-credit and final liability determinations"),
        ("TIER 3: HARD BLOCKED IN CODE (Legal Hard Rails)", C_RED, C_RED_TINT,
         "• NEVER freezes 3rd-party/beneficiary accounts (Police/CFCFRMS only)\n• NEVER files police complaints on victim's behalf (Victim must submit)\n• NEVER asks for OTP, PIN, password, or CVV\n• NEVER promises refunds or guarantees legal outcomes")
    ]

    for idx, (t_name, t_col, t_tint, t_body) in enumerate(tier_specs):
        ty = Inches(2.2 + idx * 1.5)
        add_card(s4, Inches(7.05), ty, Inches(5.2), Inches(1.35), bg_color=t_tint, border_color=t_col)
        
        tb = s4.shapes.add_textbox(Inches(7.2), ty + Inches(0.1), Inches(4.9), Inches(1.15))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        p1 = tf.paragraphs[0]
        p1.text = t_name
        p1.font.name = FONT_FAMILY
        p1.font.size = Pt(10.5)
        p1.font.bold = True
        p1.font.color.rgb = t_col

        p2 = tf.add_paragraph()
        p2.text = t_body
        p2.font.name = FONT_FAMILY
        p2.font.size = Pt(9)
        p2.font.color.rgb = C_TEXT_PRIMARY
        p2.space_before = Pt(3)

    set_notes(s4, """
In banking, autonomous AI must have strict legal boundaries.
We enforce a hardcoded 3-Tier Action Policy directly inside the engine code:
Tier 1 gives the AI autonomy over reversible, victim-side actions like temporary holds and session kills.
Tier 2 requires a human fraud officer to approve formal bank disputes, hold extensions, and financial liability decisions.
Tier 3 is physically impossible in code: the agent can never freeze third-party accounts, ask for OTPs, or promise refunds.
This ensures 100% compliance with RBI's customer protection circular and the FREE-AI governance mandate.
""")

    # =========================================================================
    # SLIDE 5: TECHNOLOGY & TECH STACK (Architecture Quadrants)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s5, C_BG_LIGHT)
    add_top_nav(s5, "Technology & Tech Stack", "Robust, Privacy-First Architecture")

    tech_blocks = [
        ("LOCAL SLM & PRIVACY LAYER", C_PAYTM_DEEP, [
            ("Ollama Qwen 4B / Qwen 2.5", "Local small language model for intent classification & risk explanation without cloud latency."),
            ("Zero Data Leakage (Edge AI)", "PII masked prior to model input; no financial data leaves bank infrastructure (DPDP Act 2023)."),
            ("Fail-Safe Regex Guardrails", "Multi-lingual scanner intercepts banned terms (OTP, PIN, refund); falls back to deterministic templates.")
        ]),
        ("HIGH-CONCURRENCY CORE ENGINE", C_PAYTM_CYAN, [
            ("Python 3.12 & FastAPI", "Asynchronous, event-driven API engine capable of processing thousands of alerts per second."),
            ("Deterministic State Machine", "Rigid FSM (NEW -> HELD -> CONTAINED -> EVIDENCE -> CLOSED) prevents invalid transitions."),
            ("Server-Sent Events (SSE)", "Real-time reactive streaming bus for officer console alerts and mobile victim app updates.")
        ]),
        ("MULTILINGUAL VOICE & MOBILE PWA", C_GREEN, [
            ("Web Speech STT & TTS", "Interactive speech synthesis & transcription supporting English, Hindi, and Telugu."),
            ("Mobile-First Victim PWA", "Low-bandwidth Progressive Web App running on Android/iOS with instant push-to-talk."),
            ("Panic-Optimized UX", "Large high-contrast buttons, audio readouts, and 1-tap copyable 1930 summary cards.")
        ]),
        ("CRYPTOGRAPHIC AUDITABILITY", C_SLATE_DARK, [
            ("SHA-256 Hash-Chained Log", "Every state transition, tool call, and human decision is cryptographically chained."),
            ("Verification Endpoint", "Built-in /audit/verify endpoint detects retroactive tampering or log manipulation."),
            ("RBI FREE-AI Ready", "Comprehensive audit trails adhering to RBI's August 2025 AI governance framework.")
        ])
    ]

    for idx, (t_title, t_col, t_points) in enumerate(tech_blocks):
        row = idx // 2
        col = idx % 2
        cx = Inches(0.8 + col * 6.0)
        cy = Inches(1.55 + row * 2.7)

        add_card(s5, cx, cy, Inches(5.7), Inches(2.5))
        add_tag(s5, cx + Inches(0.25), cy + Inches(0.2), Inches(3.2), Inches(0.35), t_title, C_CYAN_TINT, t_col)

        tb = s5.shapes.add_textbox(cx + Inches(0.25), cy + Inches(0.7), Inches(5.2), Inches(1.65))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        for p_idx, (sub, body) in enumerate(t_points):
            p1 = tf.paragraphs[0] if p_idx == 0 else tf.add_paragraph()
            p1.text = "• " + sub + ": "
            p1.font.name = FONT_FAMILY
            p1.font.size = Pt(10.5)
            p1.font.bold = True
            p1.font.color.rgb = C_TEXT_PRIMARY
            p1.space_before = Pt(4 if p_idx > 0 else 0)

            p2 = tf.add_paragraph()
            p2.text = "   " + body
            p2.font.name = FONT_FAMILY
            p2.font.size = Pt(9.5)
            p2.font.color.rgb = C_TEXT_MUTED
            p2.space_before = Pt(1)

    set_notes(s5, """
Our technology stack is built for high throughput and zero data leakage.
We run a local Small Language Model—Ollama Qwen—on-premise. All customer identifiers and PII are masked before reaching the model.
Our core engine is built on Python 3.12 and FastAPI with a deterministic Finite State Machine and SSE event streaming.
Multilingual voice is powered by browser-native Web Speech STT and TTS in Hindi, Telugu, and English.
And every single action is recorded in an immutable SHA-256 cryptographic hash chain, fulfilling RBI's FREE-AI auditability mandate.
""")

    # =========================================================================
    # SLIDE 6: USP (Comparison Matrix Table)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s6, C_BG_LIGHT)
    add_top_nav(s6, "Unique Selling Proposition", "Why Golden Hour Guardian Wins")

    # Clean Styled Comparison Table (No AI slop! Real tabular comparison)
    table_shape = s6.shapes.add_table(6, 4, Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.4))
    tbl = table_shape.table

    # Set column widths
    tbl.columns[0].width = Inches(2.2)
    tbl.columns[1].width = Inches(3.0)
    tbl.columns[2].width = Inches(3.0)
    tbl.columns[3].width = Inches(3.5)

    headers = ["CAPABILITY", "GENERIC AI CHATBOTS", "LEGACY RULE ENGINES", "GOLDEN HOUR GUARDIAN"]
    for col_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_PAYTM_DEEP if col_idx < 3 else C_PAYTM_CYAN
        tf = cell.text_frame
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = Inches(0.1)
        p = tf.paragraphs[0]
        p.text = h_text
        p.font.name = FONT_FAMILY
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

    matrix_rows = [
        ("Action Orientation", "Passive Q&A; provides FAQ links while money drains.", "Flag alerts in queue; zero automated customer outreach.", "Autonomous Tier-1 containment (hold & session kill) in < 60s."),
        ("SIM-Swap Awareness", "Fooled by phone hijack; calls the compromised SIM.", "Ignores SIM history; flags transaction without channel context.", "Detects SIM_CHANGE_72H; invalidates phone line and verifies in-app."),
        ("Data Privacy (DPDP)", "Sends customer PII to external cloud LLM APIs.", "Internal rules; no intelligence or conversational triage.", "100% on-premise SLM; masked PII; zero cloud data leakage."),
        ("Human Collaboration", "Attempts to replace support; causes customer panic.", "Floods analyst queues with high false-positive alert volume.", "Equips officers with pre-assembled dossiers and SLA countdowns."),
        ("1930 / NCRP Integration", "Tells victim to 'call 1930' with no assistance.", "None; leaves customer to navigate police portals alone.", "Pre-fills national cybercrime filing packet for 1-tap victim reporting.")
    ]

    for row_idx, row_data in enumerate(matrix_rows, start=1):
        for col_idx, cell_text in enumerate(row_data):
            cell = tbl.cell(row_idx, col_idx)
            cell.fill.solid()
            # Highlight Guardian column with subtle cyan tint
            if col_idx == 3:
                cell.fill.fore_color.rgb = C_CYAN_TINT
            elif row_idx % 2 == 1:
                cell.fill.fore_color.rgb = RGBColor(255, 255, 255)
            else:
                cell.fill.fore_color.rgb = RGBColor(241, 245, 249)

            tf = cell.text_frame
            tf.word_wrap = True
            tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = Inches(0.08)
            p = tf.paragraphs[0]
            p.text = cell_text
            p.font.name = FONT_FAMILY
            p.font.size = Pt(9.5) if col_idx > 0 else Pt(10)
            p.font.bold = True if col_idx == 0 or col_idx == 3 else False
            p.font.color.rgb = C_PAYTM_DEEP if col_idx == 3 else C_TEXT_PRIMARY

    set_notes(s6, """
Why does Golden Hour Guardian stand out in Track 3?
Look at this comparison matrix:
Generic AI chatbots only offer passive Q&A—they tell a victim whose money is vanishing to read a help article.
Legacy fraud engines flag alerts that sit in queues, with zero customer containment.
Guardian is the only system that executes autonomous Tier-1 containment in under 60 seconds, detects SIM-swap channel risks, preserves full data privacy with local SLMs, and pre-fills national 1930 cybercrime complaints.
""")

    # =========================================================================
    # SLIDE 7: IMPACT & MEASURABLE OUTCOMES
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s7, C_BG_LIGHT)
    add_top_nav(s7, "Impact & Benefits", "Measurable Outcomes for Victims, Officers & Banks")

    # 4 Massive KPI Callouts on Top
    kpis = [
        ("< 60s", "T_PROTECT (CONTAINMENT)", "Manual Baseline: 35 mins", "> 97% Faster", C_GREEN, C_GREEN_TINT),
        ("< 5m", "T_READY (EVIDENCE DOSSIER)", "Manual Baseline: 65 mins", "> 92% Faster", C_PAYTM_CYAN, C_CYAN_TINT),
        ("< 20s", "GENUINE USER FRICTION", "Manual Baseline: Hours of Hold", "Zero Friction", C_PAYTM_DEEP, C_CARD_WHITE),
        ("8x - 10x", "OFFICER CASE CAPACITY", "Manual Baseline: 1x Queue", "Scale Multiplier", C_AMBER, C_AMBER_TINT)
    ]

    for idx, (num, label, base, badge, col, tint) in enumerate(kpis):
        cx = Inches(0.8 + idx * 3.0)
        add_card(s7, cx, Inches(1.5), Inches(2.8), Inches(2.0), bg_color=tint, border_color=col)
        
        tb = s7.shapes.add_textbox(cx + Inches(0.15), Inches(1.65), Inches(2.5), Inches(1.7))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        
        p_n = tf.paragraphs[0]
        p_n.text = num
        p_n.font.name = FONT_FAMILY
        p_n.font.size = Pt(30)
        p_n.font.bold = True
        p_n.font.color.rgb = col

        p_l = tf.add_paragraph()
        p_l.text = label
        p_l.font.name = FONT_FAMILY
        p_l.font.size = Pt(10)
        p_l.font.bold = True
        p_l.font.color.rgb = C_TEXT_PRIMARY
        p_l.space_before = Pt(3)

        p_b = tf.add_paragraph()
        p_b.text = base + f" ({badge})"
        p_b.font.name = FONT_FAMILY
        p_b.font.size = Pt(9)
        p_b.font.color.rgb = C_TEXT_MUTED
        p_b.space_before = Pt(2)

    # 3 Strategic Benefits Below
    benefits = [
        ("Capital Preservation & Mule Interception", [
            "Intercepts funds while still in the banking network before mule cash-outs at ATMs.",
            "CFCFRMS 2.0 has saved ₹11,158 Cr nationwide — Guardian maximizes this window by ensuring complete filings in < 5 minutes instead of hours."
        ]),
        ("Panic Mitigation & Multilingual Inclusivity", [
            "Converts sheer panic into structured, guided action via vernacular voice assistance (Hindi, Telugu, English).",
            "Eliminates fear of phone scams: in-app verified interaction never asks for sensitive financial secrets."
        ]),
        ("Zero-Audit Liability (RBI FREE-AI & DPDP)", [
            "SHA-256 immutable audit chain provides complete transparency for regulatory investigations.",
            "Ensures full compliance with RBI customer protection guidelines (zero customer liability on rapid reporting)."
        ])
    ]

    for idx, (title, pts) in enumerate(benefits):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s7, cx, Inches(3.75), Inches(3.7), Inches(3.2))
        
        tb = s7.shapes.add_textbox(cx + Inches(0.2), Inches(3.95), Inches(3.3), Inches(2.8))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_FAMILY
        p_t.font.size = Pt(12.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_PRIMARY

        for pt in pts:
            p_p = tf.add_paragraph()
            p_p.text = "• " + pt
            p_p.font.name = FONT_FAMILY
            p_p.font.size = Pt(10)
            p_p.font.color.rgb = C_TEXT_MUTED
            p_p.space_before = Pt(6)

    set_notes(s7, """
The outcomes are quantifiable and dramatic.
Containment time drops from a manual baseline of 35 minutes to under 60 seconds—a 97% reduction in exposure.
Evidence readiness drops from 65 minutes to under 5 minutes.
Honest customers face near-zero friction: legitimate transactions are released in under 20 seconds.
And fraud analysts experience an 8x to 10x throughput multiplier, meaning teams can handle severe transaction spikes during festive sales without expanding headcount.
""")

    # =========================================================================
    # SLIDE 8: BUSINESS MODEL & PAYTM ECOSYSTEM FIT
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s8, C_BG_LIGHT)
    add_top_nav(s8, "Business Model & Paytm Ecosystem Fit", "Commercial Strategy & Value Realization")

    bm_cards = [
        ("ECOSYSTEM FIT: PAYTM PI ADD-ON", C_PAYTM_DEEP, [
            ("Complementary to Paytm Pi", "Paytm Pi detects fraudulent risk patterns in real time; Guardian provides the automated execution layer to act on those detections instantly."),
            ("Target Buyers", "Payment Aggregators (Paytm, Razorpay), Sponsor Banks (PPBL, Axis, HDFC), Digital Wallets & NBFCs."),
            ("Fills the Response Vacuum", "While MuleHunter.AI and I4C flag suspect accounts, banks lack rapid automated orchestration to protect victim accounts.")
        ]),
        ("MONETIZATION STREAMS", C_GREEN, [
            ("Tiered Enterprise SaaS", "Monthly subscription fee per active monitored user / per fraud alert volume processed."),
            ("Value-Share Recovery Model", "Contingency success fee (2-5%) on verified fraudulent funds preserved or reclaimed via CFCFRMS."),
            ("Partner Integration License", "Custom on-premise deployment and core-banking dispute pipeline integration.")
        ]),
        ("ROI & UNIT ECONOMICS", C_AMBER, [
            ("Tenfold Cost Offset", "Preventing just 10 account takeovers per month (avg loss ₹50,000) saves ₹5,00,000/month in direct liability."),
            ("Labor Cost Compression", "Automates repetitive triage and evidence compilation, slashing fraud-ops operational overhead by 70%."),
            ("Customer Retention Dividend", "Prevents user churn and brand damage caused by unassisted fraud trauma.")
        ])
    ]

    for idx, (title, col, items) in enumerate(bm_cards):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s8, cx, Inches(1.6), Inches(3.7), Inches(5.3))
        add_tag(s8, cx + Inches(0.25), Inches(1.85), Inches(3.2), Inches(0.35), title, C_CYAN_TINT, col)

        ib_tb = s8.shapes.add_textbox(cx + Inches(0.25), Inches(2.4), Inches(3.2), Inches(4.3))
        ib_tf = ib_tb.text_frame
        ib_tf.word_wrap = True
        ib_tf.margin_top = ib_tf.margin_left = ib_tf.margin_bottom = ib_tf.margin_right = 0
        for it_idx, (it_h, it_b) in enumerate(items):
            p1 = ib_tf.paragraphs[0] if it_idx == 0 else ib_tf.add_paragraph()
            p1.text = "• " + it_h
            p1.font.name = FONT_FAMILY
            p1.font.size = Pt(11)
            p1.font.bold = True
            p1.font.color.rgb = C_TEXT_PRIMARY
            p1.space_before = Pt(8 if it_idx > 0 else 0)

            p2 = ib_tf.add_paragraph()
            p2.text = it_b
            p2.font.name = FONT_FAMILY
            p2.font.size = Pt(10)
            p2.font.color.rgb = C_TEXT_MUTED
            p2.space_before = Pt(2)

    set_notes(s8, """
Our business model is an ideal expansion for Paytm.
Paytm Pi is sold to banks and fintechs for fraud detection. Golden Hour Guardian is the natural 'Autonomous Response Teammate' module on top of Pi.
We monetize through enterprise B2B SaaS licensing and a value-share model on preserved funds.
The unit economics are compelling: if a partner bank prevents just 10 account takeovers a month, the platform pays for itself tenfold while slashing manual fraud-ops overhead by 70%.
""")

    # =========================================================================
    # SLIDE 9: DEMO SCENARIOS & RESILIENCY (229 Tests)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s9, C_BG_LIGHT)
    add_top_nav(s9, "Demonstration & Verification", "Battle-Tested Scenarios (229 Automated Tests Passing)")

    scenarios = [
        ("SCENARIO: 'ATO' (ACCOUNT TAKEOVER)", C_RED, C_RED_TINT,
         "New device in distant city + SIM swapped 2h ago + rapid transfers to mule fan-in payee.",
         "Score 0.93 -> Instant Tier-1 outgoing hold -> Voice verification on trusted device -> Victim confirms NOT ME -> Contained in 48s -> Scribe builds evidence -> Officer approves dispute."),
        ("SCENARIO: 'GENUINE' (LOW FRICTION)", C_GREEN, C_GREEN_TINT,
         "Legitimate user making high-value festive purchase at a new merchant.",
         "Score 0.55 -> Prompted via trusted in-app voice -> Victim taps 'Yes, it was me' -> Outgoing hold released in < 20s. Zero manual analyst intervention required."),
        ("SCENARIO: 'INJECTION' (RED TEAM ATTACK)", C_PAYTM_DEEP, C_CYAN_TINT,
         "Adversary attempts prompt injection to trick LLM into promising refund or bypassing policy.",
         "Regex guardrail & FSM intercept malicious syntax -> Blocked by Policy Engine -> Emits POLICY_BLOCKED event -> Dispatches officer callback."),
        ("SCENARIO: 'FALLBACK' (ZERO-DOWNTIME)", C_SLATE_DARK, C_CARD_WHITE,
         "Local Ollama SLM offline or response latency exceeds timeout threshold.",
         "Engine automatically switches to deterministic fallback templates -> Zero service disruption -> Emits LLM_FALLBACK_USED audit event.")
    ]

    for idx, (s_title, s_col, s_tint, s_story, s_res) in enumerate(scenarios):
        row = idx // 2
        col = idx % 2
        cx = Inches(0.8 + col * 6.0)
        cy = Inches(1.55 + row * 2.7)

        add_card(s9, cx, cy, Inches(5.7), Inches(2.5), bg_color=s_tint, border_color=s_col)
        add_tag(s9, cx + Inches(0.25), cy + Inches(0.2), Inches(3.6), Inches(0.35), s_title, C_CARD_WHITE, s_col)

        b_tb = s9.shapes.add_textbox(cx + Inches(0.25), cy + Inches(0.65), Inches(5.2), Inches(1.75))
        b_tf = b_tb.text_frame
        b_tf.word_wrap = True
        b_tf.margin_top = b_tf.margin_left = b_tf.margin_bottom = b_tf.margin_right = 0
        
        p1 = b_tf.paragraphs[0]
        p1.text = "Setup: " + s_story
        p1.font.name = FONT_FAMILY
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = C_TEXT_PRIMARY
        p1.space_before = Pt(2)

        p2 = b_tf.add_paragraph()
        p2.text = "Outcome: " + s_res
        p2.font.name = FONT_FAMILY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = C_TEXT_MUTED
        p2.space_before = Pt(4)

    set_notes(s9, """
Our system is live and verified with 229 automated tests.
In our demo, we showcase four critical scenarios:
First, an Account Takeover where funds are contained in 48 seconds, evidence is packaged, and the human officer approves the dispute.
Second, a genuine high-value purchase verified and released in 20 seconds.
Third, a red-team adversarial injection attack that is intercepted and blocked by our policy guardrails.
And fourth, zero-downtime resiliency: even if the local LLM goes offline, the system continues running flawlessly on deterministic templates.
""")

    # =========================================================================
    # SLIDE 10: CONCLUSION & VISION (Dark Obsidian Theme)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s10, C_OBSIDIAN)

    add_tag(s10, Inches(0.8), Inches(1.1), Inches(3.2), Inches(0.35),
            "CONCLUSION & STRATEGIC VISION", C_SURFACE_DARK, C_PAYTM_CYAN)

    c10_title = s10.shapes.add_textbox(Inches(0.8), Inches(1.65), Inches(11.7), Inches(0.9))
    tf10_t = c10_title.text_frame
    tf10_t.word_wrap = True
    tf10_t.margin_top = tf10_t.margin_left = tf10_t.margin_bottom = tf10_t.margin_right = 0
    p10_t = tf10_t.paragraphs[0]
    p10_t.text = "Winning the Golden Hour in Digital Payments"
    p10_t.font.name = FONT_FAMILY
    p10_t.font.size = Pt(36)
    p10_t.font.bold = True
    p10_t.font.color.rgb = RGBColor(255, 255, 255)

    summary_cards = [
        ("ACTION OVER WORDS", "Traditional AI answers questions while fraud spreads. Guardian acts: executes holds, revokes sessions, and protects the victim in under 60 seconds."),
        ("UNBREAKABLE GOVERNANCE", "Enforces a 3-tier action policy in code. Zero hallucinations, zero secret leakage, and 100% auditable via cryptographic SHA-256 hash chains."),
        ("BUILT FOR PAYTM & INDIA", "Seamlessly integrates as the autonomous execution teammate on top of Paytm Pi, scaling trust and safety across 350M+ digital payment users.")
    ]
    for idx, (head, desc) in enumerate(summary_cards):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s10, cx, Inches(2.75), Inches(3.7), Inches(2.35), bg_color=C_SURFACE_DARK, border_color=C_BORDER_DARK)
        add_tag(s10, cx + Inches(0.25), Inches(3.0), Inches(2.6), Inches(0.35), head, C_OBSIDIAN, C_PAYTM_CYAN)

        b_tb = s10.shapes.add_textbox(cx + Inches(0.25), Inches(3.55), Inches(3.2), Inches(1.3))
        b_tf = b_tb.text_frame
        b_tf.word_wrap = True
        b_tf.margin_top = b_tf.margin_left = b_tf.margin_bottom = b_tf.margin_right = 0
        p2 = b_tf.paragraphs[0]
        p2.text = desc
        p2.font.name = FONT_FAMILY
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = RGBColor(203, 213, 225)
        p2.space_before = Pt(2)

    # Closing Callout Box
    callout = add_card(s10, Inches(0.8), Inches(5.4), Inches(11.7), Inches(1.35), bg_color=C_SURFACE_DARK, border_color=C_PAYTM_CYAN)
    co_tb = s10.shapes.add_textbox(Inches(1.0), Inches(5.55), Inches(11.3), Inches(1.0))
    co_tf = co_tb.text_frame
    co_tf.word_wrap = True
    co_tf.margin_top = co_tf.margin_left = co_tf.margin_bottom = co_tf.margin_right = 0
    p_co = co_tf.paragraphs[0]
    p_co.text = "“In cyber-fraud, time is the attacker's weapon. Golden Hour Guardian makes time our shield.”"
    p_co.font.name = FONT_FAMILY
    p_co.font.size = Pt(16)
    p_co.font.bold = True
    p_co.font.color.rgb = RGBColor(255, 255, 255)
    p_co.alignment = PP_ALIGN.CENTER

    p_co2 = co_tf.add_paragraph()
    p_co2.text = "Paytm Build for India AI Hackathon • Track 3: Autonomous AI Teammates • Ready for Live Demonstration"
    p_co2.font.name = FONT_FAMILY
    p_co2.font.size = Pt(11)
    p_co2.font.color.rgb = C_PAYTM_CYAN
    p_co2.alignment = PP_ALIGN.CENTER
    p_co2.space_before = Pt(4)

    set_notes(s10, """
In cyber-fraud, time is the attacker's weapon. Golden Hour Guardian makes time our shield.
By taking autonomous, reversible action in the first 60 seconds and empowering human fraud officers with complete evidence, we win the Golden Hour.
We are fully deployed, tested, and ready for your live demonstration. Thank you, and we welcome your questions!
""")

    prs.save(output_path)
    print(f"Bespoke deck saved successfully to: {output_path}")

if __name__ == "__main__":
    create_bespoke_deck()
