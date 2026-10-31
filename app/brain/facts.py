"""Fact sheets. Code owns every number/name; the model only ever sees masked, number-free facts.

`values`  -> real strings filled into {placeholders} by code (never sent to the model).
`prompt`  -> what the model sees: signal codes, flags, which placeholders exist. No raw mobile
             numbers, no full names, no amounts/times/counts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta, timezone
from typing import Any

from app.contracts import Case, EvidencePack, Signal, SignalCode, Txn

IST = timezone(timedelta(hours=5, minutes=30))

SIGNAL_PHRASES_EN = {
    SignalCode.NEW_DEVICE: "a login from a device not seen before",
    SignalCode.SIM_CHANGE_72H: "a recent SIM change",
    SignalCode.FIRST_TIME_PAYEE: "payments to first-time payees",
    SignalCode.PAYEE_FANIN_SPIKE: "a payee receiving money from many new senders",
    SignalCode.VELOCITY_SPIKE: "an unusual burst of payments",
    SignalCode.GEO_JUMP: "activity from a distant location",
    SignalCode.AMOUNT_ANOMALY: "amounts far above this customer's normal",
    SignalCode.ODD_HOUR: "activity at an unusual hour",
}


def format_inr(paise: int) -> str:
    """Integer paise -> '₹24,999' (Indian digit grouping; '.50' only if paise are non-zero)."""
    paise = int(paise)
    sign = "-" if paise < 0 else ""
    rupees, rem = divmod(abs(paise), 100)
    s = str(rupees)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return f"{sign}₹{s}" + (f".{rem:02d}" if rem else "")


def format_ist(ts) -> str:
    """tz-aware (or naive-UTC) datetime -> '02:15 PM' in IST."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(IST).strftime("%I:%M %p")


def top_signals(signals: list[Signal], n: int = 3) -> list[SignalCode]:
    seen: list[SignalCode] = []
    for s in sorted(signals, key=lambda s: -s.weight):
        if s.code not in seen:
            seen.append(s.code)
    return seen[:n]


@dataclass
class Facts:
    values: dict[str, str] = field(default_factory=dict)
    prompt: dict[str, Any] = field(default_factory=dict)
    signals: list[SignalCode] = field(default_factory=list)
    new_device: bool = False


def _payees(txns: list[Txn], limit: int = 3) -> str:
    out: list[str] = []
    for t in txns:
        if t.payee_vpa not in out:
            out.append(t.payee_vpa)
    return ", ".join(out[:limit])


def case_facts(case: Case, txns: list[Txn]) -> Facts:
    sigs = top_signals(case.signals)
    total = sum(t.amount_paise for t in txns)
    latest = max((t.ts for t in txns), default=None)
    values = {
        "count": str(len(txns)),
        "amount": format_inr(total),
        "time": format_ist(latest) if latest else "",
        "payees": _payees(txns),
    }
    return Facts(
        values=values,
        signals=sigs,
        new_device=SignalCode.NEW_DEVICE in sigs or SignalCode.SIM_CHANGE_72H in sigs,
        prompt={
            "signal_codes": [s.value for s in sigs],
            "signal_meaning": [SIGNAL_PHRASES_EN[s] for s in sigs],
            "new_phone_or_sim_change": SignalCode.NEW_DEVICE in sigs or SignalCode.SIM_CHANGE_72H in sigs,
            "available_placeholders": ["{count}", "{amount}", "{time}"],
        },
    )


def pack_facts(pack: EvidencePack) -> Facts:
    sigs = top_signals(pack.signals)
    latest = max((t.ts for t in pack.txns), default=None)
    first = min((t.ts for t in pack.txns), default=None)
    # City of the first non-trusted device to appear (never the victim's own trusted phone).
    city = ""
    rows = sorted(pack.device_timeline or [], key=lambda r: str(r.get("first_seen") or ""))
    for row in rows:
        if row.get("trusted"):
            continue
        c = row.get("geo_city") or row.get("city")
        if isinstance(c, str) and c.strip():
            city = c.strip()
            break
    values = {
        "count": str(len(pack.txns)),
        "amount": format_inr(pack.total_amount_paise),
        "first": format_ist(first) if first else "",
        "time": format_ist(latest) if latest else "",
        "payees": ", ".join(pack.payee_vpas[:3]),
        "city": city,
    }
    return Facts(
        values=values,
        signals=sigs,
        new_device=SignalCode.NEW_DEVICE in sigs,
        prompt={
            "victim_name_masked": pack.victim_name_masked,
            "signal_codes": [s.value for s in sigs],
            "signal_meaning": [SIGNAL_PHRASES_EN[s] for s in sigs],
            "available_placeholders": ["{count}", "{amount}", "{first}", "{time}", "{payees}", "{city}"],
        },
    )
