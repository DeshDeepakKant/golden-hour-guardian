"""STUB Brain — deterministic one-line English templates, no LLM.
The `brain` agent replaces the internals and keeps these names (see contracts.BrainAPI)."""
from __future__ import annotations

from app.contracts import Action, Case, EvidencePack, Lang, ReplyIntent, Txn


class Brain:
    last_used_fallback: bool = True

    def explain_risk(self, case: Case, txns: list[Txn]) -> str:
        self.last_used_fallback = True
        return "Unusual activity was detected on this account."

    def verification_messages(self, case: Case, txns: list[Txn]) -> list[str]:
        self.last_used_fallback = True
        return ["We noticed a payment from your account. Was this you?"]

    def classify_reply(self, text: str, lang: Lang) -> tuple[ReplyIntent, float]:
        self.last_used_fallback = True
        return ReplyIntent.OTHER, 0.0

    def evidence_narratives(self, pack: EvidencePack, lang: Lang) -> tuple[str, str]:
        self.last_used_fallback = True
        text = "Suspicious transactions were recorded on this account."
        return text, text

    def decision_rationale(self, case: Case, action: Action) -> str:
        self.last_used_fallback = True
        return f"Recommended action: {action.value}."

    def ncrp_guidance(self, pack: EvidencePack, lang: Lang) -> list[str]:
        self.last_used_fallback = True
        return ["Call 1930 or visit cybercrime.gov.in to report this fraud."]


brain = Brain()
