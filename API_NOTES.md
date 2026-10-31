# API_NOTES (UI agents read this + app/contracts.py)
Money = integer paise. Times = UTC ISO (show IST). All JSON. Every endpoint of SPEC §7 exists.

## SSE
`GET /events` (console, every message) and `GET /victim/{user_id}/events` (only that user's `victim_prompt`).
Unnamed events; `data:` is a `StreamMessage` JSON `{"kind", "data"}`. Use `es.onmessage`, switch on `kind`.
First line is a `: connected` comment, then a `: ping` comment every 15 s. On reconnect refetch `/cases`.
```
{"kind":"event","data":{"event_id":"evt_ab12","case_id":"case_1","ts":"2026-10-31T07:07:23Z","type":"HOLD_PLACED","actor":"agent:shield","tier":1,"payload":{"minutes":60,"partner_ref":"HOLD-9F2A"},"prev_hash":"..","hash":".."}}
{"kind":"case","data":{ ...full Case (state, risk_score, signals, hold_active, t_alert, t_contained, ...) }}
{"kind":"decision","data":{"decision_id":"dec_1","case_id":"case_1","action":"raise_dispute","status":"PENDING","rationale":"...","requested_at":"..","decided_by":null}}
{"kind":"metrics","data":{"cases_total":3,"cases_fraud_confirmed":1,"median_t_protect_s":5.4,"median_t_ready_s":5.5,"pct_protected_under_10min":100.0,"median_genuine_friction_s":null,"t1_actions":10,"t2_decisions":3,"t3_blocked":0,"baseline_median_t_protect_s":2100.0,"baseline_median_t_ready_s":3900.0}}
```
`event.tier`: 1 auto (green), 2 needs human (amber), 3 blocked (red), null = plain system. `POLICY_BLOCKED` events carry `payload.{action,tier,reason}`.
Event actors: `system`, `agent:{sentinel,shield,voice,scribe,desk}`, `human:<officer>`, `victim`.

## victim_prompt (data of kind `victim_prompt`; also `GET /victim/{user_id}/pending` returns the latest, or `null`)
Common keys: `case_id, user_id, variant, lang (en|hi|te), messages[str], expects_reply, answers[], txns[], deadline, safety_line, ts`.
```
verify   {"variant":"verify","messages":["...2-3 lines..."],"expects_reply":true,"answers":["YES_MINE","NOT_ME","UNSURE"],"txns":[{"txn_id":"txn_1","payee_vpa":"m1.qx@demo","amount_paise":2499900,"ts":".."}],"deadline":"..."}
retry    {"variant":"retry","messages":["Just to be sure: did you make the payment of ₹24,999 to m1.qx@demo? Please tap Yes or No."],"expects_reply":true,"answers":[...]}
protected{"variant":"protected","messages":["Your outgoing payments are paused for now.","The suspicious phone has been signed out.","..."],"actions_taken":["outgoing_payments_paused","device_signed_out","marketing_held"],"expects_reply":false}
ncrp_guide{"variant":"ncrp_guide","messages":["step 1","step 2"],"summary":"copyable text (victim lang)","ncrp_fields":{"Category":"Online Financial Fraud","Sub-category":"UPI related","Suspect UPI IDs":"m1.qx@demo, m2.zt@demo"},"helpline":"1930","portal":"https://cybercrime.gov.in","field_map_label":"Demo field map (...)"}
released {"variant":"released","messages":["Thank you. Your payments are back to normal."],"expects_reply":false}
done     {"variant":"done","messages":["Thank you. A member of our fraud team will call you shortly."],"expects_reply":false}
```
`done` is sent after an NCRP ack, and also after an escalation to an officer callback (refund ask, distress, unclear, no reply, untrusted yes). Prompts are held in memory (lost on server restart).

## Endpoints (details beyond SPEC §7)
- `POST /webhooks/fraud-alert` / `victim-report` -> 202 `{case_id}`; 404 unknown user. Alert idempotent on `alert_id`.
- `GET /cases?state=` -> `[Case]` newest first. `GET /cases/{id}` -> `{case, events[], decisions[], evidence|null}`.
- `GET /officer/queue` -> `[{decision, case:{case_id,user_id,state,risk_score,origin,t_alert,hold_active,txn_ids,victim_name_masked}, sla_age_s}]` (PENDING only).
- `POST /decisions/{id}` body `{decision_id, approve, officer?, note?}` -> `Decision`; 404 unknown, 409 already decided, 403 if policy blocks. Approving runs the Tier-2 tool. Case closes when no PENDING decisions remain.
- `POST /victim/respond` body `{case_id, answer?|transcript?, lang, channel}` -> `{state}`. 404 case, 422 neither answer nor transcript. A reply to a case that is not awaiting an answer is ignored (state returned).
- `POST /victim/ncrp-ack` `{case_id, ack_number}` -> `{ok:true}`; 422 if the number has odd characters.
- `GET /audit/{case_id}/verify` -> `{ok, length, broken_at}` (`broken_at` = DB seq of first bad row).
- `POST /sim/scenario/{name}?auto_reply=true&delay=4` -> `{case_id, scenario, auto_reply}`. Names: ato genuine inbound noresponse injection. `POST /sim/reset` -> `{ok:true}` (cancels tasks, reseeds; SSE clients stay connected, refetch `/cases`).
- `GET /health` -> `{ok, llm:"up"|"fallback"}`. `GET /metrics/summary` -> `MetricsSummary`.

## Paths to expect (states)
ato + NOT_ME: NEW, TRIAGED, HELD_PENDING_VERIFY, CONFIRMED_FRAUD, CONTAINED, EVIDENCE_READY, AWAITING_OFFICER (3 decisions: raise_dispute, extend_hold, share_evidence_with_bank), CLOSED.
ato + YES_MINE: SIM changed so not trusted: AWAITING_OFFICER with one `release_hold_untrusted` decision, hold stays.
genuine + YES_MINE: VERIFYING, RELEASED (stays RELEASED, no close). inbound: NEW -> CONFIRMED_FRAUD directly (no verify prompt).
noresponse (120 s) / injection / UNSURE twice: AWAITING_OFFICER with one `officer_callback` decision.
Env `GUARDIAN_VERIFY_TIMEOUT_S` overrides the 120 s verification timeout.
