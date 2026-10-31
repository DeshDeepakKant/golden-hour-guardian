"""Voice: the verification dialogue with the victim (button or transcript). Never asks for secrets.

The LLM only produces an intent enum via classify_reply; fixed mappings below decide what happens.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

from app import audit, brain_call, fsm, orchestrator_tasks as tasks, store, texts, tools
from app.agents import desk, sentinel
from app.config import POLICY
from app.contracts import (
    Action, Case, CaseState as S, EventType, ReplyIntent, VictimResponse, utcnow,
)
from app.policy import PolicyBlocked
from app.util import fmt_inr
from datetime import timedelta

ACTOR = "agent:voice"
VERIFY_STATES = {S.VERIFYING, S.HELD_PENDING_VERIFY}
ANSWERS = [ReplyIntent.YES_MINE.value, ReplyIntent.NOT_ME.value, ReplyIntent.UNSURE.value]
# transcript confidence needed before we trust an answer (buttons are always 1.0)
MIN_CONF = {ReplyIntent.YES_MINE: 0.7, ReplyIntent.NOT_ME: 0.5}


def timeout_s() -> float:
    env = os.environ.get("GUARDIAN_VERIFY_TIMEOUT_S")
    return float(env) if env else float(POLICY["verification"]["timeout_seconds"])


def _txn_view(case: Case) -> list[dict[str, Any]]:
    return [{"txn_id": t.txn_id, "payee_vpa": t.payee_vpa, "amount_paise": t.amount_paise,
             "ts": t.ts.isoformat()} for t in sentinel.suspect_txns(case)]


def _prompt(case: Case, variant: str, messages: list[str], **extra: Any) -> dict[str, Any]:
    asks = variant in ("verify", "retry")
    p: dict[str, Any] = {
        "case_id": case.case_id, "user_id": case.user_id, "variant": variant, "lang": case.lang,
        "messages": messages, "expects_reply": asks, "answers": ANSWERS if asks else [],
        "txns": _txn_view(case) if asks else [],
        "deadline": (utcnow() + timedelta(seconds=timeout_s())).isoformat() if asks else None,
        "safety_line": texts.pick(texts.SAFETY, case.lang), "ts": utcnow().isoformat(),
    }
    p.update(extra)
    return p


async def start_verification(case_id: str) -> None:
    case = store.get_case(case_id)
    txns = sentinel.suspect_txns(case)
    messages = await brain_call.call(case_id, "verification_messages", case, txns,
                                     default=["We noticed a payment from your account. Was this you?"])
    case = store.get_case(case_id)
    if case.state not in VERIFY_STATES:
        return
    tools.notify_victim(case, ACTOR, _prompt(case, "verify", list(messages)))
    tasks.spawn(case_id, _timeout(case_id, timeout_s()), "verify_timeout")


def send_simple(case: Case, variant: str, table: dict[str, str]) -> None:
    tools.notify_victim(case, ACTOR, _prompt(case, variant, [texts.pick(table, case.lang)]))


def send_protected(case_id: str) -> None:
    case = store.get_case(case_id)
    events = audit.list_events(case_id)
    taken, lines = [], []
    if case.hold_active:
        taken.append("outgoing_payments_paused")
    if any(e.type == EventType.SESSION_REVOKED for e in events):
        taken.append("device_signed_out")
    if any(e.type == EventType.COMMS_SUPPRESSED for e in events):
        taken.append("marketing_held")
    lines = [texts.pick(texts.PROTECTED[k], case.lang) for k in taken]
    lines.append(texts.pick(texts.PROTECTED["_review"], case.lang))
    tools.notify_victim(case, ACTOR, _prompt(case, "protected", lines, actions_taken=taken))


async def _timeout(case_id: str, seconds: float) -> None:
    await asyncio.sleep(seconds)
    case = store.get_case(case_id)
    if case is None or case.state not in VERIFY_STATES:
        return
    audit.append(case_id, EventType.VERIFY_TIMEOUT, "system", None, {"seconds": seconds})
    await desk.escalate(case_id, "NO_RESPONSE")
    send_simple(store.get_case(case_id), "done", texts.CALLBACK)


def _clip(text: Optional[str], n: int = 300) -> Optional[str]:
    return text if text is None or len(text) <= n else text[:n] + "..."


async def handle_response(resp: VictimResponse) -> dict[str, Any]:
    case = store.get_case(resp.case_id)
    if case is None:
        raise LookupError(resp.case_id)
    if resp.answer is None and not (resp.transcript and resp.transcript.strip()):
        raise ValueError("send either an answer or a transcript")
    if case.state not in VERIFY_STATES:
        audit.append(case.case_id, EventType.VICTIM_REPLIED, "victim", None,
                     {"ignored": True, "reason": f"case is {case.state.value}, not awaiting an answer"})
        return {"state": case.state.value}

    # 1) turn the reply into an intent. Buttons map directly; free text goes through the classifier.
    via, conf = "button", 1.0
    if resp.answer is not None:
        raw = resp.answer
    else:
        via = "transcript"
        out = await brain_call.call(case.case_id, "classify_reply", resp.transcript, resp.lang,
                                    default=(ReplyIntent.OTHER, 0.0))
        try:
            raw, conf = ReplyIntent(out[0]), float(out[1])
        except (ValueError, TypeError, IndexError):
            raw, conf = ReplyIntent.OTHER, 0.0
    case = store.get_case(case.case_id)           # reload after the await
    if case.state not in VERIFY_STATES:
        return {"state": case.state.value}
    intent = raw
    if via == "transcript" and intent in MIN_CONF and conf < MIN_CONF[intent]:
        intent = ReplyIntent.UNSURE               # not confident enough to act on

    if resp.lang != case.lang:
        case.lang = resp.lang
        store.save_case(case)
    audit.append(case.case_id, EventType.VICTIM_REPLIED, "victim", None,
                 {"intent": intent.value, "raw_intent": raw.value, "confidence": conf, "via": via,
                  "channel": resp.channel.value, "transcript": _clip(resp.transcript)})
    tasks.cancel(case.case_id, "verify_timeout")

    # 2) fixed intent -> action mapping (no LLM involvement past this point)
    cid = case.case_id
    if intent == ReplyIntent.NOT_ME:
        fsm.transition(case, S.CONFIRMED_FRAUD, ACTOR, "victim said it was not them")
        from app import orchestrator
        tasks.spawn(cid, orchestrator.run_fraud_pipeline(cid), "fraud_pipeline")
    elif intent == ReplyIntent.YES_MINE:
        try:
            tools.release_hold_trusted(case, ACTOR, resp.channel)
        except PolicyBlocked:
            await desk.escalate(cid, "UNTRUSTED_YES", Action.RELEASE_HOLD_UNTRUSTED)
            send_simple(store.get_case(cid), "done", texts.CALLBACK)
        else:
            fsm.transition(store.get_case(cid), S.CONFIRMED_GENUINE, ACTOR, "victim confirmed on trusted channel")
            fsm.transition(store.get_case(cid), S.RELEASED, ACTOR, "hold released, payments normal")
            send_simple(store.get_case(cid), "released", texts.RELEASED)
    elif intent == ReplyIntent.UNSURE:
        retries = sum(1 for e in audit.list_events(cid)
                      if e.type == EventType.VICTIM_CONTACTED and e.payload.get("variant") == "retry")
        if retries < POLICY["verification"].get("retries", 1):
            _send_retry(store.get_case(cid))
        else:
            await desk.escalate(cid, "UNSURE")
            send_simple(store.get_case(cid), "done", texts.CALLBACK)
    else:   # ASKS_REFUND / DISTRESS / OTHER: never auto-act, a human calls back
        await desk.escalate(cid, intent.value)
        send_simple(store.get_case(cid), "done", texts.CALLBACK)
    return {"state": store.get_case(cid).state.value}


def _send_retry(case: Case) -> None:
    txns = sentinel.suspect_txns(case)
    if txns:
        biggest = max(txns, key=lambda t: t.amount_paise)
        line = texts.pick(texts.RETRY, case.lang).format(amount=fmt_inr(biggest.amount_paise),
                                                          payee=biggest.payee_vpa)
    else:
        line = texts.pick(texts.RETRY, case.lang).format(amount="the payment", payee="the payee")
    tools.notify_victim(case, ACTOR, _prompt(case, "retry", [line]))
    tasks.spawn(case.case_id, _timeout(case.case_id, timeout_s()), "verify_timeout")
