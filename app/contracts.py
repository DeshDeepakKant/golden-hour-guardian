"""
FROZEN CONTRACTS — Golden Hour Guardian
=======================================
Single source of truth shared by every build agent.
Only the MAIN session may edit this file (see HANDOFF.md, "Contract change rule").

Conventions
- Money is always integer paise (₹1 = 100 paise). Never floats for money.
- Time is always timezone-aware UTC datetime; UI converts to IST.
- IDs are short strings with a prefix: case_, evt_, dec_, txn_, usr_, dev_, alr_.
- The LLM never produces numbers, IDs or amounts. Code fills them into templates.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Literal, Optional, Protocol

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class CaseState(str, Enum):
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    DISMISSED = "DISMISSED"                       # low risk, no action
    HELD_PENDING_VERIFY = "HELD_PENDING_VERIFY"   # high risk: reversible hold, verifying
    VERIFYING = "VERIFYING"                       # medium risk: verifying, no hold yet
    CONFIRMED_GENUINE = "CONFIRMED_GENUINE"
    RELEASED = "RELEASED"
    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"
    CONTAINED = "CONTAINED"                       # victim's OWN access protected
    EVIDENCE_READY = "EVIDENCE_READY"
    AWAITING_OFFICER = "AWAITING_OFFICER"         # Tier-2 decisions pending
    NO_RESPONSE_ESCALATED = "NO_RESPONSE_ESCALATED"
    CLOSED = "CLOSED"


class Tier(IntEnum):
    T1_AUTO = 1        # agent acts alone (reversible, victim-side, informational)
    T2_HUMAN = 2       # agent prepares, human approves
    T3_FORBIDDEN = 3   # never, enforced in code


class EventType(str, Enum):
    ALERT_RECEIVED = "ALERT_RECEIVED"
    VICTIM_REPORT_RECEIVED = "VICTIM_REPORT_RECEIVED"
    TRIAGED = "TRIAGED"
    STATE_CHANGED = "STATE_CHANGED"
    HOLD_PLACED = "HOLD_PLACED"
    HOLD_RELEASED = "HOLD_RELEASED"
    SESSION_REVOKED = "SESSION_REVOKED"
    COMMS_SUPPRESSED = "COMMS_SUPPRESSED"
    VICTIM_CONTACTED = "VICTIM_CONTACTED"
    VICTIM_REPLIED = "VICTIM_REPLIED"
    VERIFY_TIMEOUT = "VERIFY_TIMEOUT"
    EVIDENCE_READY = "EVIDENCE_READY"
    VICTIM_GUIDED_1930 = "VICTIM_GUIDED_1930"
    NCRP_ACK_RECORDED = "NCRP_ACK_RECORDED"
    DECISION_REQUESTED = "DECISION_REQUESTED"
    DECISION_MADE = "DECISION_MADE"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    LLM_FALLBACK_USED = "LLM_FALLBACK_USED"
    CASE_CLOSED = "CASE_CLOSED"


class SignalCode(str, Enum):
    NEW_DEVICE = "NEW_DEVICE"
    SIM_CHANGE_72H = "SIM_CHANGE_72H"
    FIRST_TIME_PAYEE = "FIRST_TIME_PAYEE"
    PAYEE_FANIN_SPIKE = "PAYEE_FANIN_SPIKE"   # payee received from many new senders recently
    VELOCITY_SPIKE = "VELOCITY_SPIKE"
    GEO_JUMP = "GEO_JUMP"
    AMOUNT_ANOMALY = "AMOUNT_ANOMALY"
    ODD_HOUR = "ODD_HOUR"


class ReplyIntent(str, Enum):
    YES_MINE = "YES_MINE"
    NOT_ME = "NOT_ME"
    UNSURE = "UNSURE"
    ASKS_REFUND = "ASKS_REFUND"     # never auto-acted on; routed to officer
    DISTRESS = "DISTRESS"           # calm script + human callback
    OTHER = "OTHER"


class DecisionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Channel(str, Enum):
    APP_TRUSTED_DEVICE = "APP_TRUSTED_DEVICE"   # in-app on the previously trusted device
    VOICE_REGISTERED_NO = "VOICE_REGISTERED_NO" # untrusted if SIM_CHANGE_72H present
    OFFICER_CALLBACK = "OFFICER_CALLBACK"


Lang = Literal["en", "hi", "te"]


# ---------------------------------------------------------------------------
# Actions and their tiers (the policy engine enforces this table)
# ---------------------------------------------------------------------------
class Action(str, Enum):
    # Tier 1 — autonomous
    READ_LEDGER = "read_ledger"
    SCORE_RISK = "score_risk"
    PLACE_TEMP_HOLD = "place_temp_hold"             # victim's OWN outgoing payments, auto-expires
    RELEASE_HOLD_TRUSTED = "release_hold_trusted"   # victim said YES_MINE on trusted channel, no SIM change
    REVOKE_SESSION = "revoke_session"               # suspicious session/device on victim's own account
    NOTIFY_VICTIM = "notify_victim"
    START_VERIFICATION = "start_verification"
    BUILD_EVIDENCE_PACK = "build_evidence_pack"
    GUIDE_NCRP = "guide_ncrp"                       # show 1930/NCRP steps + prefilled summary to victim
    SUPPRESS_MARKETING = "suppress_marketing"
    REQUEST_DECISION = "request_decision"           # create a Tier-2 decision for the officer
    # Tier 2 — human approves
    RAISE_DISPUTE = "raise_dispute"
    EXTEND_HOLD = "extend_hold"
    RELEASE_HOLD_UNTRUSTED = "release_hold_untrusted"
    SHARE_EVIDENCE_WITH_BANK = "share_evidence_with_bank"
    REFUND_OR_CREDIT = "refund_or_credit"
    RESTORE_ACCESS = "restore_access"
    FLAG_PAYEE_INTERNAL = "flag_payee_internal"
    OFFICER_CALLBACK = "officer_callback"           # a human calls the victim (refund asks, distress, unclear)
    # Tier 3 — forbidden
    FREEZE_BENEFICIARY = "freeze_beneficiary"
    FILE_POLICE_COMPLAINT = "file_police_complaint"
    REQUEST_OTP_PIN = "request_otp_pin"
    PROMISE_REFUND = "promise_refund"
    CONTACT_PAYEE = "contact_payee"


ACTION_TIERS: dict[Action, Tier] = {
    Action.READ_LEDGER: Tier.T1_AUTO,
    Action.SCORE_RISK: Tier.T1_AUTO,
    Action.PLACE_TEMP_HOLD: Tier.T1_AUTO,
    Action.RELEASE_HOLD_TRUSTED: Tier.T1_AUTO,
    Action.REVOKE_SESSION: Tier.T1_AUTO,
    Action.NOTIFY_VICTIM: Tier.T1_AUTO,
    Action.START_VERIFICATION: Tier.T1_AUTO,
    Action.BUILD_EVIDENCE_PACK: Tier.T1_AUTO,
    Action.GUIDE_NCRP: Tier.T1_AUTO,
    Action.SUPPRESS_MARKETING: Tier.T1_AUTO,
    Action.REQUEST_DECISION: Tier.T1_AUTO,
    Action.RAISE_DISPUTE: Tier.T2_HUMAN,
    Action.EXTEND_HOLD: Tier.T2_HUMAN,
    Action.RELEASE_HOLD_UNTRUSTED: Tier.T2_HUMAN,
    Action.SHARE_EVIDENCE_WITH_BANK: Tier.T2_HUMAN,
    Action.REFUND_OR_CREDIT: Tier.T2_HUMAN,
    Action.RESTORE_ACCESS: Tier.T2_HUMAN,
    Action.FLAG_PAYEE_INTERNAL: Tier.T2_HUMAN,
    Action.OFFICER_CALLBACK: Tier.T2_HUMAN,
    Action.FREEZE_BENEFICIARY: Tier.T3_FORBIDDEN,
    Action.FILE_POLICE_COMPLAINT: Tier.T3_FORBIDDEN,
    Action.REQUEST_OTP_PIN: Tier.T3_FORBIDDEN,
    Action.PROMISE_REFUND: Tier.T3_FORBIDDEN,
    Action.CONTACT_PAYEE: Tier.T3_FORBIDDEN,
}

assert set(ACTION_TIERS) == set(Action), "every Action must have a tier"


# ---------------------------------------------------------------------------
# Inbound payloads
# ---------------------------------------------------------------------------
class Signal(BaseModel):
    code: SignalCode
    weight: float = Field(ge=0, le=1)
    detail: str = ""


class FraudAlert(BaseModel):
    alert_id: str
    user_id: str
    source: Literal["model", "rule"] = "model"
    score: float = Field(ge=0, le=1)
    signals: list[Signal] = []
    txn_ids: list[str] = []
    created_at: datetime = Field(default_factory=utcnow)


class VictimReport(BaseModel):
    user_id: str
    channel: Literal["app", "voice"] = "app"
    text: str = Field(max_length=2000)
    lang: Lang = "en"
    created_at: datetime = Field(default_factory=utcnow)


class VictimResponse(BaseModel):
    case_id: str
    answer: Optional[ReplyIntent] = None   # set when a button is tapped
    transcript: Optional[str] = Field(default=None, max_length=2000)  # set when spoken/typed
    lang: Lang = "en"
    channel: Channel = Channel.APP_TRUSTED_DEVICE


class NcrpAck(BaseModel):
    case_id: str
    ack_number: str = Field(min_length=4, max_length=40)


class OfficerDecisionIn(BaseModel):
    decision_id: str
    approve: bool
    officer: str = "officer_demo"
    note: str = Field(default="", max_length=500)


# ---------------------------------------------------------------------------
# Domain records
# ---------------------------------------------------------------------------
class Txn(BaseModel):
    txn_id: str
    user_id: str
    payee_vpa: str
    amount_paise: int
    ts: datetime
    status: Literal["SUCCESS", "PENDING", "FAILED", "REVERSED"] = "SUCCESS"
    device_id: str
    is_first_time_payee: bool = False


class Case(BaseModel):
    case_id: str
    user_id: str
    state: CaseState = CaseState.NEW
    risk_score: float = 0.0
    signals: list[Signal] = []
    txn_ids: list[str] = []
    lang: Lang = "en"
    trusted_channel: Channel = Channel.APP_TRUSTED_DEVICE
    hold_active: bool = False
    hold_expires_at: Optional[datetime] = None
    origin: Literal["alert", "victim_report"] = "alert"
    created_at: datetime = Field(default_factory=utcnow)
    # metric timestamps (filled as they happen)
    t_alert: Optional[datetime] = None
    t_triaged: Optional[datetime] = None
    t_victim_contacted: Optional[datetime] = None
    t_verified: Optional[datetime] = None
    t_contained: Optional[datetime] = None
    t_evidence_ready: Optional[datetime] = None
    t_guided_1930: Optional[datetime] = None
    t_officer_decided: Optional[datetime] = None
    t_closed: Optional[datetime] = None


class CaseEvent(BaseModel):
    event_id: str
    case_id: str
    ts: datetime = Field(default_factory=utcnow)
    type: EventType
    actor: str            # "system" | "agent:<name>" | "human:<role>" | "victim"
    tier: Optional[Tier] = None
    payload: dict[str, Any] = {}
    prev_hash: str = ""
    hash: str = ""        # sha256(prev_hash + canonical_json(event without hash))


class Decision(BaseModel):
    decision_id: str
    case_id: str
    action: Action
    status: DecisionStatus = DecisionStatus.PENDING
    rationale: str            # why the agent recommends it (LLM-worded, facts from code)
    requested_at: datetime = Field(default_factory=utcnow)
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    note: str = ""


class EvidencePack(BaseModel):
    case_id: str
    generated_at: datetime = Field(default_factory=utcnow)
    victim_name_masked: str          # e.g. "R*** K***"
    mobile_masked: str               # e.g. "98******21"
    txns: list[Txn]
    total_amount_paise: int
    payee_vpas: list[str]
    device_timeline: list[dict[str, Any]]
    signals: list[Signal]
    ncrp_fields: dict[str, str]      # field -> value, ready to copy into the portal by the VICTIM
    summary_victim_lang: str         # narrative in victim's language
    summary_en: str                  # narrative for officer/bank


class MetricsSummary(BaseModel):
    cases_total: int
    cases_fraud_confirmed: int
    median_t_protect_s: Optional[float]        # alert -> contained
    median_t_ready_s: Optional[float]          # alert -> evidence ready AND victim guided
    pct_protected_under_10min: Optional[float]
    median_genuine_friction_s: Optional[float] # alert -> released, for genuine users
    t1_actions: int                            # autonomous actions taken
    t2_decisions: int                          # human decisions made
    t3_blocked: int                            # forbidden actions blocked by policy
    baseline_median_t_protect_s: float         # simulated manual baseline (config/baseline.yaml)
    baseline_median_t_ready_s: float


# ---------------------------------------------------------------------------
# Interfaces between modules (implemented by different agents)
# ---------------------------------------------------------------------------
class BrainAPI(Protocol):
    """Implemented in app/brain/api.py by the `brain` agent.
    Every function MUST return within settings.llm.timeout_s and MUST fall back to
    deterministic templates if the LLM is unavailable or output fails the guard.
    After each call, `last_used_fallback` tells the caller whether a template was used
    (core-engine logs LLM_FALLBACK_USED when it is True)."""

    last_used_fallback: bool

    def explain_risk(self, case: Case, txns: list[Txn]) -> str: ...
    def verification_messages(self, case: Case, txns: list[Txn]) -> list[str]: ...
    def classify_reply(self, text: str, lang: Lang) -> tuple[ReplyIntent, float]: ...
    def evidence_narratives(self, pack: EvidencePack, lang: Lang) -> tuple[str, str]: ...
    def decision_rationale(self, case: Case, action: Action) -> str: ...
    def ncrp_guidance(self, pack: EvidencePack, lang: Lang) -> list[str]: ...  # steps shown to the victim


class PartnerGateway(Protocol):
    """Implemented in mocks/partners.py by the `mockworld` agent.
    Stands in for real bank / PSP / notification systems. All calls are logged."""

    def place_hold(self, user_id: str, minutes: int) -> str: ...
    def release_hold(self, user_id: str) -> None: ...
    def revoke_session(self, user_id: str, device_id: str) -> None: ...
    def send_push(self, user_id: str, payload: dict[str, Any]) -> None: ...
    def suppress_marketing(self, user_id: str, minutes: int) -> None: ...
    def raise_dispute(self, txn_ids: list[str], evidence_ref: str) -> str: ...  # Tier-2 only


class LedgerRepo(Protocol):
    """Implemented in app/repo.py by the `core-engine` agent (reads the SQLite seed)."""

    def get_txns(self, txn_ids: list[str]) -> list[Txn]: ...
    def recent_txns(self, user_id: str, minutes: int) -> list[Txn]: ...
    def user_profile(self, user_id: str) -> dict[str, Any]: ...
    def device_timeline(self, user_id: str, hours: int) -> list[dict[str, Any]]: ...
    def payee_fanin(self, payee_vpa: str, minutes: int) -> int: ...


# ---------------------------------------------------------------------------
# Server-sent event envelope (GET /events and GET /victim/{user_id}/events)
# ---------------------------------------------------------------------------
class StreamMessage(BaseModel):
    kind: Literal["event", "case", "decision", "metrics", "victim_prompt"]
    data: dict[str, Any]
