-- FROZEN DB SCHEMA (SQLite). Only the MAIN session edits this file.
-- Money in paise (INTEGER). Times as ISO-8601 UTC TEXT.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---------- synthetic world (written by mocks/seed.py) ----------
CREATE TABLE IF NOT EXISTS users (
  user_id        TEXT PRIMARY KEY,
  name           TEXT NOT NULL,          -- synthetic names only
  mobile         TEXT NOT NULL,          -- synthetic numbers only
  city           TEXT NOT NULL,
  lang           TEXT NOT NULL DEFAULT 'en',
  trusted_device TEXT NOT NULL,
  sim_changed_at TEXT                    -- NULL if no recent SIM change
);

CREATE TABLE IF NOT EXISTS devices (
  device_id   TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(user_id),
  model       TEXT NOT NULL,
  first_seen  TEXT NOT NULL,
  last_seen   TEXT NOT NULL,
  geo_city    TEXT NOT NULL,
  revoked     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS txns (
  txn_id              TEXT PRIMARY KEY,
  user_id             TEXT NOT NULL REFERENCES users(user_id),
  payee_vpa           TEXT NOT NULL,
  amount_paise        INTEGER NOT NULL,
  ts                  TEXT NOT NULL,
  status              TEXT NOT NULL,
  device_id           TEXT NOT NULL,
  is_first_time_payee INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_txns_user_ts ON txns(user_id, ts);
CREATE INDEX IF NOT EXISTS ix_txns_payee_ts ON txns(payee_vpa, ts);

-- ---------- case management (written by app/) ----------
CREATE TABLE IF NOT EXISTS cases (
  case_id  TEXT PRIMARY KEY,
  user_id  TEXT NOT NULL REFERENCES users(user_id),
  state    TEXT NOT NULL,
  json     TEXT NOT NULL            -- full Case model as JSON (source of truth)
);
CREATE INDEX IF NOT EXISTS ix_cases_state ON cases(state);

CREATE TABLE IF NOT EXISTS case_events (   -- append-only, hash-chained audit log
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id   TEXT UNIQUE NOT NULL,
  case_id    TEXT NOT NULL,
  ts         TEXT NOT NULL,
  type       TEXT NOT NULL,
  actor      TEXT NOT NULL,
  tier       INTEGER,
  payload    TEXT NOT NULL,
  prev_hash  TEXT NOT NULL,
  hash       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_events_case ON case_events(case_id, seq);

CREATE TABLE IF NOT EXISTS decisions (
  decision_id TEXT PRIMARY KEY,
  case_id     TEXT NOT NULL,
  status      TEXT NOT NULL,
  json        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_decisions_status ON decisions(status);

CREATE TABLE IF NOT EXISTS evidence_packs (
  case_id TEXT PRIMARY KEY,
  json    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_calls (  -- every mock partner call, for the demo + audit
  seq     INTEGER PRIMARY KEY AUTOINCREMENT,
  ts      TEXT NOT NULL,
  method  TEXT NOT NULL,
  args    TEXT NOT NULL,
  result  TEXT
);
