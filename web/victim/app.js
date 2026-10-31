/* Guardian victim app: vanilla JS, no deps.
   Talks only to this server. Links: tel:1930 and https://cybercrime.gov.in only. */
(function () {
  "use strict";

  const params = new URLSearchParams(location.search);
  const USER = params.get("user") || "usr_meena";
  // Device id (set by scripts/android.sh). The server, not this app, decides whether it is trusted.
  const DEVICE = params.get("device") || "";
  const apiParam = params.get("api");
  const storedApi = typeof localStorage !== "undefined" ? localStorage.getItem("guardian_api_base") : "";
  const rawBase = apiParam || window.GUARDIAN_API_BASE || storedApi || "";
  const API = rawBase ? (rawBase.replace(/\/$/, "") + "/") : "/";
  const BCP47 = { en: "en-IN", hi: "hi-IN" };
  const MIN_PROTECTED_MS = 5000;   // keep "protected" visible before the guidance replaces it

  // ---------- strings ----------
  const T = {
    en: {
      proto: "PROTOTYPE — SIMULATED DATA",
      safety: "Guardian will never ask for your OTP, PIN or password.",
      setupTitle: "Security alerts", unlock: "Tap to enable security alerts",
      setupHint: "This lets Guardian speak to you and vibrate when it needs a quick check.",
      homeTitle: "Your account is monitored", langLabel: "Language", statusLabel: "Last status",
      noAlerts: "No alerts so far.",
      checkTitle: "Security check", yes: "Yes, I made it", no: "No, it wasn't me", unsure: "Not sure",
      mic: "Speak your answer", listening: "Listening…", replay: "Hear again",
      micDenied: "Microphone not allowed. Please tap a button.", micNone: "Could not hear you. Please try again or tap a button.",
      noVoice: "Voice not available for this language. Please read the text.",
      waiting: "Thank you. Checking…",
      protectedTitle: "Your account is now secured",
      acts: {
        outgoing_payments_paused: "Your outgoing payments are paused for now.",
        device_signed_out: "The suspicious phone has been signed out.",
        marketing_held: "Promotional messages are on hold.",
      },
      reportTitle: "Report it now", steps: "Steps", summary: "Summary to copy", copy: "Copy", copied: "Copied",
      fields: "Details for the portal", call: "Call 1930", portal: "Open cybercrime.gov.in",
      ackLabel: "Acknowledgement number from the portal", submit: "Submit",
      ackBad: "Please check the number and try again.",
      releasedTitle: "All clear", doneTitle: "Done",
      offline: "Could not reach Guardian. Retrying…",
      voiceWord: "Voice",
    },
    hi: {
      proto: "PROTOTYPE — SIMULATED DATA",
      safety: "Guardian आपसे कभी आपका OTP, PIN या पासवर्ड नहीं मांगेगा।",
      setupTitle: "सुरक्षा अलर्ट", unlock: "सुरक्षा अलर्ट चालू करने के लिए टैप करें",
      setupHint: "इससे Guardian ज़रूरत पड़ने पर आपसे बोल सकेगा और फोन वाइब्रेट करेगा।",
      homeTitle: "आपके खाते की निगरानी की जा रही है", langLabel: "भाषा", statusLabel: "आखिरी स्थिति",
      noAlerts: "अभी तक कोई अलर्ट नहीं।",
      checkTitle: "सुरक्षा जांच", yes: "हां, मैंने किया", no: "नहीं, यह मैं नहीं था", unsure: "पक्का नहीं",
      mic: "बोलकर जवाब दें", listening: "सुन रहा हूं…", replay: "फिर से सुनें",
      micDenied: "माइक्रोफोन की अनुमति नहीं है। कृपया बटन दबाएं।", micNone: "आवाज़ सुनाई नहीं दी। फिर कोशिश करें या बटन दबाएं।",
      noVoice: "इस भाषा के लिए आवाज़ उपलब्ध नहीं है। कृपया लिखा हुआ पढ़ें।",
      waiting: "धन्यवाद। जांच हो रही है…",
      protectedTitle: "आपका खाता अब सुरक्षित किया गया",
      acts: {
        outgoing_payments_paused: "आपके आउटगोइंग भुगतान अभी रोके गए हैं।",
        device_signed_out: "संदिग्ध फोन को साइन आउट कर दिया गया है।",
        marketing_held: "प्रचार संदेश रोके गए हैं।",
      },
      reportTitle: "अभी रिपोर्ट करें", steps: "चरण", summary: "कॉपी करने के लिए सारांश", copy: "कॉपी करें", copied: "कॉपी हो गया",
      fields: "पोर्टल के लिए विवरण", call: "1930 पर कॉल करें", portal: "cybercrime.gov.in खोलें",
      ackLabel: "पोर्टल से मिला पावती नंबर", submit: "जमा करें",
      ackBad: "कृपया नंबर जांचकर फिर कोशिश करें।",
      releasedTitle: "सब ठीक है", doneTitle: "पूरा हुआ",
      offline: "Guardian से संपर्क नहीं हो पाया। फिर कोशिश कर रहे हैं…",
      voiceWord: "आवाज़",
    },
  };

  // ---------- state ----------
  const $ = (id) => document.getElementById(id);
  const state = {
    uiLang: "en",
    unlocked: false,
    prompt: null,          // prompt currently on screen
    latest: null,          // latest prompt received (shown after unlock)
    seen: new Set(),       // prompt keys already handled (no re-speak / re-vibrate)
    shownAt: 0,
    deferTimer: null,
    lastStatus: null,      // { text, ts } in memory only
    recog: null,
    listening: false,
    voices: [],
    micOk: true,
    es: null,
  };

  try {
    const saved = localStorage.getItem("guardian_lang");   // only the language preference is persisted
    if (saved && T[saved]) state.uiLang = saved;
  } catch (_) { /* storage may be blocked */ }

  const t = () => T[state.uiLang];
  const key = (p) => [p.case_id, p.variant, p.ts].join("|");

  // ---------- helpers ----------
  function setText(id, s) { const el = $(id); if (el) el.textContent = s; }
  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }
  function el(tag, cls, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function toast(msg, ms) {
    const n = $("toast"); n.textContent = msg; n.hidden = false;
    clearTimeout(toast._t); toast._t = setTimeout(() => { n.hidden = true; }, ms || 2500);
  }
  function fmtAmount(paise) {
    const rupees = Math.floor(Number(paise) / 100), rem = Math.abs(Number(paise) % 100);
    const s = rupees.toLocaleString("en-IN");
    return "₹" + s + (rem ? "." + String(rem).padStart(2, "0") : "");
  }
  function fmtIST(iso) {
    try {
      return new Date(iso).toLocaleString("en-IN", { timeZone: "Asia/Kolkata", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: true }) + " IST";
    } catch (_) { return ""; }
  }
  function showScreen(name) {
    document.querySelectorAll(".screen").forEach((s) => { s.hidden = s.id !== "screen-" + name; });
    window.scrollTo(0, 0);
  }

  // ---------- i18n of static UI ----------
  function applyLang(lang, persist) {
    if (!T[lang]) return;
    state.uiLang = lang;
    if (persist) { try { localStorage.setItem("guardian_lang", lang); } catch (_) {} }
    document.documentElement.lang = lang;
    const s = t();
    setText("proto", s.proto); setText("safety", s.safety);
    setText("setup-title", s.setupTitle); setText("btn-unlock", s.unlock); setText("setup-hint", s.setupHint);
    setText("home-title", s.homeTitle); setText("home-lang-label", s.langLabel); setText("home-status-label", s.statusLabel);
    setText("verify-title", s.checkTitle); setText("ans-yes", s.yes); setText("ans-no", s.no); setText("ans-unsure", s.unsure);
    setText("mic-label", state.listening ? s.listening : s.mic); setText("btn-replay", s.replay);
    setText("waiting-title", s.waiting); setText("protected-title", s.protectedTitle);
    setText("report-title", s.reportTitle); setText("report-steps-label", s.steps); setText("report-summary-label", s.summary);
    setText("btn-copy", s.copy); setText("report-fields-label", s.fields);
    setText("btn-call", s.call); setText("btn-portal", s.portal);
    setText("ack-label", s.ackLabel); setText("ack-submit", s.submit);
    document.querySelectorAll("#lang-picker button").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));
    renderHomeStatus(); renderVoiceStatus();
  }

  function renderHomeStatus() {
    const st = state.lastStatus;
    setText("home-status", st ? st.text : t().noAlerts);
    setText("home-status-time", st && st.ts ? fmtIST(st.ts) : "");
  }

  // ---------- voices / TTS ----------
  function loadVoices() {
    if (!("speechSynthesis" in window)) return;
    state.voices = window.speechSynthesis.getVoices() || [];
    renderVoiceStatus();
  }
  function pickVoice(lang) {
    const want = BCP47[lang].toLowerCase(), base = lang;
    const norm = (v) => (v.lang || "").replace("_", "-").toLowerCase();
    return state.voices.find((v) => norm(v) === want)
        || state.voices.find((v) => norm(v).split("-")[0] === base) || null;
  }
  function renderVoiceStatus() {
    if (!("speechSynthesis" in window)) { setText("voice-status", t().voiceWord + ": —"); return; }
    const parts = ["en", "hi", "te"].map((l) => l + (pickVoice(l) ? " ✓" : " ✗"));
    setText("voice-status", t().voiceWord + ": " + parts.join("  "));
  }
  function stopSpeech() { try { window.speechSynthesis.cancel(); } catch (_) {} }
  // Returns true if speech was started, false if no voice is available (caller shows a text note).
  function speak(lines, lang) {
    if (!state.unlocked || !("speechSynthesis" in window)) return false;
    const voice = pickVoice(lang);
    if (!voice) return false;
    stopSpeech();
    lines.forEach((line) => {
      const u = new SpeechSynthesisUtterance(line);
      u.voice = voice; u.lang = voice.lang || BCP47[lang]; u.rate = 0.95; u.pitch = 1;
      window.speechSynthesis.speak(u);
    });
    return true;
  }
  function vibrate(pattern) { try { if (navigator.vibrate) navigator.vibrate(pattern); } catch (_) {} }

  // ---------- unlock ----------
  function unlock() {
    state.unlocked = true;
    try {
      if ("speechSynthesis" in window) {
        const u = new SpeechSynthesisUtterance(".");   // silent utterance: marks the page as allowed to speak
        u.volume = 0; window.speechSynthesis.speak(u);
      }
    } catch (_) {}
    vibrate(1);
    loadVoices();
    showHomeOrPrompt();
    if (state.latest) { state.seen.delete(key(state.latest)); }
    if (state.latest) present(state.latest, true);
  }

  function showHomeOrPrompt() {
    if (!state.unlocked) { showScreen("setup"); return; }
    if (!state.prompt) showScreen("home");
  }

  // ---------- prompt rendering ----------
  function handlePrompt(p) {
    if (!p || !p.variant) return;
    const k = key(p);
    if (state.seen.has(k) && state.latest && key(state.latest) === k) return;
    state.latest = p;
    if (!state.unlocked) return;   // queued until the user taps unlock
    // Let "protected" stay readable before replacing it with the next screen.
    if (state.prompt && state.prompt.variant === "protected" && p.variant !== "protected") {
      const wait = MIN_PROTECTED_MS - (Date.now() - state.shownAt);
      if (wait > 0) {
        clearTimeout(state.deferTimer);
        state.deferTimer = setTimeout(() => { if (state.latest === p) present(p, false); }, wait);
        return;
      }
    }
    clearTimeout(state.deferTimer);
    present(p, false);
  }

  // English companion lines (server sends messages_en only when the message is not already English).
  function renderEnglish(after, p) {
    document.querySelectorAll(".en-block[data-for='" + after.id + "']").forEach((n) => n.remove());
    const en = Array.isArray(p.messages_en) ? p.messages_en : [];
    if (!en.length || p.lang === "en") return;
    const box = el("div", "en-block");
    box.dataset.for = after.id;
    box.setAttribute("lang", "en");
    box.appendChild(el("div", "en-label", "English"));
    en.forEach((m) => box.appendChild(el("p", null, m)));
    after.insertAdjacentElement("afterend", box);
  }

  function present(p, force) {
    const k = key(p);
    const fresh = force || !state.seen.has(k);
    state.seen.add(k);
    state.prompt = p;
    state.shownAt = Date.now();
    if (p.lang && T[p.lang]) applyLang(p.lang, false);   // screen follows the language of the message
    const lines = Array.isArray(p.messages) ? p.messages : [];
    const sentence = lines[0] || "";
    state.lastStatus = { text: sentence || p.variant, ts: p.ts };
    renderHomeStatus();
    setText("verify-note", ""); setText("ack-error", "");

    switch (p.variant) {
      case "verify":
      case "retry": renderVerify(p, lines, fresh); break;
      case "protected": renderProtected(p, lines, fresh); break;
      case "ncrp_guide": renderReport(p, lines); break;
      case "released": renderClose(p, lines, t().releasedTitle); break;
      case "done": renderClose(p, lines, t().doneTitle); break;
      default: showScreen("home");
    }
  }

  function renderVerify(p, lines, fresh) {
    const box = $("verify-txns"); clear(box);
    (p.txns || []).forEach((x) => {
      const row = el("div", "t-row");
      const left = el("div", "t-main");
      left.appendChild(el("span", "amt", fmtAmount(x.amount_paise)));
      left.appendChild(el("span", "payee", x.payee_vpa || ""));
      row.appendChild(left);
      row.appendChild(el("span", "when", x.ts ? fmtIST(x.ts).replace(/ IST$/, "") : ""));
      box.appendChild(row);
    });
    const L = $("verify-lines"); clear(L);
    lines.forEach((m) => L.appendChild(el("p", null, m)));
    renderEnglish(L, p);
    const answers = p.answers && p.answers.length ? p.answers : ["YES_MINE", "NOT_ME", "UNSURE"];
    $("ans-yes").hidden = !answers.includes("YES_MINE");
    $("ans-no").hidden = !answers.includes("NOT_ME");
    $("ans-unsure").hidden = !answers.includes("UNSURE");
    setButtonsDisabled(false);
    updateMicVisibility();
    showScreen("verify");
    if (fresh) {
      vibrate([300, 150, 300, 150, 600]);
      if (!speak(lines, p.lang || "en") && state.unlocked) setText("verify-note", t().noVoice);
    }
  }

  function renderProtected(p, lines, fresh) {
    const ul = $("protected-list"); clear(ul);
    const shown = lines.length ? lines
      : (p.actions_taken || []).map((a) => t().acts[a]).filter(Boolean);
    shown.forEach((m) => ul.appendChild(el("li", null, m)));
    renderEnglish(ul, p);
    showScreen("protected");
    if (fresh) speak(shown, p.lang || "en");
  }

  function renderReport(p, lines) {
    stopSpeech();
    const ol = $("report-steps"); clear(ol);
    lines.forEach((m) => ol.appendChild(el("li", null, m)));
    renderEnglish(ol, p);
    $("report-summary").value = p.summary || "";
    const dl = $("report-fields"); clear(dl);
    const f = p.ncrp_fields || {};
    const names = Object.keys(f);
    names.forEach((n) => { dl.appendChild(el("dt", null, n)); dl.appendChild(el("dd", null, String(f[n]))); });
    if (p.field_map_label) { dl.appendChild(el("dt", null, "")); dl.appendChild(el("dd", "small muted", p.field_map_label)); }
    $("report-fields-card").hidden = names.length === 0;
    // Links are fixed in the HTML: tel:1930 and https://cybercrime.gov.in only.
    $("ack-input").value = "";
    $("ack-submit").disabled = false;
    showScreen("report");
  }

  function renderClose(p, lines, title) {
    setText("close-title", title);
    const L = $("close-lines"); clear(L);
    lines.forEach((m) => L.appendChild(el("p", null, m)));
    renderEnglish(L, p);
    showScreen("close");
  }

  // ---------- replying ----------
  function setButtonsDisabled(d) {
    ["ans-yes", "ans-no", "ans-unsure"].forEach((id) => { $(id).disabled = d; });
  }

  async function postJSON(path, body) {
    const headers = { "Content-Type": "application/json" };
    if (DEVICE) headers["X-Guardian-Device"] = DEVICE;
    const r = await fetch(API + path, { method: "POST", headers: headers, body: JSON.stringify(body) });
    return r;
  }

  async function respond(extra) {
    const p = state.prompt;
    if (!p || !p.case_id) return;
    stopSpeech(); stopListening();
    setButtonsDisabled(true);
    const body = Object.assign({ case_id: p.case_id, lang: p.lang || state.uiLang, channel: "APP_TRUSTED_DEVICE" }, extra);
    try {
      const r = await postJSON("victim/respond", body);
      if (!r.ok) throw new Error("HTTP " + r.status);
      setText("waiting-title", t().waiting);
      showScreen("waiting");
      // If the server answered before we got here, the next prompt may already be queued.
      setTimeout(fetchPending, 1200);
    } catch (e) {
      setButtonsDisabled(false);
      toast(t().offline);
    }
  }

  // ---------- microphone ----------
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  function updateMicVisibility() {
    $("btn-mic").hidden = !(SR && state.micOk && navigator.onLine !== false);
  }
  function stopListening() {
    state.listening = false;
    $("btn-mic").classList.remove("listening");
    setText("mic-label", t().mic);
    if (state.recog) { try { state.recog.abort(); } catch (_) {} state.recog = null; }
  }
  function startListening() {
    if (!SR || state.listening) return;
    const lang = (state.prompt && state.prompt.lang) || state.uiLang;
    stopSpeech();
    const r = new SR();
    r.lang = BCP47[lang] || "en-IN"; r.interimResults = false; r.maxAlternatives = 1; r.continuous = false;
    let got = false;
    r.onresult = (ev) => {
      const text = ev.results && ev.results[0] && ev.results[0][0] ? ev.results[0][0].transcript.trim() : "";
      if (text) { got = true; respond({ transcript: text.slice(0, 2000) }); }   // sent to server only, never stored locally
    };
    r.onerror = (ev) => {
      if (ev.error === "not-allowed" || ev.error === "service-not-allowed") { state.micOk = false; setText("verify-note", t().micDenied); }
      else if (ev.error === "network") { state.micOk = false; }
      else if (ev.error !== "aborted") { setText("verify-note", t().micNone); }
      updateMicVisibility();
    };
    r.onend = () => {
      const was = state.listening;
      state.listening = false; state.recog = null;
      $("btn-mic").classList.remove("listening"); setText("mic-label", t().mic);
      if (was && !got && state.micOk && !$("verify-note").textContent) setText("verify-note", t().micNone);
    };
    state.recog = r; state.listening = true;
    $("btn-mic").classList.add("listening"); setText("mic-label", t().listening); setText("verify-note", "");
    try { r.start(); } catch (_) { stopListening(); }
  }

  // ---------- NCRP ack and copy ----------
  async function copySummary() {
    const ta = $("report-summary"); const text = ta.value;
    let ok = false;
    try { if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(text); ok = true; } } catch (_) {}
    if (!ok) {
      try { ta.removeAttribute("readonly"); ta.focus(); ta.select(); ta.setSelectionRange(0, text.length); ok = document.execCommand("copy"); }
      catch (_) {} finally { ta.setAttribute("readonly", ""); ta.blur(); }
    }
    if (ok) { toast(t().copied); const b = $("btn-copy"); b.textContent = t().copied; setTimeout(() => { b.textContent = t().copy; }, 1800); }
  }

  async function submitAck(ev) {
    ev.preventDefault();
    const p = state.prompt; if (!p || !p.case_id) return;
    const num = $("ack-input").value.trim();
    setText("ack-error", "");
    if (num.length < 4) { setText("ack-error", t().ackBad); return; }
    $("ack-submit").disabled = true;
    try {
      const r = await postJSON("victim/ncrp-ack", { case_id: p.case_id, ack_number: num });
      if (!r.ok) { setText("ack-error", t().ackBad); $("ack-submit").disabled = false; return; }
      // Server also sends a "done" prompt; show the close screen right away.
      const doneMsg = { case_id: p.case_id, variant: "done", lang: p.lang, messages: [], ts: "local-" + Date.now() };
      state.seen.add(key(doneMsg));
      state.prompt = doneMsg; state.latest = doneMsg;
      renderClose(doneMsg, [], t().doneTitle);
      setTimeout(fetchPending, 1000);
    } catch (e) {
      setText("ack-error", t().offline); $("ack-submit").disabled = false;
    }
  }

  // ---------- server connection ----------
  async function fetchPending() {
    try {
      const r = await fetch(API + "victim/" + encodeURIComponent(USER) + "/pending", { cache: "no-store" });
      if (!r.ok) return;
      const p = await r.json();
      if (!p) return;
      // Ignore the locally shown "done" until the server has something newer for that case.
      if (state.prompt && String(state.prompt.ts).startsWith("local-") && p.case_id === state.prompt.case_id && p.variant !== "done") {
        if (p.variant === "ncrp_guide") return;
      }
      handlePrompt(p);
    } catch (_) { /* offline: SSE reconnect will refetch */ }
  }

  function connect() {
    if (state.es) { try { state.es.close(); } catch (_) {} }
    const es = new EventSource(API + "victim/" + encodeURIComponent(USER) + "/events");
    state.es = es;
    es.onopen = () => { fetchPending(); };
    es.onmessage = (m) => {
      let msg; try { msg = JSON.parse(m.data); } catch (_) { return; }
      if (msg && msg.kind === "victim_prompt" && msg.data) handlePrompt(msg.data);
    };
    es.onerror = () => {
      if (es.readyState === EventSource.CLOSED) setTimeout(connect, 2000);   // browser gave up: reconnect ourselves
    };
  }

  // ---------- wiring ----------
  function init() {
    applyLang(state.uiLang, false);
    showScreen("setup");
    $("btn-unlock").addEventListener("click", unlock);
    document.querySelectorAll("#lang-picker button").forEach((b) => b.addEventListener("click", () => applyLang(b.dataset.lang, true)));
    $("ans-yes").addEventListener("click", () => respond({ answer: "YES_MINE" }));
    $("ans-no").addEventListener("click", () => respond({ answer: "NOT_ME" }));
    $("ans-unsure").addEventListener("click", () => respond({ answer: "UNSURE" }));
    $("btn-mic").addEventListener("click", () => { state.listening ? stopListening() : startListening(); });
    $("btn-replay").addEventListener("click", () => {
      const p = state.prompt; if (!p) return;
      if (!speak(p.messages || [], p.lang || "en")) setText("verify-note", t().noVoice);
    });
    $("btn-copy").addEventListener("click", copySummary);
    $("ack-form").addEventListener("submit", submitAck);

    if ("speechSynthesis" in window) {
      loadVoices();
      window.speechSynthesis.addEventListener ? window.speechSynthesis.addEventListener("voiceschanged", loadVoices)
                                             : (window.speechSynthesis.onvoiceschanged = loadVoices);
    }
    window.addEventListener("online", updateMicVisibility);
    window.addEventListener("offline", updateMicVisibility);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") {
        if (!state.es || state.es.readyState === EventSource.CLOSED) connect();
        fetchPending();
      }
    });

    connect();
    fetchPending();

    if ("serviceWorker" in navigator && window.isSecureContext) {
      navigator.serviceWorker.register("sw.js", { scope: "./" }).catch(() => {});
    }
  }

  init();
})();
