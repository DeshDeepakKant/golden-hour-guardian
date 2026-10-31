"""Scribe: evidence pack (masked) + demo NCRP field map + victim guidance."""
from __future__ import annotations

import asyncio
import re

from app import brain_call, fsm, store, texts, tools
from app.agents import sentinel, voice
from app.contracts import CaseState as S, EvidencePack, Case, utcnow
from app.repo import repo
from app.util import fmt_inr, fmt_ist

ACTOR = "agent:scribe"
FORM_LABEL = "Demo field map (approximation of the NCRP form; fields may differ on the real portal)"


def mask_name(name: str) -> str:
    """'Ravi Kumar (demo)' -> 'R*** K***'."""
    name = re.sub(r"\(.*?\)", "", name).strip()
    return " ".join(w[0].upper() + "***" for w in name.split() if w) or "***"


def mask_mobile(mobile: str) -> str:
    """'9000000021' -> '90******21'."""
    digits = re.sub(r"\D", "", mobile)
    if len(digits) <= 4:
        return "*" * len(digits)
    return digits[:2] + "*" * (len(digits) - 4) + digits[-2:]


def build_pack(case: Case) -> EvidencePack:
    """Structure only; narratives are filled in afterwards. Facts all come from the ledger."""
    profile = repo.user_profile(case.user_id)
    txns = sorted(sentinel.suspect_txns(case), key=lambda t: t.ts)
    total = sum(t.amount_paise for t in txns)
    payees = list(dict.fromkeys(t.payee_vpa for t in txns))
    first, last = (txns[0].ts, txns[-1].ts) if txns else (utcnow(), utcnow())
    description = (f"Unauthorised UPI payments totalling {fmt_inr(total)} to {len(payees)} payee(s) "
                   f"between {fmt_ist(first)} and {fmt_ist(last)}. Reported by the customer via the bank app."
                   if txns else "Customer reports unauthorised UPI payments.")
    ncrp = {
        "Form": FORM_LABEL,
        "Category": "Online Financial Fraud",
        "Sub-category": "UPI related",
        "Number of transactions": str(len(txns)),
        "Transaction IDs": ", ".join(t.txn_id for t in txns),
        "Amounts": ", ".join(fmt_inr(t.amount_paise) for t in txns),
        "Total amount": fmt_inr(total),
        "Transaction timestamps (IST)": ", ".join(fmt_ist(t.ts) for t in txns),
        "Suspect UPI IDs": ", ".join(payees),
        "Short description": description,
    }
    return EvidencePack(
        case_id=case.case_id, victim_name_masked=mask_name(profile.get("name", "")),
        mobile_masked=mask_mobile(profile.get("mobile", "")), txns=txns, total_amount_paise=total,
        payee_vpas=payees, device_timeline=repo.device_timeline(case.user_id, 72), signals=case.signals,
        ncrp_fields=ncrp, summary_victim_lang="", summary_en=description,
    )


async def run(case_id: str) -> None:
    """CONTAINED -> EVIDENCE_READY, then show the victim the 1930/NCRP steps."""
    case = store.get_case(case_id)
    pack = build_pack(case)
    fallback_text = pack.summary_en
    narratives, steps = await asyncio.gather(
        brain_call.call(case_id, "evidence_narratives", pack, case.lang, default=(fallback_text, fallback_text)),
        brain_call.call(case_id, "ncrp_guidance", pack, case.lang,
                        default=["Call 1930 or visit cybercrime.gov.in to report this fraud."]),
    )
    summary_victim, summary_en = narratives
    pack = pack.model_copy(update={"summary_victim_lang": summary_victim, "summary_en": summary_en})

    case = store.get_case(case_id)
    tools.build_evidence_pack(case, pack, ACTOR)
    fsm.transition(store.get_case(case_id), S.EVIDENCE_READY, ACTOR, "evidence pack built")

    case = store.get_case(case_id)
    prompt = voice._prompt(
        case, "ncrp_guide", list(steps), summary=pack.summary_victim_lang, ncrp_fields=pack.ncrp_fields,
        helpline="1930", portal="https://cybercrime.gov.in", field_map_label=FORM_LABEL,
    )
    tools.guide_ncrp(case, ACTOR, prompt)
