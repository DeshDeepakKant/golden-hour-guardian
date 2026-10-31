/* Guardian officer console. Vanilla JS, no dependencies. Displays server values; computes no metrics. */
(function () {
  'use strict';

  // ---------- state ----------
  var cases = new Map();        // case_id -> Case
  var decisions = new Map();    // decision_id -> Decision (pending + known resolved)
  var names = new Map();        // case_id -> masked victim name (from queue/evidence)
  var endAt = new Map();        // case_id -> ms epoch when a non-closed terminal state was first seen
  var selectedId = null;
  var detail = null;            // {case, events, decisions, evidence}
  var detailSeq = 0;
  var serverOffsetMs = 0;       // server time minus local time
  var MAX_EVENTS = 200;
  var TEN_MIN_S = 600;
  var TERMINAL = { CLOSED: 1, RELEASED: 1, DISMISSED: 1, CONFIRMED_GENUINE: 1 };

  var $ = function (id) { return document.getElementById(id); };

  // ---------- helpers ----------
  function clean(s) {
    // Show exactly what the server/log holds; never rewrite wording (REVIEW S5).
    return String(s == null ? '' : s);
  }
  // Surface (not hide) banned outcome wording that slipped past the server-side guard.
  var GUARD_MISS = /\bfrozen\b|\bguarantee|will be (refunded|returned|reversed|recovered)/i;
  function guardMiss(s) {
    return GUARD_MISS.test(String(s || '')) ? h('span', { class: 'badge b-red', title: 'Banned wording in AI text', text: 'guard miss' }) : null;
  }
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'class') el.className = attrs[k];
      else if (k === 'text') el.textContent = clean(attrs[k]);
      else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== false && attrs[k] != null) el.setAttribute(k, attrs[k]);
    }
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c == null || c === false) continue;
      el.appendChild(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(clean(c)) : c);
    }
    return el;
  }
  function svg(tag, attrs, text) {
    var el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    if (text != null) el.textContent = clean(text);
    return el;
  }
  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }
  function parseTs(s) {
    if (!s) return NaN;
    var t = String(s);
    if (!/(Z|[+-]\d\d:?\d\d)$/.test(t)) t += 'Z';
    return Date.parse(t);
  }
  function nowMs() { return Date.now() + serverOffsetMs; }
  var istTime = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  var istFull = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  function fmtTime(s) { var t = parseTs(s); return isNaN(t) ? '—' : istTime.format(new Date(t)); }
  function fmtFull(s) { var t = parseTs(s); return isNaN(t) ? '—' : istFull.format(new Date(t)) + ' IST'; }
  function inr(paise) {
    if (paise == null) return '—';
    var r = paise / 100;
    return '₹' + r.toLocaleString('en-IN', { maximumFractionDigits: 2 });
  }
  function mmss(sec) {
    sec = Math.max(0, Math.floor(sec));
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }
  function fmtDur(s) {
    if (s == null) return '—';
    if (s < 120) return (Math.round(s * 10) / 10) + ' s';
    return mmss(s);
  }
  function maskUser(id) {
    if (!id) return '—';
    var m = /^([a-z]+_)(.+)$/.exec(id);
    if (!m) return id.slice(0, 1) + '***';
    return m[1] + m[2].slice(0, 1) + '***';
  }
  function pretty(s) { return clean(String(s || '').toLowerCase().replace(/_/g, ' ')); }
  function api(path, opts) {
    return fetch(path, opts).then(function (r) {
      var d = r.headers.get('Date');
      if (d) { var t = Date.parse(d); if (!isNaN(t)) serverOffsetMs = t + 500 - Date.now(); }
      if (!r.ok) {
        return r.text().then(function (txt) {
          var e = new Error(r.status + ' ' + txt.slice(0, 160)); e.status = r.status; throw e;
        });
      }
      return r.json();
    });
  }
  function debounce(fn, ms) {
    var t = null;
    return function () { if (t) clearTimeout(t); t = setTimeout(function () { t = null; fn(); }, ms); };
  }

  var ACTION_LABELS = {
    raise_dispute: 'Raise dispute with bank',
    extend_hold: 'Extend temporary hold',
    release_hold_untrusted: 'Release hold (untrusted channel)',
    share_evidence_with_bank: 'Share evidence with bank',
    refund_or_credit: 'Refund / credit decision',
    restore_access: 'Restore access',
    flag_payee_internal: 'Flag payee internally',
    officer_callback: 'Officer calls the customer'
  };
  function actionLabel(a) { return ACTION_LABELS[a] || pretty(a); }

  var STATE_CLASS = {
    NEW: 'b-grey', TRIAGED: 'b-blue', DISMISSED: 'b-grey', HELD_PENDING_VERIFY: 'b-amber', VERIFYING: 'b-amber',
    CONFIRMED_GENUINE: 'b-green', RELEASED: 'b-green', CONFIRMED_FRAUD: 'b-red', CONTAINED: 'b-blue',
    EVIDENCE_READY: 'b-blue', AWAITING_OFFICER: 'b-amber', NO_RESPONSE_ESCALATED: 'b-red', CLOSED: 'b-green'
  };
  function stateBadge(state) { return h('span', { class: 'badge ' + (STATE_CLASS[state] || 'b-grey'), text: pretty(state) }); }

  function originIcon(origin) {
    var s = svg('svg', { class: 'origin', viewBox: '0 0 24 24', 'aria-hidden': 'true' });
    var p = svg('path', {
      fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linejoin': 'round', 'stroke-linecap': 'round',
      d: origin === 'victim_report' ? 'M4 5h16v11H9l-5 4V5Z' : 'M6 17V11a6 6 0 0 1 12 0v6l2 2H4l2-2ZM10 21h4'
    });
    s.appendChild(p);
    var t = svg('title', {}, origin === 'victim_report' ? 'Reported by customer' : 'Fraud alert');
    s.appendChild(t);
    return s;
  }

  // ---------- clocks ----------
  function caseEndMs(c) {
    if (c.t_closed) return parseTs(c.t_closed);
    if (TERMINAL[c.state]) {
      if (endAt.has(c.case_id)) return endAt.get(c.case_id);
      var f = c.t_verified || c.t_triaged;
      if (f) return parseTs(f);
    }
    return null;
  }
  function clockInfo(c) {
    var start = parseTs(c.t_alert || c.created_at);
    if (isNaN(start)) return { text: '--:--', cls: 'clock' };
    var end = caseEndMs(c);
    var secs = ((end != null ? end : nowMs()) - start) / 1000;
    return { text: mmss(secs), cls: 'clock ' + (secs < TEN_MIN_S ? 'ok' : 'late') + (end != null ? ' done' : '') };
  }
  function tickClocks() {
    var els = document.querySelectorAll('[data-clock]');
    for (var i = 0; i < els.length; i++) {
      var c = cases.get(els[i].getAttribute('data-clock'));
      if (!c) continue;
      var info = clockInfo(c);
      if (els[i].textContent !== info.text) els[i].textContent = info.text;
      if (els[i].className !== info.cls) els[i].className = info.cls;
    }
  }

  // ---------- metrics ----------
  function renderMetrics(m) {
    $('m-protect').textContent = fmtDur(m.median_t_protect_s);
    $('m-ready').textContent = fmtDur(m.median_t_ready_s);
    $('m-protect-base').textContent = 'simulated baseline ' + mmss(m.baseline_median_t_protect_s);
    $('m-ready-base').textContent = 'simulated baseline ' + mmss(m.baseline_median_t_ready_s);
    $('m-pct').textContent = m.pct_protected_under_10min == null ? '—' : Math.round(m.pct_protected_under_10min) + '%';
    $('m-cases').textContent = m.cases_total + (m.cases_total === 1 ? ' case · ' : ' cases · ') + m.cases_fraud_confirmed + ' fraud';
    $('m-friction').textContent = fmtDur(m.median_genuine_friction_s);
    $('m-t1').textContent = m.t1_actions;
    $('m-t2').textContent = m.t2_decisions;
    $('m-t3').textContent = m.t3_blocked;
  }
  function loadMetrics() { return api('/metrics/summary').then(renderMetrics).catch(function () {}); }
  function loadHealth() {
    return api('/health').then(function (d) {
      var p = $('llm-pill');
      var up = d && d.llm === 'up';
      p.className = 'pill ' + (up ? 'pill-green' : 'pill-amber');
      p.textContent = up ? 'Claude up' : 'templates';
    }).catch(function () {});
  }

  // ---------- case queue ----------
  function sortedCases() {
    return Array.from(cases.values()).sort(function (a, b) {
      return parseTs(b.created_at) - parseTs(a.created_at);
    });
  }
  function renderQueue() {
    var list = $('case-list');
    clear(list);
    var arr = sortedCases();
    $('queue-count').textContent = arr.length;
    $('queue-empty').hidden = arr.length > 0;
    arr.forEach(function (c) {
      var info = clockInfo(c);
      var nm = names.get(c.case_id);
      var li = h('li', {
        class: 'case-item' + (c.case_id === selectedId ? ' sel' : ''), tabindex: '0', role: 'button',
        'data-case': c.case_id, 'aria-label': 'Open case ' + c.case_id,
        onclick: function () { selectCase(c.case_id); },
        onkeydown: function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectCase(c.case_id); } }
      },
        h('div', { class: 'case-row' },
          h('span', { class: 'case-user' }, originIcon(c.origin), nm || maskUser(c.user_id)),
          h('span', { class: info.cls, 'data-clock': c.case_id, text: info.text })),
        h('div', { class: 'case-row', style: 'margin-top:4px' },
          stateBadge(c.state),
          h('span', { class: 'small' }, 'risk ', h('b', { text: (c.risk_score || 0).toFixed(2) }))),
        h('div', { class: 'case-meta' },
          h('span', { text: c.case_id.replace(/^case_/, '#') }),
          h('span', { text: c.hold_active ? 'payments paused' : '' })));
      list.appendChild(li);
    });
  }
  function loadCases() {
    return api('/cases').then(function (arr) {
      var seen = {};
      arr.forEach(function (c) { seen[c.case_id] = 1; upsertCase(c, true); });
      Array.from(cases.keys()).forEach(function (id) { if (!seen[id]) cases.delete(id); });
      if (selectedId && !cases.has(selectedId)) { selectedId = null; detail = null; renderDetail(); }
      renderQueue();
    }).catch(function () {});
  }
  function upsertCase(c, quiet) {
    var prev = cases.get(c.case_id);
    if (TERMINAL[c.state] && c.state !== 'CLOSED' && !c.t_closed && !endAt.has(c.case_id) && prev && !TERMINAL[prev.state]) {
      endAt.set(c.case_id, nowMs());
    }
    cases.set(c.case_id, c);
    if (!quiet) renderQueue();
  }

  // ---------- selection + detail ----------
  function selectCase(id) {
    selectedId = id;
    detail = null;
    $('audit-result').textContent = '';
    $('audit-result').className = 'audit-result';
    renderQueue();
    renderDetail();
    renderDecisions();
    loadDetail();
  }
  function loadDetail() {
    var id = selectedId;
    if (!id) return Promise.resolve();
    var seq = ++detailSeq;
    return api('/cases/' + encodeURIComponent(id)).then(function (d) {
      if (seq !== detailSeq || id !== selectedId) return;
      detail = d;
      if (d.case) upsertCase(d.case, true);
      if (d.evidence && d.evidence.victim_name_masked) names.set(id, d.evidence.victim_name_masked);
      (d.decisions || []).forEach(function (x) { decisions.set(x.decision_id, x); });
      renderQueue();
      renderDetail();
      renderDecisions();
    }).catch(function () {});
  }
  var loadDetailSoon = debounce(loadDetail, 250);

  function renderDetail() {
    var has = !!(selectedId && detail);
    $('detail-empty').hidden = !!selectedId;
    $('detail').hidden = !has;
    $('btn-verify-audit').disabled = !selectedId;
    if (!has) return;
    renderHead(); renderRisk(); renderTimeline(true); renderEvidence(); renderTrail();
  }
  function curCase() { return (selectedId && cases.get(selectedId)) || (detail && detail.case) || null; }

  function renderHead() {
    var c = curCase(); if (!c) return;
    var box = $('d-head'); clear(box);
    var info = clockInfo(c);
    var nm = names.get(c.case_id);
    box.appendChild(h('span', { class: 'd-title', text: 'Case ' + c.case_id.replace(/^case_/, '#') }));
    box.appendChild(stateBadge(c.state));
    box.appendChild(h('span', { class: info.cls, 'data-clock': c.case_id, text: info.text, title: 'Time since alert (server t_alert)' }));
    box.appendChild(h('div', { class: 'kv' },
      h('span', {}, 'Customer ', h('b', { text: (nm ? nm + ' · ' : '') + maskUser(c.user_id) })),
      h('span', {}, 'Risk ', h('b', { text: (c.risk_score || 0).toFixed(2) })),
      h('span', {}, 'Origin ', h('b', { text: c.origin === 'victim_report' ? 'customer report' : 'fraud alert' })),
      h('span', {}, 'Language ', h('b', { text: c.lang })),
      h('span', {}, 'Own payments ', h('b', { text: c.hold_active ? 'paused (temporary hold)' : 'normal' })),
      h('span', {}, 'Alert ', h('b', { text: fmtFull(c.t_alert || c.created_at) })),
      c.t_contained ? h('span', {}, 'Protected ', h('b', { text: fmtTime(c.t_contained) })) : null,
      c.t_evidence_ready ? h('span', {}, 'Evidence ', h('b', { text: fmtTime(c.t_evidence_ready) })) : null));
  }

  function renderRisk() {
    var c = curCase(); if (!c) return;
    var box = $('d-risk'); clear(box);
    var expl = null;
    (detail.events || []).forEach(function (e) {
      if (e.type === 'TRIAGED' && e.payload && e.payload.explanation) expl = e.payload.explanation;
    });
    box.appendChild(h('div', { text: expl || 'Explanation pending…' }));
    var chips = h('div', { class: 'chips' });
    (c.signals || []).forEach(function (s) {
      chips.appendChild(h('span', { class: 'chip sig', title: s.detail || '', text: pretty(s.code) + ' ' + Number(s.weight).toFixed(2) }));
    });
    if ((c.signals || []).length) box.appendChild(chips);
  }

  // ---------- timeline ----------
  function actorChip(actor) {
    var cls = 'sys', label = actor || 'system';
    if (/^agent:/.test(label)) cls = 'agent';
    else if (/^human/.test(label)) cls = 'human';
    else if (label === 'victim') cls = 'victim';
    return h('span', { class: 'chip ' + cls, text: label });
  }
  function tierChip(t) {
    if (t === 1) return h('span', { class: 'chip t1', text: 'T1 auto' });
    if (t === 2) return h('span', { class: 'chip t2', text: 'T2 needs you' });
    if (t === 3) return h('span', { class: 'chip t3', text: 'T3 blocked' });
    return null;
  }
  function kvText(p) {
    var parts = [];
    Object.keys(p || {}).forEach(function (k) {
      var v = p[k];
      if (v == null) return;
      if (typeof v === 'object') v = Array.isArray(v) ? v.map(function (x) { return typeof x === 'object' ? '…' : x; }).join(', ') : '…';
      parts.push(k.replace(/_/g, ' ') + ': ' + v);
    });
    var s = parts.join(' · ');
    return s.length > 220 ? s.slice(0, 217) + '…' : s;
  }
  function eventText(e) {
    var p = e.payload || {};
    switch (e.type) {
      case 'ALERT_RECEIVED':
        return 'Alert score ' + (p.score != null ? Number(p.score).toFixed(2) : '?') + ' from ' + (p.source || 'model') + ', ' + ((p.txn_ids || []).length) + ' payments';
      case 'VICTIM_REPORT_RECEIVED': return p.text ? '“' + p.text + '”' : kvText(p);
      case 'STATE_CHANGED': return pretty(p.from) + ' → ' + pretty(p.to) + (p.reason ? ' (' + p.reason + ')' : '');
      case 'TRIAGED':
        if (p.explanation) return 'Risk explanation recorded';
        return 'Path ' + pretty(p.path) + ', score ' + (p.score != null ? Number(p.score).toFixed(2) : '?');
      case 'HOLD_PLACED': return 'Temporary hold on customer’s own outgoing payments' + (p.minutes ? ' for ' + p.minutes + ' min' : '') + (p.partner_ref ? ' · ' + p.partner_ref : '');
      case 'HOLD_RELEASED': return 'Temporary hold released' + (p.reason ? ' (' + p.reason + ')' : '');
      case 'SESSION_REVOKED': return 'Suspicious device signed out' + (p.device_id ? ': ' + p.device_id : '');
      case 'COMMS_SUPPRESSED':
        if (p.result === 'SUPPRESSED' || p.category === 'marketing') return 'Marketing message held (case open)';
        return 'Marketing and cross-sell messages held' + (p.minutes ? ' for ' + p.minutes + ' min' : '');
      case 'VICTIM_CONTACTED': return 'Customer contacted (' + (p.variant || 'message') + ')' + ((p.messages || []).length ? ': ' + p.messages[0] : '');
      case 'VICTIM_REPLIED': return 'Customer replied ' + pretty(p.intent) + (p.via ? ' via ' + p.via : '') + (p.transcript ? ': “' + p.transcript + '”' : '');
      case 'VERIFY_TIMEOUT': return 'No reply after ' + (p.seconds != null ? p.seconds + ' s' : 'timeout') + ', escalating';
      case 'EVIDENCE_READY': return 'Evidence pack ready: ' + (p.txn_count || 0) + ' payments, ' + inr(p.total_amount_paise);
      case 'VICTIM_GUIDED_1930': return 'Customer shown 1930 / NCRP steps with a prefilled summary';
      case 'NCRP_ACK_RECORDED': return 'Customer recorded NCRP acknowledgement ' + (p.ack_number || '');
      case 'DECISION_REQUESTED': return 'Asked officer: ' + actionLabel(p.action);
      case 'DECISION_MADE': return kvText(p);
      case 'POLICY_BLOCKED': return 'Blocked: ' + pretty(p.action) + (p.reason ? ' — ' + p.reason : '');
      case 'LLM_FALLBACK_USED': return 'Template used instead of language model' + (p.function ? ' (' + p.function + ')' : '');
      case 'CASE_CLOSED': return 'Case closed';
      default: return kvText(p);
    }
  }
  function timelineItem(e, isNew) {
    var tier = e.tier != null ? Number(e.tier) : null;
    return h('li', { class: 'tl-item' + (tier === 3 ? ' t3' : '') + (isNew ? ' new' : ''), 'data-evt': e.event_id },
      h('div', { class: 'tl-time', text: fmtTime(e.ts) }),
      h('div', {},
        h('div', { class: 'tl-line' },
          h('span', { class: 'tl-type', text: pretty(e.type) }), actorChip(e.actor), tierChip(tier)),
        h('div', { class: 'tl-text', text: eventText(e) })));
  }
  function renderTimeline(full) {
    var ol = $('d-timeline');
    var evs = (detail && detail.events) || [];
    var shown = evs.slice(-MAX_EVENTS);
    $('d-tl-note').textContent = evs.length > MAX_EVENTS ? '(last ' + MAX_EVENTS + ' of ' + evs.length + ')' : '(' + evs.length + ' events)';
    if (full) {
      clear(ol);
      shown.forEach(function (e) { ol.appendChild(timelineItem(e, false)); });
      ol.scrollTop = ol.scrollHeight;
    }
  }
  function appendEvent(e) {
    if (!detail || e.case_id !== selectedId) return;
    if (detail.events.some(function (x) { return x.event_id === e.event_id; })) return;
    detail.events.push(e);
    if (detail.events.length > MAX_EVENTS * 2) detail.events = detail.events.slice(-MAX_EVENTS);
    var ol = $('d-timeline');
    var stick = ol.scrollHeight - ol.scrollTop - ol.clientHeight < 40;
    ol.appendChild(timelineItem(e, true));
    while (ol.children.length > MAX_EVENTS) ol.removeChild(ol.firstChild);
    if (stick) ol.scrollTop = ol.scrollHeight;
    renderTimeline(false);
    if (e.type === 'TRIAGED' && e.payload && e.payload.explanation) renderRisk();
    if (e.type === 'EVIDENCE_READY') loadDetailSoon();
  }

  // ---------- evidence + money trail ----------
  function renderEvidence() {
    var box = $('d-evidence'); clear(box);
    var ev = detail && detail.evidence;
    if (!ev) { box.appendChild(h('div', { class: 'muted', text: 'Evidence pack not built yet.' })); return; }
    box.appendChild(h('div', { class: 'small muted', text: 'Customer ' + ev.victim_name_masked + ' · mobile ' + ev.mobile_masked + ' · generated ' + fmtFull(ev.generated_at) }));
    box.appendChild(h('p', { class: 'summary', text: ev.summary_en }, guardMiss(ev.summary_en)));
    box.appendChild(h('div', { class: 'sub', text: 'Payments · total ' + inr(ev.total_amount_paise) }));
    var tb = h('tbody');
    (ev.txns || []).forEach(function (t) {
      tb.appendChild(h('tr', {},
        h('td', { class: 'mono', text: t.txn_id }), h('td', { text: fmtTime(t.ts) }),
        h('td', { text: t.payee_vpa + (t.is_first_time_payee ? ' (new)' : '') }),
        h('td', { text: t.device_id }), h('td', { text: t.status }),
        h('td', { class: 'num', text: inr(t.amount_paise) })));
    });
    box.appendChild(h('table', {},
      h('thead', {}, h('tr', {}, h('th', { text: 'Txn' }), h('th', { text: 'Time' }), h('th', { text: 'Payee' }), h('th', { text: 'Device' }), h('th', { text: 'Status' }), h('th', { class: 'num', text: 'Amount' }))), tb));
    var fields = ev.ncrp_fields || {};
    var label = fields.Form;
    box.appendChild(h('div', { class: 'sub', text: 'NCRP field map' }));
    if (label) box.appendChild(h('div', { class: 'small muted', text: label }));
    var nb = h('tbody');
    Object.keys(fields).forEach(function (k) {
      if (k === 'Form') return;
      nb.appendChild(h('tr', {}, h('th', { text: k }), h('td', { text: fields[k] })));
    });
    box.appendChild(h('table', { class: 'ncrp' }, nb));
    var dt = ev.device_timeline || [];
    if (dt.length) {
      box.appendChild(h('div', { class: 'sub', text: 'Device timeline' }));
      var db = h('tbody');
      dt.forEach(function (d) {
        db.appendChild(h('tr', {},
          h('td', { text: d.model || d.device_id }), h('td', { text: d.geo_city || '' }),
          h('td', { text: 'first seen ' + fmtFull(d.first_seen) }),
          h('td', {}, h('span', { class: 'badge ' + (d.revoked ? 'b-red' : d.trusted ? 'b-green' : 'b-amber'), text: d.revoked ? 'signed out' : d.trusted ? 'trusted' : 'not trusted' }))));
      });
      box.appendChild(h('table', {}, db));
    }
  }

  function renderTrail() {
    var box = $('d-trail'); clear(box);
    box.className = 'card trail';
    var ev = detail && detail.evidence;
    if (!ev || !(ev.txns || []).length) { box.appendChild(h('div', { class: 'muted', text: 'Money trail appears once the evidence pack is ready.' })); return; }
    var by = {}, order = [];
    ev.txns.forEach(function (t) {
      if (!by[t.payee_vpa]) { by[t.payee_vpa] = { n: 0, sum: 0 }; order.push(t.payee_vpa); }
      by[t.payee_vpa].n++; by[t.payee_vpa].sum += t.amount_paise;
    });
    // table first
    var tb = h('tbody');
    order.forEach(function (v) {
      tb.appendChild(h('tr', {}, h('td', { text: v }), h('td', { class: 'num', text: by[v].n + ' payment' + (by[v].n > 1 ? 's' : '') }), h('td', { class: 'num', text: inr(by[v].sum) })));
    });
    box.appendChild(h('table', {}, h('thead', {}, h('tr', {}, h('th', { text: 'Payee' }), h('th', { class: 'num', text: 'Payments' }), h('th', { class: 'num', text: 'Total' }))), tb));
    // simple inline SVG: customer -> payees
    var shown = order.slice(0, 6);
    var rowH = 44, W = 600, H = Math.max(90, shown.length * rowH + 16);
    var s = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'Money trail from customer to payees' });
    var maxSum = Math.max.apply(null, shown.map(function (v) { return by[v].sum; }));
    var uy = H / 2;
    shown.forEach(function (v, i) {
      var y = 8 + i * rowH + rowH / 2 - 4;
      var w = 2 + 6 * (by[v].sum / maxSum);
      s.appendChild(svg('path', { class: 'link', 'stroke-width': w.toFixed(1), d: 'M150 ' + uy + ' C 280 ' + uy + ', 300 ' + y + ', 400 ' + y }));
      s.appendChild(svg('text', { class: 'amt', x: 275, y: ((uy + y) / 2 - 6).toFixed(0), 'text-anchor': 'middle' }, inr(by[v].sum)));
      s.appendChild(svg('rect', { class: 'node', x: 400, y: y - 16, width: 190, height: 32, rx: 8 }));
      s.appendChild(svg('text', { x: 410, y: y + 5 }, v.length > 22 ? v.slice(0, 21) + '…' : v));
    });
    s.appendChild(svg('rect', { class: 'node node-user', x: 10, y: uy - 22, width: 140, height: 44, rx: 10 }));
    s.appendChild(svg('text', { x: 80, y: uy - 2, 'text-anchor': 'middle' }, 'Customer'));
    s.appendChild(svg('text', { class: 'small', x: 80, y: uy + 14, 'text-anchor': 'middle' }, ev.victim_name_masked || ''));
    box.appendChild(s);
    if (order.length > shown.length) box.appendChild(h('div', { class: 'small muted', text: '+ ' + (order.length - shown.length) + ' more payees in the table' }));
  }

  // ---------- decisions ----------
  var cardEls = new Map();   // decision_id -> element (pending cards, reused to keep typed notes)
  var drafts = new Map();    // decision_id -> note text

  function pendingList() {
    return Array.from(decisions.values()).filter(function (d) { return d.status === 'PENDING'; })
      .sort(function (a, b) {
        var sa = a.case_id === selectedId ? 0 : 1, sb = b.case_id === selectedId ? 0 : 1;   // selected case first
        return sa - sb || parseTs(a.requested_at) - parseTs(b.requested_at);
      });
  }
  function buildCard(d) {
    var id = d.decision_id;
    var note = h('input', {
      type: 'text', id: 'dec-note-' + id, maxlength: '500', placeholder: 'Note (optional)', 'aria-label': 'Decision note',
      oninput: function (e) { drafts.set(id, e.target.value); }
    });
    note.value = drafts.get(id) || '';
    var err = h('div', { class: 'd-err', hidden: 'hidden' });
    var card = h('div', { class: 'dcard', id: 'dec-' + id, 'data-decision': id },
      h('div', { class: 'd-top' },
        h('span', { class: 'd-action', text: actionLabel(d.action) }),
        h('span', { class: 'chip t2', text: 'T2 needs you' })),
      h('button', { class: 'd-case', type: 'button', text: 'case ' + d.case_id.replace(/^case_/, '#'), onclick: function () { selectCase(d.case_id); } }),
      h('div', { class: 'd-why', text: d.rationale }, guardMiss(d.rationale)),
      note, err,
      h('div', { class: 'd-btns' },
        h('button', { class: 'btn btn-approve', id: 'dec-approve-' + id, type: 'button', text: 'Approve', onclick: function () { submitDecision(d.decision_id, true); } }),
        h('button', { class: 'btn btn-reject', id: 'dec-reject-' + id, type: 'button', text: 'Reject', onclick: function () { submitDecision(d.decision_id, false); } })));
    return card;
  }
  function renderDecisions() {
    var pend = pendingList();
    var box = $('pending-list');
    var keep = {};
    pend.forEach(function (d, i) {
      keep[d.decision_id] = 1;
      if (!cardEls.has(d.decision_id)) cardEls.set(d.decision_id, buildCard(d));
      var el = cardEls.get(d.decision_id);
      // only move nodes that are out of place, so a focused note field keeps focus
      if (box.children[i] !== el) box.insertBefore(el, box.children[i] || null);
    });
    Array.from(cardEls.keys()).forEach(function (id) {
      if (!keep[id]) { var el = cardEls.get(id); if (el.parentNode) el.parentNode.removeChild(el); cardEls.delete(id); drafts.delete(id); }
    });
    $('pending-count').textContent = pend.length;
    $('pending-empty').hidden = pend.length > 0;

    var rb = $('resolved-list'); clear(rb);
    var res = Array.from(decisions.values()).filter(function (d) { return d.status !== 'PENDING' && d.case_id === selectedId; })
      .sort(function (a, b) { return parseTs(b.decided_at) - parseTs(a.decided_at); });
    res.forEach(function (d) {
      rb.appendChild(h('div', { class: 'dcard resolved' },
        h('div', { class: 'd-top' },
          h('span', { class: 'd-action', text: actionLabel(d.action) }),
          h('span', { class: 'badge ' + (d.status === 'APPROVED' ? 'b-green' : 'b-red'), text: d.status })),
        h('div', { class: 'small muted', text: 'by ' + (d.decided_by || '—') + ' · ' + fmtFull(d.decided_at) }),
        d.note ? h('div', { class: 'd-why', text: 'Note: ' + d.note }) : null));
    });
    $('resolved-empty').hidden = res.length > 0;
  }
  function submitDecision(id, approve) {
    var card = cardEls.get(id);
    if (!card || card.classList.contains('busy')) return;
    var err = card.querySelector('.d-err');
    err.hidden = true;
    card.classList.add('busy');
    var btns = card.querySelectorAll('button'); btns.forEach(function (b) { b.disabled = true; });
    api('/decisions/' + encodeURIComponent(id), {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision_id: id, approve: approve, officer: 'officer_demo', note: (drafts.get(id) || '').slice(0, 500) })
    }).then(function (d) {
      decisions.set(d.decision_id, d);
      renderDecisions();
      refreshSoon();
      if (d.case_id === selectedId) loadDetailSoon();
    }).catch(function (e) {
      card.classList.remove('busy');
      btns.forEach(function (b) { b.disabled = false; });
      err.textContent = e.status === 409 ? 'Already decided elsewhere. Refreshing.' : e.status === 403 ? 'Blocked by policy.' : 'Failed: ' + e.message;
      err.hidden = false;
      if (e.status === 409) { loadQueue(); }
    });
  }
  function loadQueue() {
    return api('/officer/queue').then(function (rows) {
      var pendingIds = {};
      rows.forEach(function (r) {
        pendingIds[r.decision.decision_id] = 1;
        decisions.set(r.decision.decision_id, r.decision);
        if (r.case && r.case.victim_name_masked) names.set(r.case.case_id, r.case.victim_name_masked);
      });
      // anything we believed pending that the server no longer lists was decided
      Array.from(decisions.keys()).forEach(function (id) {
        if (decisions.get(id).status === 'PENDING' && !pendingIds[id]) decisions.delete(id);
      });
      renderDecisions();
      renderQueue();
    }).catch(function () {});
  }

  // ---------- audit ----------
  function verifyAudit() {
    if (!selectedId) return;
    var out = $('audit-result');
    out.className = 'audit-result'; out.textContent = 'Checking…';
    api('/audit/' + encodeURIComponent(selectedId) + '/verify').then(function (r) {
      if (r.ok) { out.className = 'audit-result ok'; out.textContent = '✓ chain intact (' + r.length + ' records)'; }
      else { out.className = 'audit-result bad'; out.textContent = '✗ broken at record ' + r.broken_at; }
    }).catch(function (e) { out.className = 'audit-result bad'; out.textContent = '✗ ' + e.message; });
  }

  // ---------- scenarios ----------
  function launch(name) {
    var st = $('sc-status');
    st.textContent = 'Launching ' + name + '…';
    var q = $('sc-autoreply').checked ? '?auto_reply=true' : '';
    api('/sim/scenario/' + encodeURIComponent(name) + q, { method: 'POST' }).then(function (r) {
      st.textContent = 'Started ' + name + ' (' + r.case_id + ')';
      return loadCases().then(function () { if (cases.has(r.case_id)) selectCase(r.case_id); else { selectedId = r.case_id; } });
    }).catch(function (e) { st.textContent = 'Failed: ' + e.message; });
  }
  function resetAll() {
    var st = $('sc-status');
    st.textContent = 'Resetting…';
    api('/sim/reset', { method: 'POST' }).then(function () {
      cases.clear(); decisions.clear(); names.clear(); endAt.clear();
      selectedId = null; detail = null;
      renderQueue(); renderDetail(); renderDecisions();
      st.textContent = 'Reset done';
      return Promise.all([loadCases(), loadQueue(), loadMetrics()]);
    }).catch(function (e) { st.textContent = 'Failed: ' + e.message; });
  }

  // ---------- live stream ----------
  var refreshSoon = debounce(function () { loadMetrics(); loadQueue(); }, 300);
  var resyncSoon = debounce(function () { loadCases().then(function () { loadQueue(); loadMetrics(); loadHealth(); if (selectedId) loadDetail(); }); }, 300);

  function onMessage(ev) {
    var msg;
    try { msg = JSON.parse(ev.data); } catch (e) { return; }
    var d = msg.data || {};
    if (msg.kind === 'case') {
      upsertCase(d);
      if (d.case_id === selectedId) {
        if (detail) detail.case = d;
        renderHead();
      }
    } else if (msg.kind === 'event') {
      if (!cases.has(d.case_id)) resyncSoon();
      if (d.case_id === selectedId) appendEvent(d);
    } else if (msg.kind === 'decision') {
      decisions.set(d.decision_id, d);
      if (detail && d.case_id === selectedId) {
        var i = (detail.decisions || []).findIndex(function (x) { return x.decision_id === d.decision_id; });
        if (i >= 0) detail.decisions[i] = d; else (detail.decisions = detail.decisions || []).push(d);
      }
      renderDecisions();
      if (d.status === 'PENDING' && !names.has(d.case_id)) refreshSoon();
    } else if (msg.kind === 'metrics') {
      renderMetrics(d);
      loadHealth();
    }
  }
  function connect() {
    var es = new EventSource('/events');
    es.onopen = function () {
      $('banner').hidden = true;
      resyncSoon();   // initial load and every reconnect: re-fetch cases (debounced)
    };
    es.onmessage = onMessage;
    es.onerror = function () {
      // EventSource reconnects by itself; just tell the officer.
      $('banner').hidden = false;
    };
  }

  // ---------- init ----------
  document.querySelectorAll('[data-scenario]').forEach(function (b) {
    b.addEventListener('click', function () { launch(b.getAttribute('data-scenario')); });
  });
  $('sc-reset').addEventListener('click', resetAll);
  $('btn-verify-audit').addEventListener('click', verifyAudit);

  renderQueue(); renderDecisions();
  loadHealth(); loadMetrics(); loadCases(); loadQueue();
  connect();
  setInterval(tickClocks, 1000);
  setInterval(loadHealth, 20000);
})();
