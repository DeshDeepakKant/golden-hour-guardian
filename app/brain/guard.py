"""Output guard for LLM text. Fail -> caller uses a deterministic template.

Rules: banned patterns (config/policy.yaml llm_guard + built-ins), max length, no digit runs >= 3
outside placeholders (numbers come from code), no URLs except cybercrime.gov.in, no unknown
placeholders, and the text must be in the right script for hi/te.
"""
from __future__ import annotations

import re

from app.config import POLICY

ALLOWED_PLACEHOLDERS = frozenset({"amount", "count", "time", "payees", "city", "ack"})
ALLOWED_DOMAIN = "cybercrime.gov.in"
ALLOWED_NUMBERS = frozenset({"1930"})  # national cyber-fraud helpline, fixed fact
MAX_LEN = 600

# Always on, in addition to config/policy.yaml: promises of outcomes we cannot give.
_BUILTIN_BANNED = [
    r"\bguarantee",
    r"will be (refunded|returned|reversed|frozen|recovered)",
    r"we (will|shall) (freeze|return|recover|get your money)",
    r"money back",
    r"वापस मिल",
    r"रिफंड (मिल|हो) जाएगा",
    r"लौटा (देंगे|दिया जाएगा)",
    r"రిఫండ్ వస్తుంది",
    r"తిరిగి (వస్తుంది|ఇస్తాము|ఇస్తాం)",
    # Hinglish (Latin-script Hindi) refund promises
    r"\bwapas (mil|kar|de)",
    r"\blauta?a? ?denge\b",
    r"\brefund (mil|ho) jayega\b",
    # Asking the victim for any code (OTP by another name) — Tier 3 REQUEST_OTP_PIN
    r"\b(enter|share|tell|give|send|read out|type)\b[^.]{0,30}\bcodes?\b",
    # Claims of Tier-3 actions we never take (FREEZE_BENEFICIARY, FILE_POLICE_COMPLAINT)
    r"\bwill freeze\b|\bfrozen\b",
    r"complaint (has been|was|is being|is) (filed|lodged|registered)",
]

_PLACEHOLDER_RE = re.compile(r"\{([a-z_]+)\}")
_DIGIT_RUN_RE = re.compile(r"\d{3,}")
_URL_RE = re.compile(
    r"(?:https?://|www\.)\S+"
    r"|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|in|org|net|gov|io|co|app|me|ly|xyz|info|biz|link|top)\b(?:/\S*)?",
    re.I,
)
_SCRIPTS = {"hi": (r"[ऀ-ॿ]", "Devanagari"), "te": (r"[ఀ-౿]", "Telugu")}


def _banned_patterns() -> list[re.Pattern[str]]:
    pats = list(POLICY.get("llm_guard", {}).get("banned_patterns", [])) + _BUILTIN_BANNED
    return [re.compile(p, re.I) for p in pats]


def check(text: str, lang: str = "en", max_len: int = MAX_LEN) -> tuple[bool, str]:
    """Return (ok, reason). reason is "" when ok."""
    if not isinstance(text, str) or not text.strip():
        return False, "empty"
    if len(text) > max_len:
        return False, "too_long"
    for pat in _banned_patterns():
        if pat.search(text):
            return False, f"banned:{pat.pattern}"
    for name in _PLACEHOLDER_RE.findall(text):
        if name not in ALLOWED_PLACEHOLDERS:
            return False, f"unknown_placeholder:{name}"
    bare = _PLACEHOLDER_RE.sub(" ", text)
    for run in _DIGIT_RUN_RE.findall(bare):
        if run not in ALLOWED_NUMBERS:
            return False, "digit_run"
    for m in _URL_RE.finditer(bare):
        url = m.group(0).lower().rstrip(".,;:!?)'\"")
        url = re.sub(r"^https?://", "", url).removeprefix("www.").rstrip("/")
        if url != ALLOWED_DOMAIN and not url.startswith(ALLOWED_DOMAIN + "/"):
            return False, "url"
    if "{" in bare or "}" in bare:
        return False, "malformed_placeholder"
    if lang in _SCRIPTS:
        script_re = re.compile(_SCRIPTS[lang][0])
        native = _URL_RE.sub(" ", re.sub(r"'[^']*'", " ", bare))  # ignore quoted UI labels / the domain
        letters = [c for c in native if c.isalpha()]
        if letters and sum(1 for c in letters if script_re.match(c)) / len(letters) < 0.3:
            return False, f"wrong_script:{_SCRIPTS[lang][1]}"
    return True, ""
