# mockworld — HANDOFF

**Receives from:** scaffolder stubs (`mocks/*`, `app/db.py`) + frozen contracts.

**Delivers to:**
- `core-engine`: `mocks.seed.seed(conn, reset)`, `mocks.scenarios.inject(conn, name)`, `mocks.partners.partners`. Core calls them from `/sim/*` routes and tools. Function names and return shapes above are the interface — don't rename.
- `qa` / `demo-director`: scenario names and their `scripted_reply` values.

**Must not:** import anything from `app/` except `app.contracts`, `app.db`, `app.config`. No real-looking personal data, real bank names or real UPI handles.

**Exit report (≤120 words):** files, test result, the exact user IDs + scenario names, anything core-engine must know (e.g. timing of the queued marketing push).

**Pitfalls:** timestamps must be UTC ISO strings; amounts in paise (₹24,999 = 2499900); fan-in txns must belong to *other* users so they don't pollute usr_ravi's history.
