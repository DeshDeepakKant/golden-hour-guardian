"""Synthetic sample objects shared by tests and scripts/bench_llm.py. Fake data only."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.contracts import Case, CaseState, EvidencePack, Signal, SignalCode, Txn


def sample_txns() -> list[Txn]:
    base = datetime(2026, 3, 14, 8, 45, tzinfo=timezone.utc)  # 14:15 IST
    return [
        Txn(txn_id=f"txn_{i}", user_id="usr_demo", payee_vpa=f"mule{i}@fakebank",
            amount_paise=amt, ts=base + timedelta(minutes=i), device_id="dev_new",
            is_first_time_payee=True)
        for i, amt in enumerate([1_000_000, 900_000, 599_900], start=1)
    ]


def sample_signals() -> list[Signal]:
    return [
        Signal(code=SignalCode.NEW_DEVICE, weight=0.9),
        Signal(code=SignalCode.SIM_CHANGE_72H, weight=0.8),
        Signal(code=SignalCode.PAYEE_FANIN_SPIKE, weight=0.85),
        Signal(code=SignalCode.FIRST_TIME_PAYEE, weight=0.6),
    ]


def sample_case(lang: str = "en") -> Case:
    return Case(case_id="case_demo", user_id="usr_demo", state=CaseState.HELD_PENDING_VERIFY,
                risk_score=0.93, signals=sample_signals(),
                txn_ids=[t.txn_id for t in sample_txns()], lang=lang)  # type: ignore[arg-type]


def sample_pack(lang: str = "en") -> EvidencePack:
    txns = sample_txns()
    return EvidencePack(
        case_id="case_demo", victim_name_masked="R*** K***", mobile_masked="98******21",
        txns=txns, total_amount_paise=sum(t.amount_paise for t in txns),
        payee_vpas=[t.payee_vpa for t in txns],
        device_timeline=[{"device_id": "dev_new", "geo_city": "Pune"}],
        signals=sample_signals(), ncrp_fields={}, summary_victim_lang="", summary_en="",
    )
