import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_presentation(output_path="Golden_Hour_Guardian_Pitch_Deck.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Professional Palette (Paytm Fintech Theme)
    # Dominance: 65% Slate/Navy, 25% Pure White & Subtle Tints, 10% Sharp Paytm Cyan Accent
    C_DARK_BG = RGBColor(10, 25, 47)          # #0A192F Deep Executive Navy
    C_DARK_CARD = RGBColor(23, 42, 69)        # #172A45 Elevated Navy
    C_DARK_BORDER = RGBColor(51, 65, 85)      # #334155
    C_LIGHT_BG = RGBColor(248, 250, 252)      # #F8FAFC Premium Off-White
    C_WHITE = RGBColor(255, 255, 255)         # #FFFFFF
    C_CARD_BG = RGBColor(255, 255, 255)       # Pure White Cards
    C_CARD_BORDER = RGBColor(226, 232, 240)   # #E2E8F0 Subtle Border

    # Brand & Semantic Accents
    C_PAYTM_CYAN = RGBColor(0, 186, 242)      # #00BAF2 Paytm Brand Cyan
    C_DEEP_BLUE = RGBColor(0, 46, 110)        # #002E6E Trust Blue
    C_HEADING_DARK = RGBColor(15, 23, 42)     # #0F172A Dark Slate Header
    C_BODY_DARK = RGBColor(51, 65, 85)        # #334155 Readable Body
    C_TEXT_MUTED = RGBColor(100, 116, 139)    # #64748B Secondary Text
    
    # Policy / KPI Semantic Colors
    C_EMERALD = RGBColor(16, 185, 129)        # #10B981 Success / Tier 1
    C_EMERALD_TINT = RGBColor(236, 253, 245)  # #ECFDF5
    C_AMBER = RGBColor(217, 119, 6)           # #D97706 Warning / Tier 2
    C_AMBER_TINT = RGBColor(254, 243, 199)    # #FEF3C7
    C_ROSE = RGBColor(225, 29, 72)            # #E11D48 Danger / Tier 3
    C_ROSE_TINT = RGBColor(255, 241, 242)     # #FFF1F2
    C_CYAN_TINT = RGBColor(240, 249, 255)     # #F0F9FF Light Info Tint

    FONT_FAMILY = "Calibri"

    def set_bg(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text, dark=False):
        # Category Badge
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = FONT_FAMILY
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = C_PAYTM_CYAN

        # Slide Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.78), Inches(11.7), Inches(0.65))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = FONT_FAMILY
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = C_WHITE if dark else C_HEADING_DARK

    def add_card(slide, left, top, width, height, bg_color=C_CARD_BG, border_color=C_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.2)
        else:
            card.line.fill.background()
        return card

    def add_circle_badge(slide, left, top, size, bg_color, text, text_color):
        circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, size, size)
        circle.fill.solid()
        circle.fill.fore_color.rgb = bg_color
        circle.line.fill.background()
        tb = slide.shapes.add_textbox(left, top, size, size)
        tf = tb.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = text
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_FAMILY
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = text_color
        return circle

    def set_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text.strip()

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (Dark Executive Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1, C_DARK_BG)

    # Hackathon Track Pill
    pill = add_card(s1, Inches(0.8), Inches(1.2), Inches(6.8), Inches(0.45), bg_color=C_DARK_CARD, border_color=C_PAYTM_CYAN)
    p_tb = s1.shapes.add_textbox(Inches(0.9), Inches(1.22), Inches(6.6), Inches(0.4))
    p_tf = p_tb.text_frame
    p_tf.margin_top = p_tf.margin_left = p_tf.margin_bottom = p_tf.margin_right = 0
    p1 = p_tf.paragraphs[0]
    p1.text = "PAYTM BUILD FOR INDIA AI HACKATHON  •  TRACK 3: AUTONOMOUS AI TEAMMATES"
    p1.font.name = FONT_FAMILY
    p1.font.size = Pt(11)
    p1.font.bold = True
    p1.font.color.rgb = C_PAYTM_CYAN

    # Project Title
    m_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.85), Inches(11.7), Inches(1.3))
    m_tf = m_box.text_frame
    m_tf.word_wrap = True
    m_tf.margin_top = m_tf.margin_left = m_tf.margin_bottom = m_tf.margin_right = 0
    pm = m_tf.paragraphs[0]
    pm.text = "GOLDEN HOUR GUARDIAN"
    pm.font.name = FONT_FAMILY
    pm.font.size = Pt(44)
    pm.font.bold = True
    pm.font.color.rgb = C_WHITE

    # Subtitle
    sub_box = s1.shapes.add_textbox(Inches(0.8), Inches(3.2), Inches(11.7), Inches(0.7))
    sub_tf = sub_box.text_frame
    sub_tf.word_wrap = True
    sub_tf.margin_top = sub_tf.margin_left = sub_tf.margin_bottom = sub_tf.margin_right = 0
    psub = sub_tf.paragraphs[0]
    psub.text = "The Autonomous AI Teammate for Real-Time UPI Fraud Containment & Victim Protection"
    psub.font.name = FONT_FAMILY
    psub.font.size = Pt(20)
    psub.font.color.rgb = RGBColor(203, 213, 225)

    # 3 Hero Highlight Cards (Clean rounded boxes, no cheesy accent lines)
    hero_cards = [
        ("⚡", "< 60s Containment", "Autonomous Tier-1 hold on victim's outgoing payments & immediate session revocation."),
        ("🎙️", "Multilingual Voice Outreach", "Proactive verification in En, Hi, Te on verified trusted device without asking for secrets."),
        ("📋", "1930 / NCRP Filing Ready", "Auto-assembles forensic evidence dossier and pre-fills national cybercrime complaints.")
    ]
    for idx, (icon, head, desc) in enumerate(hero_cards):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s1, cx, Inches(4.3), Inches(3.7), Inches(1.8), bg_color=C_DARK_CARD, border_color=C_DARK_BORDER)
        
        # Circle badge for icon
        add_circle_badge(s1, cx + Inches(0.25), Inches(4.55), Inches(0.55), RGBColor(15, 33, 64), icon, C_PAYTM_CYAN)
        
        c_tb = s1.shapes.add_textbox(cx + Inches(0.95), Inches(4.5), Inches(2.5), Inches(1.4))
        c_tf = c_tb.text_frame
        c_tf.word_wrap = True
        c_tf.margin_top = c_tf.margin_left = c_tf.margin_bottom = c_tf.margin_right = 0
        p_h = c_tf.paragraphs[0]
        p_h.text = head
        p_h.font.name = FONT_FAMILY
        p_h.font.size = Pt(14)
        p_h.font.bold = True
        p_h.font.color.rgb = C_WHITE
        p_d = c_tf.add_paragraph()
        p_d.text = desc
        p_d.font.name = FONT_FAMILY
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = RGBColor(148, 163, 184)
        p_d.space_before = Pt(4)

    # Bottom Thesis statement
    ft_box = s1.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.4))
    ft_tf = ft_box.text_frame
    p_ft = ft_tf.paragraphs[0]
    p_ft.text = "Track 3 Thesis: Build AI teammates that don't just respond; they get the job done under strict human governance."
    p_ft.font.name = FONT_FAMILY
    p_ft.font.size = Pt(11.5)
    p_ft.font.italic = True
    p_ft.font.color.rgb = RGBColor(148, 163, 184)

    set_notes(s1, """
Good morning, judges. When a digital payment account is taken over, the first 60 minutes—the Golden Hour—determines whether money is recovered or permanently lost. Today, chatbots only give advice while funds evaporate through mule accounts. 
We present Golden Hour Guardian, an autonomous AI teammate designed for Paytm's fraud ecosystem. Guardian doesn't just answer questions; it executes bounded, reversible containment actions in under 60 seconds, conducts native multilingual voice verification, compiles ready-to-file national 1930 evidence dossiers, and empowers human fraud officers with one-click dispute approvals.
""")

    # =========================================================================
    # SLIDE 2: PROBLEM STATEMENT (Light Executive Theme)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2, C_LIGHT_BG)
    add_header(s2, "The Critical 60-Minute Crisis in UPI Fraud", "Problem Statement")

    prob_cols = [
        ("🚨", "The Fraud Explosion", C_ROSE, [
            ("₹1,087+ Crore lost in UPI frauds", "Over 13.4 lakh incidents reported in Lok Sabha (FY24-25)."),
            ("55% Account Takeovers (ATO)", "BioCatch India data: attackers target rapid device and credential takeover."),
            ("Mule Relay Networks", "Funds are layered across multi-tier mule accounts in under 10 minutes.")
        ]),
        ("⏳", "The Broken Manual Response", C_AMBER, [
            ("35+ Min Alert-to-Action Lag", "Alert sits in queue (15m) + analyst triage (7m) + manual call attempts (10m)."),
            ("65+ Min Evidence Compilation", "Analysts manually gather ledger records, device tokens, and IP histories."),
            ("The Missed 'Golden Hour'", "By the time a human officer reacts, funds have vanished from the banking rail.")
        ]),
        ("😰", "Victim Panic & Paralysis", C_PAYTM_CYAN, [
            ("50% of Victims Never Report", "LocalCircles: Half of victims give up due to panic, confusion, and complex portals."),
            ("Impersonation Scam Fears", "Victims fear automated calls asking for OTP/PIN, ignoring urgent bank outreach."),
            ("Genuine User Friction", "Heavy-handed blanket account freezes frustrate and alienate honest customers.")
        ])
    ]

    for idx, (icon, col_title, col_col, items) in enumerate(prob_cols):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s2, cx, Inches(1.6), Inches(3.7), Inches(5.3))
        
        # Icon badge
        add_circle_badge(s2, cx + Inches(0.3), Inches(1.85), Inches(0.55), C_LIGHT_BG, icon, col_col)
        
        tb = s2.shapes.add_textbox(cx + Inches(0.95), Inches(1.9), Inches(2.5), Inches(0.5))
        tf = tb.text_frame
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        p_t = tf.paragraphs[0]
        p_t.text = col_title
        p_t.font.name = FONT_FAMILY
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = C_HEADING_DARK

        # Items
        ib_tb = s2.shapes.add_textbox(cx + Inches(0.3), Inches(2.6), Inches(3.1), Inches(4.1))
        ib_tf = ib_tb.text_frame
        ib_tf.word_wrap = True
        ib_tf.margin_top = ib_tf.margin_left = ib_tf.margin_bottom = ib_tf.margin_right = 0
        for i_idx, (it_title, it_desc) in enumerate(items):
            p_ih = ib_tf.paragraphs[0] if i_idx == 0 else ib_tf.add_paragraph()
            p_ih.text = "• " + it_title
            p_ih.font.name = FONT_FAMILY
            p_ih.font.size = Pt(12)
            p_ih.font.bold = True
            p_ih.font.color.rgb = col_col
            p_ih.space_before = Pt(10 if i_idx > 0 else 0)

            p_id = ib_tf.add_paragraph()
            p_id.text = it_desc
            p_id.font.name = FONT_FAMILY
            p_id.font.size = Pt(11)
            p_id.font.color.rgb = C_BODY_DARK
            p_id.space_before = Pt(2)

    set_notes(s2, """
Let's look at the reality in India today. According to Finance Ministry records, over 13 lakh UPI frauds were recorded in a single year, with ₹1,087 crores lost. In Account Takeovers, fraudsters move stolen money into mule accounts within 5 to 10 minutes.
The Indian government built the CFCFRMS 1930 system to freeze money while in transit, but it relies on rapid, accurate reporting. Today's response is completely manual: alerts wait 15 minutes in queue, analysts take 7 minutes to triage, and manual evidence gathering takes over an hour. Even worse, half of victims panic and never file. By the time human teams react, the Golden Hour is lost.
""")

    # =========================================================================
    # SLIDE 3: PROPOSED SOLUTION (Meet Golden Hour Guardian)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3, C_LIGHT_BG)
    add_header(s3, "Meet Golden Hour Guardian: Autonomous Fraud Teammate", "Proposed Solution")

    # Overview Callout Card (Subtle background tint)
    add_card(s3, Inches(0.8), Inches(1.55), Inches(11.7), Inches(0.8), bg_color=C_CYAN_TINT, border_color=C_PAYTM_CYAN)
    ov_tb = s3.shapes.add_textbox(Inches(1.05), Inches(1.65), Inches(11.2), Inches(0.6))
    ov_tf = ov_tb.text_frame
    ov_tf.word_wrap = True
    ov_tf.margin_top = ov_tf.margin_left = ov_tf.margin_bottom = ov_tf.margin_right = 0
    p_ov = ov_tf.paragraphs[0]
    p_ov.text = "An autonomous AI teammate integrated with Paytm Pi: receives real-time alerts, executes instant reversible containment, verifies victims with zero-secret voice dialogue, and auto-compiles national 1930/NCRP evidence dossiers."
    p_ov.font.name = FONT_FAMILY
    p_ov.font.size = Pt(12)
    p_ov.font.color.rgb = C_HEADING_DARK

    # 4 Teammate Roles
    roles = [
        ("🛡️", "SHIELD", "Instant Containment", C_PAYTM_CYAN, [
            "Places immediate temporary hold on victim's own outgoing payments (auto-expires in 60m).",
            "Revokes active compromised sessions & rogue device tokens in real-time.",
            "Suppresses promotional/cross-sell SMS to prevent victim confusion."
        ]),
        ("🎙️", "VOICE", "Multilingual Dialogue", C_EMERALD, [
            "Proactive verification in English, Hindi, and Telugu on the trusted app.",
            "Zero-Secret Guarantee: Strict guardrails never ask for OTP, PIN, password, or CVV.",
            "Trusted Channel Rule: Validates SIM swap history; ignores swapped SIM lines."
        ]),
        ("📋", "SCRIBE", "Forensic Dossier", C_DEEP_BLUE, [
            "Synthesizes transaction ledger, mule fan-in velocity, and device footprints.",
            "Pre-fills complete 1930 / NCRP cybercrime filing fields.",
            "Generates copyable filing packets so panicked victims file in 2 minutes."
        ]),
        ("⚖️", "DESK", "Officer Co-Pilot", C_HEADING_DARK, [
            "Presents pre-computed Tier-2 dispute recommendations with LLM rationale.",
            "Tracks Golden-Hour countdown SLA timers for the human fraud queue.",
            "One-click dispute dispatch to partner banks upon officer approval."
        ])
    ]

    for idx, (icon, r_name, r_sub, r_col, r_bullets) in enumerate(roles):
        cx = Inches(0.8 + idx * 3.0)
        add_card(s3, cx, Inches(2.55), Inches(2.8), Inches(4.35))
        
        # Badge
        add_circle_badge(s3, cx + Inches(0.2), Inches(2.75), Inches(0.55), C_LIGHT_BG, icon, r_col)
        
        hdr_tb = s3.shapes.add_textbox(cx + Inches(0.85), Inches(2.75), Inches(1.8), Inches(0.6))
        hdr_tf = hdr_tb.text_frame
        hdr_tf.margin_top = hdr_tf.margin_left = hdr_tf.margin_bottom = hdr_tf.margin_right = 0
        p_rn = hdr_tf.paragraphs[0]
        p_rn.text = r_name
        p_rn.font.name = FONT_FAMILY
        p_rn.font.size = Pt(14)
        p_rn.font.bold = True
        p_rn.font.color.rgb = r_col
        p_rs = hdr_tf.add_paragraph()
        p_rs.text = r_sub
        p_rs.font.name = FONT_FAMILY
        p_rs.font.size = Pt(10)
        p_rs.font.color.rgb = C_TEXT_MUTED

        # Bullets
        b_tb = s3.shapes.add_textbox(cx + Inches(0.2), Inches(3.55), Inches(2.4), Inches(3.2))
        b_tf = b_tb.text_frame
        b_tf.word_wrap = True
        b_tf.margin_top = b_tf.margin_left = b_tf.margin_bottom = b_tf.margin_right = 0
        for b_idx, b_text in enumerate(r_bullets):
            p_b = b_tf.paragraphs[0] if b_idx == 0 else b_tf.add_paragraph()
            p_b.text = "✔ " + b_text
            p_b.font.name = FONT_FAMILY
            p_b.font.size = Pt(10.5)
            p_b.font.color.rgb = C_BODY_DARK
            p_b.space_before = Pt(8)

    set_notes(s3, """
Here is how Golden Hour Guardian solves this crisis: it is an autonomous AI teammate structured into four logical roles.
Shield immediately executes reversible containment—placing an auto-expiring hold on the victim's own outgoing payments and killing rogue sessions.
Voice reaches out proactively to the victim via their trusted app in English, Hindi, or Telugu. It never asks for OTPs or secrets.
Scribe automatically gathers the ledger, mule fan-in data, and pre-fills the national 1930 cybercrime complaint.
And Desk acts as the fraud officer's co-pilot, presenting pre-computed Tier-2 dispute recommendations with SLA countdown timers.
""")

    # =========================================================================
    # SLIDE 4: ARCHITECTURE & POLICY TIERS (Zero Governance Drift)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4, C_LIGHT_BG)
    add_header(s4, "Autonomous Execution with Zero Governance Drift", "Architecture & Policy Tiers")

    # Left: Process Flow Card
    add_card(s4, Inches(0.8), Inches(1.55), Inches(5.6), Inches(5.35))
    w_tb = s4.shapes.add_textbox(Inches(1.05), Inches(1.75), Inches(5.1), Inches(4.9))
    w_tf = w_tb.text_frame
    w_tf.word_wrap = True
    w_tf.margin_top = w_tf.margin_left = w_tf.margin_bottom = w_tf.margin_right = 0
    p_wh = w_tf.paragraphs[0]
    p_wh.text = "🔄 Autonomous End-to-End Workflow"
    p_wh.font.name = FONT_FAMILY
    p_wh.font.size = Pt(15)
    p_wh.font.bold = True
    p_wh.font.color.rgb = C_HEADING_DARK

    steps = [
        ("1. Real-Time Ingestion (Paytm Pi Webhook)", "Receives high-risk alert (score >= 0.85, new device, velocity spikes)."),
        ("2. Autonomous Tier-1 Containment (0 - 5s)", "Instantly places temporary hold on outgoing payments & revokes rogue session."),
        ("3. Trusted-Channel Verification (5 - 30s)", "Proactive in-app voice prompt. If SIM swap in 72h, registered number is untrusted."),
        ("4. Scribe Evidence Assembly (Parallel)", "Synthesizes money trail graph, mule velocity & pre-fills 1930 / NCRP form."),
        ("5. Officer Desk Dispatch & Approval", "Officer reviews dossier with 1-click partner dispute action & audit chain check.")
    ]
    for s_title, s_desc in steps:
        p_st = w_tf.add_paragraph()
        p_st.text = s_title
        p_st.font.name = FONT_FAMILY
        p_st.font.size = Pt(11.5)
        p_st.font.bold = True
        p_st.font.color.rgb = C_PAYTM_CYAN
        p_st.space_before = Pt(8)
        p_sd = w_tf.add_paragraph()
        p_sd.text = s_desc
        p_sd.font.name = FONT_FAMILY
        p_sd.font.size = Pt(10.5)
        p_sd.font.color.rgb = C_BODY_DARK
        p_sd.space_before = Pt(1)

    # Right: 3-Tier Policy Table (Color-tinted cards for clear contrast)
    add_card(s4, Inches(6.8), Inches(1.55), Inches(5.7), Inches(5.35))
    p_tb = s4.shapes.add_textbox(Inches(7.05), Inches(1.75), Inches(5.2), Inches(0.5))
    p_tf = p_tb.text_frame
    p_tf.margin_top = p_tf.margin_left = p_tf.margin_bottom = p_tf.margin_right = 0
    p_ph = p_tf.paragraphs[0]
    p_ph.text = "🛡️ Hardcoded 3-Tier Action Policy (RBI Aligned)"
    p_ph.font.name = FONT_FAMILY
    p_ph.font.size = Pt(15)
    p_ph.font.bold = True
    p_ph.font.color.rgb = C_HEADING_DARK

    tier_cards = [
        ("TIER 1 — AGENT ACTS ALONE", C_EMERALD, C_EMERALD_TINT,
         "• Reversible hold on victim's OWN outgoing UPI (auto-expires in 60m)\n• Revoke suspicious session token & device access\n• In-app voice verification; pre-fill 1930 complaint; suppress marketing"),
        ("TIER 2 — AGENT PREPARES, HUMAN APPROVES", C_AMBER, C_AMBER_TINT,
         "• Raise formal dispute via partner bank channel\n• Extend hold beyond 120 minutes\n• Release hold after recent SIM swap (untrusted channel)\n• Liability & shadow-credit refund determinations"),
        ("TIER 3 — IMPOSSIBLE IN CODE (Hard Blocked)", C_ROSE, C_ROSE_TINT,
         "• NEVER freezes 3rd-party/beneficiary accounts (Police jurisdiction)\n• NEVER files police complaints on victim's behalf (Victim must file)\n• NEVER asks for OTP, PIN, password, or CVV\n• NEVER guarantees refunds or promises legal outcomes")
    ]

    for idx, (t_name, t_col, t_tint, t_text) in enumerate(tier_cards):
        ty = Inches(2.35 + idx * 1.45)
        add_card(s4, Inches(7.0), ty, Inches(5.3), Inches(1.35), bg_color=t_tint, border_color=t_col)
        
        tb_t = s4.shapes.add_textbox(Inches(7.15), ty + Inches(0.1), Inches(5.0), Inches(1.15))
        tf_t = tb_t.text_frame
        tf_t.word_wrap = True
        tf_t.margin_top = tf_t.margin_left = tf_t.margin_bottom = tf_t.margin_right = 0
        p1 = tf_t.paragraphs[0]
        p1.text = t_name
        p1.font.name = FONT_FAMILY
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = t_col

        p2 = tf_t.add_paragraph()
        p2.text = t_text
        p2.font.name = FONT_FAMILY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = C_HEADING_DARK
        p2.space_before = Pt(3)

    set_notes(s4, """
In banking, autonomous AI must be safe and governed. We enforce a hardcoded 3-Tier Action Policy in code:
Tier 1 gives the AI autonomy over reversible, victim-side containment actions like temporary holds and session kills.
Tier 2 requires a human fraud officer to approve formal bank disputes, hold extensions, and financial liability decisions.
Tier 3 is physically impossible in code: the agent can never freeze third-party accounts, ask for OTPs, or promise refunds.
This ensures 100% compliance with RBI's customer protection circular and the FREE-AI governance mandate.
""")

    # =========================================================================
    # SLIDE 5: TECHNOLOGY & TECH STACK (Privacy-First Architecture)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5, C_LIGHT_BG)
    add_header(s5, "Robust, Privacy-First Architecture", "Technology & Tech Stack")

    tech_blocks = [
        ("🤖", "Local SLM & Privacy Layer", C_PAYTM_CYAN, [
            ("Ollama Qwen 3 (4B) / Qwen 2.5", "Local small language model for intent classification & risk explanation without cloud latency."),
            ("Zero Data Leakage (Edge AI)", "PII masked prior to model input; no financial data leaves bank servers (DPDP Act 2023 compliant)."),
            ("Fail-Safe Regex Guardrails", "Regex interceptor blocks banned patterns (OTP/PIN/fee); falls back to deterministic templates.")
        ]),
        ("⚡", "High-Throughput Core Engine", C_DEEP_BLUE, [
            ("Python 3.12 & FastAPI", "Asynchronous, event-driven API engine capable of processing thousands of alerts per second."),
            ("Deterministic State Machine", "Rigid FSM (NEW -> HELD -> CONTAINED -> EVIDENCE -> CLOSED) prevents invalid states."),
            ("Server-Sent Events (SSE)", "Real-time streaming bus for officer console alerts and mobile victim app updates.")
        ]),
        ("🎙️", "Multilingual Voice & Mobile PWA", C_EMERALD, [
            ("Web Speech STT & TTS", "Interactive speech synthesis & transcription supporting English, Hindi, and Telugu."),
            ("Mobile-First Victim PWA", "Low-bandwidth Progressive Web App running on Android/iOS with push verification."),
            ("Panic-Optimized UX", "Large high-contrast buttons, audio readouts, and 1-tap copyable 1930 summaries.")
        ]),
        ("🔐", "Tamper-Evident Auditability", C_HEADING_DARK, [
            ("SHA-256 Hash-Chained Log", "Every state change, tool invocation, and human officer decision is cryptographically linked."),
            ("Instant Verification Endpoint", "Built-in /audit/verify endpoint detects any historical tampering or retroactive edits."),
            ("RBI FREE-AI Ready", "Comprehensive audit trails adhering to RBI's August 2025 AI governance framework.")
        ])
    ]

    for idx, (icon, t_title, t_col, t_points) in enumerate(tech_blocks):
        row = idx // 2
        col = idx % 2
        cx = Inches(0.8 + col * 6.0)
        cy = Inches(1.65 + row * 2.7)

        add_card(s5, cx, cy, Inches(5.7), Inches(2.5))
        add_circle_badge(s5, cx + Inches(0.25), cy + Inches(0.2), Inches(0.55), C_LIGHT_BG, icon, t_col)
        
        tb = s5.shapes.add_textbox(cx + Inches(0.95), cy + Inches(0.2), Inches(4.5), Inches(0.5))
        tf = tb.text_frame
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        p_th = tf.paragraphs[0]
        p_th.text = t_title
        p_th.font.name = FONT_FAMILY
        p_th.font.size = Pt(14)
        p_th.font.bold = True
        p_th.font.color.rgb = t_col

        b_tb = s5.shapes.add_textbox(cx + Inches(0.25), cy + Inches(0.85), Inches(5.2), Inches(1.5))
        b_tf = b_tb.text_frame
        b_tf.word_wrap = True
        b_tf.margin_top = b_tf.margin_left = b_tf.margin_bottom = b_tf.margin_right = 0
        for p_idx, (sub, body) in enumerate(t_points):
            p_s = b_tf.paragraphs[0] if p_idx == 0 else b_tf.add_paragraph()
            p_s.text = "• " + sub + ": "
            p_s.font.name = FONT_FAMILY
            p_s.font.size = Pt(10.5)
            p_s.font.bold = True
            p_s.font.color.rgb = C_HEADING_DARK
            p_s.space_before = Pt(4)
            p_b = b_tf.add_paragraph()
            p_b.text = "   " + body
            p_b.font.name = FONT_FAMILY
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = C_BODY_DARK
            p_b.space_before = Pt(1)

    set_notes(s5, """
Our technical stack is built for financial scale and uncompromising privacy.
We run a local Small Language Model—Ollama Qwen—on-premise. All PII is masked before reaching the model, ensuring zero financial data leaves the bank's VPC.
Our backend is Python 3.12 and FastAPI with a deterministic Finite State Machine and SSE event streaming.
Multilingual voice is powered by browser-native Web Speech STT and TTS in Hindi, Telugu, and English.
And every single action is written to an immutable SHA-256 cryptographic hash chain, fulfilling RBI's FREE-AI auditability mandate.
""")

    # =========================================================================
    # SLIDE 6: USP (Unique Selling Proposition)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6, C_LIGHT_BG)
    add_header(s6, "Why Golden Hour Guardian Outperforms", "Unique Selling Proposition (USP)")

    usps = [
        ("⚡", "True Autonomy, Not Just Q&A", "While conventional chatbots provide static FAQ links while money drains, Guardian executes autonomous Tier-1 containment (session kill, payment hold) in milliseconds."),
        ("🛡️", "SIM-Swap Aware Trust Rail", "Contextual awareness detects if a SIM was changed in the last 72 hours (SIM_CHANGE_72H). If swapped, phone verification is marked untrusted, defeating OTP and call hijacking."),
        ("🔒", "100% Local DPDP Compliance", "Runs on local Small Language Models (SLMs) with masked PII. Zero financial data or customer identity is sent to external cloud APIs, satisfying strict Indian banking regulations."),
        ("🤝", "Symbiotic Human-AI Teammate", "Automates 95% of manual evidence gathering and triage, delivering a single-click dispute dossier with SLA countdown timers to human fraud officers."),
        ("📋", "National 1930 / CFCFRMS Bridge", "Transforms panicked victims into effective reporters by auto-generating correctly formatted NCRP complaint fields and capturing national acknowledgement numbers.")
    ]

    for idx, (icon, title, desc) in enumerate(usps):
        cy = Inches(1.6 + idx * 1.08)
        add_card(s6, Inches(0.8), cy, Inches(11.7), Inches(0.95))
        
        # Circle badge
        add_circle_badge(s6, Inches(1.05), cy + Inches(0.18), Inches(0.6), C_LIGHT_BG, icon, C_PAYTM_CYAN)

        # Content
        ctb = s6.shapes.add_textbox(Inches(1.85), cy + Inches(0.12), Inches(10.4), Inches(0.75))
        ctf = ctb.text_frame
        ctf.word_wrap = True
        ctf.margin_top = ctf.margin_left = ctf.margin_bottom = ctf.margin_right = 0
        p_ut = ctf.paragraphs[0]
        p_ut.text = title
        p_ut.font.name = FONT_FAMILY
        p_ut.font.size = Pt(13)
        p_ut.font.bold = True
        p_ut.font.color.rgb = C_HEADING_DARK

        p_ud = ctf.add_paragraph()
        p_ud.text = desc
        p_ud.font.name = FONT_FAMILY
        p_ud.font.size = Pt(10.5)
        p_ud.font.color.rgb = C_BODY_DARK
        p_ud.space_before = Pt(2)

    set_notes(s6, """
What sets Golden Hour Guardian apart?
First, real autonomy: it doesn't just chat, it acts.
Second, SIM-swap intelligence: if a fraudster swapped the victim's SIM, calling the registered number is useless. Guardian recognizes this and verifies via the trusted app instead.
Third, local edge AI: 100% compliant with the DPDP Act.
Fourth, symbiotic collaboration: it prepares the evidence and lets the human officer approve partner bank disputes with one click.
And fifth, it turns panicked victims into empowered reporters by pre-filling national 1930 cybercrime complaints.
""")

    # =========================================================================
    # SLIDE 7: IMPACT & BENEFITS (Measurable Outcomes)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_bg(s7, C_LIGHT_BG)
    add_header(s7, "Measurable Outcomes for Victims, Officers & Banks", "Impact & Benefits")

    # Top KPI Cards (Massive numbers, clear comparison chips)
    kpis = [
        ("T_protect (Containment)", "35 mins", "< 60s", "> 97% Faster", C_EMERALD, C_EMERALD_TINT),
        ("T_ready (Evidence Dossier)", "65 mins", "< 5m", "> 92% Faster", C_PAYTM_CYAN, C_CYAN_TINT),
        ("Genuine User Friction", "Hours of hold", "< 20s", "Instant Release", C_DEEP_BLUE, C_LIGHT_BG),
        ("Officer Case Capacity", "1x Manual queue", "8x - 10x", "Scale Multiplier", C_AMBER, C_AMBER_TINT)
    ]

    for idx, (label, before, after, gain, col, tint) in enumerate(kpis):
        cx = Inches(0.8 + idx * 3.0)
        add_card(s7, cx, Inches(1.6), Inches(2.8), Inches(1.9), bg_color=tint, border_color=col)
        
        tb = s7.shapes.add_textbox(cx + Inches(0.15), Inches(1.75), Inches(2.5), Inches(1.6))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        p_lbl = tf.paragraphs[0]
        p_lbl.text = label
        p_lbl.font.name = FONT_FAMILY
        p_lbl.font.size = Pt(11)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = C_HEADING_DARK

        p_aft = tf.add_paragraph()
        p_aft.text = after
        p_aft.font.name = FONT_FAMILY
        p_aft.font.size = Pt(28)
        p_aft.font.bold = True
        p_aft.font.color.rgb = col
        p_aft.space_before = Pt(4)

        p_bef = tf.add_paragraph()
        p_bef.text = f"Baseline: {before}  ({gain})"
        p_bef.font.name = FONT_FAMILY
        p_bef.font.size = Pt(9.5)
        p_bef.font.color.rgb = C_TEXT_MUTED
        p_bef.space_before = Pt(2)

    # Bottom 3 Detailed Outcome Columns
    outcomes = [
        ("🛡️", "Capital Preservation", [
            "Intercepts stolen funds while still in the banking network before mule cash-outs.",
            "CFCFRMS 2.0 has saved ₹11,158 Cr nationwide — Guardian maximizes this window by ensuring complete filings in < 5 minutes instead of hours."
        ]),
        ("👥", "Panic Mitigation & Inclusivity", [
            "Converts sheer panic into structured, guided action via vernacular voice assistance (Hindi, Telugu, English).",
            "Eliminates fear of phone scams: in-app verified interaction never asks for sensitive financial secrets."
        ]),
        ("🏛️", "Zero-Audit Liability (RBI & DPDP)", [
            "SHA-256 immutable audit chain provides complete transparency for regulatory investigations.",
            "Ensures full compliance with RBI's customer protection circular (zero customer liability on rapid reporting)."
        ])
    ]

    for idx, (icon, title, points) in enumerate(outcomes):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s7, cx, Inches(3.75), Inches(3.7), Inches(3.15))
        add_circle_badge(s7, cx + Inches(0.25), Inches(3.95), Inches(0.55), C_LIGHT_BG, icon, C_PAYTM_CYAN)

        tb = s7.shapes.add_textbox(cx + Inches(0.95), Inches(4.0), Inches(2.5), Inches(0.5))
        tf = tb.text_frame
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_FAMILY
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = C_HEADING_DARK

        b_tb = s7.shapes.add_textbox(cx + Inches(0.25), Inches(4.65), Inches(3.2), Inches(2.1))
        b_tf = b_tb.text_frame
        b_tf.word_wrap = True
        b_tf.margin_top = b_tf.margin_left = b_tf.margin_bottom = b_tf.margin_right = 0
        for pt in points:
            p_p = b_tf.paragraphs[0] if pt == points[0] else b_tf.add_paragraph()
            p_p.text = "• " + pt
            p_p.font.name = FONT_FAMILY
            p_p.font.size = Pt(10)
            p_p.font.color.rgb = C_BODY_DARK
            p_p.space_before = Pt(6)

    set_notes(s7, """
The outcomes are quantifiable and transformative.
Containment time drops from a manual baseline of 35 minutes to under 60 seconds—a 97% reduction in exposure.
Evidence readiness drops from 65 minutes to under 5 minutes.
Honest customers face near-zero friction: legitimate transactions are released in under 20 seconds.
And human fraud officers experience an 8x to 10x throughput multiplier, meaning teams can handle severe transaction spikes during festive sales without expanding headcount.
""")

    # =========================================================================
    # SLIDE 8: BUSINESS MODEL & ECOSYSTEM FIT (Commercial Strategy)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_bg(s8, C_LIGHT_BG)
    add_header(s8, "Commercial Strategy & Value Realization", "Business Model & Paytm Ecosystem Fit")

    bm_cards = [
        ("🎯", "Ecosystem Fit: Paytm Pi Add-On", C_PAYTM_CYAN, [
            ("Complementary to Paytm Pi", "Paytm Pi detects fraudulent risk patterns; Guardian provides the automated execution teammate to act on those detections instantly."),
            ("Target Buyers", "Payment Aggregators (Paytm, Razorpay), Sponsor Banks (PPBL, Axis, HDFC), Digital Wallets & NBFCs."),
            ("Fills the Response Vacuum", "While MuleHunter.AI and I4C flag suspect accounts, banks lack rapid automated orchestration to protect victim accounts.")
        ]),
        ("💰", "Monetization Streams", C_EMERALD, [
            ("Tiered Enterprise SaaS", "Monthly subscription fee per active monitored user / per fraud alert volume processed."),
            ("Value-Share Recovery Model", "Contingency success fee (2-5%) on verified fraudulent funds preserved or reclaimed via CFCFRMS."),
            ("Partner Integration License", "Custom on-premise deployment and core-banking dispute pipeline integration.")
        ]),
        ("📈", "ROI & Unit Economics", C_DEEP_BLUE, [
            ("Tenfold Cost Offset", "Preventing just 10 account takeovers per month (avg loss ₹50,000) saves ₹5,00,000/month in direct liability."),
            ("Labor Cost Compression", "Automates repetitive triage and evidence compilation, slashing fraud-ops operational overhead by 70%."),
            ("Customer Retention Dividend", "Prevents user churn and brand damage caused by unassisted fraud trauma.")
        ])
    ]

    for idx, (icon, title, col, items) in enumerate(bm_cards):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s8, cx, Inches(1.6), Inches(3.7), Inches(5.3))
        add_circle_badge(s8, cx + Inches(0.25), Inches(1.85), Inches(0.55), C_LIGHT_BG, icon, col)

        tb = s8.shapes.add_textbox(cx + Inches(0.95), Inches(1.9), Inches(2.5), Inches(0.5))
        tf = tb.text_frame
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        p_hd = tf.paragraphs[0]
        p_hd.text = title
        p_hd.font.name = FONT_FAMILY
        p_hd.font.size = Pt(13)
        p_hd.font.bold = True
        p_hd.font.color.rgb = C_HEADING_DARK

        ib_tb = s8.shapes.add_textbox(cx + Inches(0.25), Inches(2.6), Inches(3.2), Inches(4.1))
        ib_tf = ib_tb.text_frame
        ib_tf.word_wrap = True
        ib_tf.margin_top = ib_tf.margin_left = ib_tf.margin_bottom = ib_tf.margin_right = 0
        for it_idx, (it_h, it_b) in enumerate(items):
            p_ih = ib_tf.paragraphs[0] if it_idx == 0 else ib_tf.add_paragraph()
            p_ih.text = "• " + it_h
            p_ih.font.name = FONT_FAMILY
            p_ih.font.size = Pt(11)
            p_ih.font.bold = True
            p_ih.font.color.rgb = col
            p_ih.space_before = Pt(8 if it_idx > 0 else 0)

            p_ib = ib_tf.add_paragraph()
            p_ib.text = it_b
            p_ib.font.name = FONT_FAMILY
            p_ib.font.size = Pt(10)
            p_ib.font.color.rgb = C_BODY_DARK
            p_ib.space_before = Pt(1)

    set_notes(s8, """
Our business model is an ideal expansion for Paytm.
Paytm Pi is sold to banks and fintechs for fraud detection. Golden Hour Guardian is the natural 'Autonomous Response Teammate' module on top of Pi.
We monetize through enterprise B2B SaaS licensing and a value-share model on preserved funds.
The unit economics are compelling: if a partner bank prevents just 10 account takeovers a month, the platform pays for itself tenfold while slashing manual fraud-ops overhead by 70%.
""")

    # =========================================================================
    # SLIDE 9: DEMO SCENARIOS & RESILIENCY (Battle-Tested 229 Tests)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_bg(s9, C_LIGHT_BG)
    add_header(s9, "Battle-Tested Scenarios (229 Automated Tests)", "Demonstration & Verification")

    scenarios = [
        ("🚨", "Scenario: 'ato' (Account Takeover)", C_ROSE, C_ROSE_TINT,
         "New device in distant city + SIM swapped 2h ago + rapid transfers to mule fan-in payee.",
         "Score 0.93 -> Instant Tier-1 outgoing hold -> Voice verification on trusted device -> Victim confirms NOT ME -> Contained in 48s -> Scribe builds evidence -> Officer approves dispute."),
        ("✔", "Scenario: 'genuine' (Low Friction)", C_EMERALD, C_EMERALD_TINT,
         "Legitimate user making high-value festive purchase at a new merchant.",
         "Score 0.55 -> Prompted via trusted in-app voice -> Victim taps 'Yes, it was me' -> Outgoing hold released in < 20s. Zero manual analyst intervention required."),
        ("🛡️", "Scenario: 'injection' (Red Team Attack)", C_DEEP_BLUE, C_CYAN_TINT,
         "Adversary attempts prompt injection to trick LLM into promising refund or bypassing policy.",
         "Regex guardrail & FSM intercept malicious syntax -> Blocked by Policy Engine -> Emits POLICY_BLOCKED event -> Dispatches officer callback."),
        ("⚙️", "Scenario: 'fallback' (Zero-Downtime)", C_HEADING_DARK, C_LIGHT_BG,
         "Local Ollama SLM offline or response latency exceeds timeout threshold.",
         "Engine automatically switches to deterministic fallback templates -> Zero service disruption -> Emits LLM_FALLBACK_USED audit event.")
    ]

    for idx, (icon, s_title, s_col, s_tint, s_story, s_res) in enumerate(scenarios):
        row = idx // 2
        col = idx % 2
        cx = Inches(0.8 + col * 6.0)
        cy = Inches(1.65 + row * 2.7)

        add_card(s9, cx, cy, Inches(5.7), Inches(2.5), bg_color=s_tint, border_color=s_col)
        add_circle_badge(s9, cx + Inches(0.25), cy + Inches(0.2), Inches(0.55), C_WHITE, icon, s_col)

        tb = s9.shapes.add_textbox(cx + Inches(0.95), cy + Inches(0.2), Inches(4.5), Inches(0.5))
        tf = tb.text_frame
        tf.margin_top = tf.margin_left = tf.margin_bottom = tf.margin_right = 0
        p_th = tf.paragraphs[0]
        p_th.text = s_title
        p_th.font.name = FONT_FAMILY
        p_th.font.size = Pt(13)
        p_th.font.bold = True
        p_th.font.color.rgb = s_col

        b_tb = s9.shapes.add_textbox(cx + Inches(0.25), cy + Inches(0.85), Inches(5.2), Inches(1.5))
        b_tf = b_tb.text_frame
        b_tf.word_wrap = True
        b_tf.margin_top = b_tf.margin_left = b_tf.margin_bottom = b_tf.margin_right = 0
        
        p_st = b_tf.paragraphs[0]
        p_st.text = "Setup: " + s_story
        p_st.font.name = FONT_FAMILY
        p_st.font.size = Pt(10)
        p_st.font.bold = True
        p_st.font.color.rgb = C_HEADING_DARK

        p_re = b_tf.add_paragraph()
        p_re.text = "Outcome: " + s_res
        p_re.font.name = FONT_FAMILY
        p_re.font.size = Pt(9.5)
        p_re.font.color.rgb = C_BODY_DARK
        p_re.space_before = Pt(3)

    set_notes(s9, """
Our system is live and verified with 229 automated tests.
In our demo, we showcase four critical scenarios:
First, an Account Takeover where funds are contained in 48 seconds, evidence is packaged, and the human officer approves the dispute.
Second, a genuine high-value purchase verified and released in 20 seconds.
Third, a red-team adversarial injection attack that is intercepted and blocked by our policy guardrails.
And fourth, zero-downtime resiliency: even if the local LLM goes offline, the system continues running flawlessly on deterministic templates.
""")

    # =========================================================================
    # SLIDE 10: CONCLUSION & VISION (Dark Theme Hero)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_bg(s10, C_DARK_BG)

    # Category Pill
    c10_pill = add_card(s10, Inches(0.8), Inches(1.1), Inches(3.2), Inches(0.4), bg_color=C_DARK_CARD, border_color=C_PAYTM_CYAN)
    p10_tb = s10.shapes.add_textbox(Inches(0.9), Inches(1.12), Inches(3.0), Inches(0.35))
    p10_tf = p10_tb.text_frame
    p10_tf.margin_top = p10_tf.margin_left = p10_tf.margin_bottom = p10_tf.margin_right = 0
    p10_p = p10_tf.paragraphs[0]
    p10_p.text = "CONCLUSION & STRATEGIC VISION"
    p10_p.font.name = FONT_FAMILY
    p10_p.font.size = Pt(11)
    p10_p.font.bold = True
    p10_p.font.color.rgb = C_PAYTM_CYAN

    # Main Title
    c10_title = s10.shapes.add_textbox(Inches(0.8), Inches(1.65), Inches(11.7), Inches(0.9))
    tf10_t = c10_title.text_frame
    tf10_t.word_wrap = True
    tf10_t.margin_top = tf10_t.margin_left = tf10_t.margin_bottom = tf10_t.margin_right = 0
    p10_t = tf10_t.paragraphs[0]
    p10_t.text = "Winning the Golden Hour in Digital Payments"
    p10_t.font.name = FONT_FAMILY
    p10_t.font.size = Pt(36)
    p10_t.font.bold = True
    p10_t.font.color.rgb = C_WHITE

    # 3 Summary Pillar Cards
    summary_cards = [
        ("⚡", "Action Over Passive Chat", "Traditional AI answers questions while fraud spreads. Guardian acts: executes holds, revokes sessions, and protects the victim in under 60 seconds."),
        ("🛡️", "Strict Policy Governance", "Enforces a 3-tier action policy in code. Zero hallucinations, zero secret leakage, and 100% auditable via cryptographic SHA-256 hash chains."),
        ("🇮🇳", "Ready for Paytm & India", "Seamlessly integrates as the autonomous execution teammate on top of Paytm Pi, scaling trust and safety across 350M+ digital payment users.")
    ]
    for idx, (icon, head, desc) in enumerate(summary_cards):
        cx = Inches(0.8 + idx * 4.0)
        add_card(s10, cx, Inches(2.8), Inches(3.7), Inches(2.3), bg_color=C_DARK_CARD, border_color=C_DARK_BORDER)
        add_circle_badge(s10, cx + Inches(0.25), Inches(3.05), Inches(0.55), RGBColor(15, 33, 64), icon, C_PAYTM_CYAN)

        c_tb = s10.shapes.add_textbox(cx + Inches(0.95), Inches(3.05), Inches(2.5), Inches(0.5))
        c_tf = c_tb.text_frame
        c_tf.margin_top = c_tf.margin_left = c_tf.margin_bottom = c_tf.margin_right = 0
        p1 = c_tf.paragraphs[0]
        p1.text = head
        p1.font.name = FONT_FAMILY
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = C_WHITE

        b_tb = s10.shapes.add_textbox(cx + Inches(0.25), Inches(3.75), Inches(3.2), Inches(1.2))
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
    callout = add_card(s10, Inches(0.8), Inches(5.4), Inches(11.7), Inches(1.3), bg_color=RGBColor(15, 33, 64), border_color=C_PAYTM_CYAN)
    co_tb = s10.shapes.add_textbox(Inches(1.0), Inches(5.55), Inches(11.3), Inches(1.0))
    co_tf = co_tb.text_frame
    co_tf.word_wrap = True
    co_tf.margin_top = co_tf.margin_left = co_tf.margin_bottom = co_tf.margin_right = 0
    p_co = co_tf.paragraphs[0]
    p_co.text = "“In cyber-fraud, time is the attacker's weapon. Golden Hour Guardian makes time our shield.”"
    p_co.font.name = FONT_FAMILY
    p_co.font.size = Pt(16)
    p_co.font.bold = True
    p_co.font.color.rgb = C_WHITE
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
    print(f"Professional presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    build_presentation()
