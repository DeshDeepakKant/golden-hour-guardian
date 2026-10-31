"""Persistence for Case / Decision / EvidencePack (JSON column = full pydantic model)."""
from __future__ import annotations

from typing import Optional

from app.contracts import Case, Decision, DecisionStatus, EvidencePack
from app.db import connect
from app.util import aware


def save_case(case: Case) -> None:
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO cases (case_id, user_id, state, json) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(case_id) DO UPDATE SET state = excluded.state, json = excluded.json",
            (case.case_id, case.user_id, case.state.value, case.model_dump_json()),
        )
        conn.commit()
    finally:
        conn.close()


def get_case(case_id: str) -> Optional[Case]:
    conn = connect()
    try:
        row = conn.execute("SELECT json FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    finally:
        conn.close()
    return Case.model_validate_json(row["json"]) if row else None


def refresh(case: Case) -> Case:
    """Copy the persisted fields into `case` in place (so a stale object never overwrites newer data)."""
    fresh = get_case(case.case_id)
    if fresh is not None:
        for name in Case.model_fields:
            setattr(case, name, getattr(fresh, name))
    return case


def list_cases(state: Optional[str] = None) -> list[Case]:
    conn = connect()
    try:
        if state:
            rows = conn.execute("SELECT json FROM cases WHERE state = ?", (state,)).fetchall()
        else:
            rows = conn.execute("SELECT json FROM cases").fetchall()
    finally:
        conn.close()
    cases = [Case.model_validate_json(r["json"]) for r in rows]
    return sorted(cases, key=lambda c: aware(c.created_at), reverse=True)


def latest_open_case_for_user(user_id: str) -> Optional[Case]:
    for c in list_cases():
        if c.user_id == user_id and c.state.value not in ("CLOSED", "DISMISSED", "RELEASED"):
            return c
    return None


def find_case_by_alert(alert_id: str) -> Optional[str]:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT case_id FROM case_events WHERE type = 'ALERT_RECEIVED' "
            "AND json_extract(payload, '$.alert_id') = ? ORDER BY seq LIMIT 1",
            (alert_id,),
        ).fetchone()
    finally:
        conn.close()
    return row["case_id"] if row else None


# ---------------------------------------------------------------- decisions
def save_decision(d: Decision) -> None:
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO decisions (decision_id, case_id, status, json) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(decision_id) DO UPDATE SET status = excluded.status, json = excluded.json",
            (d.decision_id, d.case_id, d.status.value, d.model_dump_json()),
        )
        conn.commit()
    finally:
        conn.close()


def get_decision(decision_id: str) -> Optional[Decision]:
    conn = connect()
    try:
        row = conn.execute("SELECT json FROM decisions WHERE decision_id = ?", (decision_id,)).fetchone()
    finally:
        conn.close()
    return Decision.model_validate_json(row["json"]) if row else None


def list_decisions(case_id: Optional[str] = None, status: Optional[DecisionStatus] = None) -> list[Decision]:
    sql, args = "SELECT json FROM decisions", []
    clauses = []
    if case_id:
        clauses.append("case_id = ?")
        args.append(case_id)
    if status:
        clauses.append("status = ?")
        args.append(status.value)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    conn = connect()
    try:
        rows = conn.execute(sql, args).fetchall()
    finally:
        conn.close()
    return sorted((Decision.model_validate_json(r["json"]) for r in rows), key=lambda d: aware(d.requested_at))


# ----------------------------------------------------------------- evidence
def save_evidence(pack: EvidencePack) -> None:
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO evidence_packs (case_id, json) VALUES (?, ?) "
            "ON CONFLICT(case_id) DO UPDATE SET json = excluded.json",
            (pack.case_id, pack.model_dump_json()),
        )
        conn.commit()
    finally:
        conn.close()


def get_evidence(case_id: str) -> Optional[EvidencePack]:
    conn = connect()
    try:
        row = conn.execute("SELECT json FROM evidence_packs WHERE case_id = ?", (case_id,)).fetchone()
    finally:
        conn.close()
    return EvidencePack.model_validate_json(row["json"]) if row else None
