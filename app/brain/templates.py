"""Deterministic fallback text for every BrainAPI method x language (en, hi, te).

# TODO: native speaker check  (Hindi and Telugu strings; see HANDOFF H5)

Placeholders: {amount} {count} {time} {payees} {city} {ack}. Code fills them (see `fill`).
Amounts arrive pre-formatted ("₹24,999"); do not spell numbers in words (TTS speaks the digits).
Internal-only extras used by code templates: {signals}, {phrase}.
"""
from __future__ import annotations

import re
from typing import Mapping

from app.contracts import Action, SignalCode

LANGS = ("en", "hi", "te")

DEFAULT_CITY = {"en": "a new location", "hi": "एक नई जगह", "te": "కొత్త ప్రదేశం"}

SAFETY_LINE = {
    "en": "We will never ask for your OTP, PIN or password.",
    "hi": "हम आपसे कभी OTP, PIN या पासवर्ड नहीं माँगेंगे।",
    "te": "మేము మిమ్మల్ని ఎప్పుడూ OTP, PIN లేదా పాస్‌వర్డ్ అడగము.",
}

# --- verification_messages ------------------------------------------------
VERIFY_WHAT = {
    "en": "Guardian security check: {count} payment(s) totalling {amount} left your account at {time}.",
    "hi": "Guardian सुरक्षा जाँच: आपके खाते से {time} पर {count} भुगतान हुए, कुल {amount}।",
    "te": "Guardian భద్రతా తనిఖీ: మీ ఖాతా నుండి {time} కి {count} చెల్లింపులు జరిగాయి, మొత్తం {amount}.",
}
VERIFY_WHAT_NEWDEV = {
    "en": "Guardian security check: {count} payment(s) totalling {amount} left your account at {time}, and a new phone was used.",
    "hi": "Guardian सुरक्षा जाँच: आपके खाते से {time} पर {count} भुगतान हुए, कुल {amount}, और एक नया फ़ोन इस्तेमाल हुआ।",
    "te": "Guardian భద్రతా తనిఖీ: మీ ఖాతా నుండి {time} కి {count} చెల్లింపులు జరిగాయి, మొత్తం {amount}, ఒక కొత్త ఫోన్ ఉపయోగించబడింది.",
}
VERIFY_QUESTION = {
    "en": "Did you make these payments?",
    "hi": "क्या ये भुगतान आपने किए हैं?",
    "te": "ఈ చెల్లింపులు మీరు చేశారా?",
}

# --- signal wording -------------------------------------------------------
SIGNAL_TEXT = {
    "en": {
        SignalCode.NEW_DEVICE: "a login from a device not seen before",
        SignalCode.SIM_CHANGE_72H: "a recent SIM change",
        SignalCode.FIRST_TIME_PAYEE: "payments to first-time payees",
        SignalCode.PAYEE_FANIN_SPIKE: "a payee receiving money from many new senders",
        SignalCode.VELOCITY_SPIKE: "an unusual burst of payments",
        SignalCode.GEO_JUMP: "activity from a distant location",
        SignalCode.AMOUNT_ANOMALY: "amounts far above this customer's normal",
        SignalCode.ODD_HOUR: "activity at an unusual hour",
    },
    "hi": {
        SignalCode.NEW_DEVICE: "एक नए डिवाइस से लॉगिन",
        SignalCode.SIM_CHANGE_72H: "हाल ही में SIM बदला जाना",
        SignalCode.FIRST_TIME_PAYEE: "पहली बार के प्राप्तकर्ता को भुगतान",
        SignalCode.PAYEE_FANIN_SPIKE: "एक प्राप्तकर्ता को कई नए लोगों से पैसे आना",
        SignalCode.VELOCITY_SPIKE: "कम समय में असामान्य रूप से कई भुगतान",
        SignalCode.GEO_JUMP: "दूर की जगह से गतिविधि",
        SignalCode.AMOUNT_ANOMALY: "सामान्य से कहीं ज़्यादा रकम",
        SignalCode.ODD_HOUR: "असामान्य समय पर गतिविधि",
    },
    "te": {
        SignalCode.NEW_DEVICE: "కొత్త పరికరం నుండి లాగిన్",
        SignalCode.SIM_CHANGE_72H: "ఇటీవల SIM మార్పు",
        SignalCode.FIRST_TIME_PAYEE: "మొదటిసారి గ్రహీతకు చెల్లింపులు",
        SignalCode.PAYEE_FANIN_SPIKE: "ఒక గ్రహీతకు చాలా కొత్త వ్యక్తుల నుండి డబ్బు రావడం",
        SignalCode.VELOCITY_SPIKE: "తక్కువ సమయంలో అసాధారణంగా ఎక్కువ చెల్లింపులు",
        SignalCode.GEO_JUMP: "దూర ప్రదేశం నుండి కార్యకలాపం",
        SignalCode.AMOUNT_ANOMALY: "సాధారణం కంటే చాలా ఎక్కువ మొత్తం",
        SignalCode.ODD_HOUR: "అసాధారణ సమయంలో కార్యకలాపం",
    },
}
JOINER = {"en": " and ", "hi": " और ", "te": " మరియు "}
NO_SIGNALS = {"en": "unusual activity", "hi": "असामान्य गतिविधि", "te": "అసాధారణ కార్యకలాపం"}

# --- explain_risk (English, officer) -------------------------------------
EXPLAIN_RISK = (
    "Guardian flagged this case because of {signals}. "
    "These patterns can indicate account takeover or a mule payee, so an officer should review "
    "before any money-related decision."
)

# --- evidence_narratives --------------------------------------------------
NARRATIVE = {
    "en": (
        "At {time}, {count} payment(s) totalling {amount} left this account to {payees}. "
        "The account showed {signals}. Recent activity was seen from {city}. "
        "This summary records facts only and does not assign blame."
    ),
    "hi": (
        "{time} पर आपके खाते से {payees} को {count} भुगतान हुए, कुल {amount}। "
        "खाते में {signals} दिखे। हाल की गतिविधि {city} से दिखी। "
        "यह सारांश केवल तथ्य बताता है।"
    ),
    "te": (
        "{time} కి మీ ఖాతా నుండి {payees} కు {count} చెల్లింపులు జరిగాయి, మొత్తం {amount}. "
        "ఖాతాలో {signals} కనిపించాయి. ఇటీవలి కార్యకలాపం {city} నుండి కనిపించింది. "
        "ఈ సారాంశం వాస్తవాలను మాత్రమే తెలుపుతుంది."
    ),
}

# --- decision_rationale (English, officer) --------------------------------
RATIONALE = (
    "Suggested for officer review: {phrase}. Signals on this case: {signals}. "
    "This is a recommendation only; the decision is yours."
)
ACTION_PHRASE = {
    Action.RAISE_DISPUTE: "raise a dispute with the bank for the suspected fraudulent payments",
    Action.EXTEND_HOLD: "extend the temporary hold on the customer's own outgoing payments past the automatic limit",
    Action.RELEASE_HOLD_UNTRUSTED: "release the hold although the confirmation did not come over a trusted channel",
    Action.SHARE_EVIDENCE_WITH_BANK: "share the evidence pack with the bank",
    Action.REFUND_OR_CREDIT: "review whether any credit to the customer is appropriate",
    Action.RESTORE_ACCESS: "restore the customer's access after the account was secured",
    Action.FLAG_PAYEE_INTERNAL: "flag the payee internally for monitoring",
    Action.OFFICER_CALLBACK: "call the customer, who asked about money back or sounds distressed",
}

# --- ncrp_guidance --------------------------------------------------------
NCRP_STEPS = {
    "en": [
        "Call 1930 (the national cyber fraud helpline) or open cybercrime.gov.in and choose 'Report financial fraud'.",
        "Keep the summary ready. Use the copy button in this app.",
        "Share the transaction IDs, amounts and suspect UPI IDs shown in the summary.",
        "Note the acknowledgement number you receive and enter it in this app.",
        "Our fraud team is reviewing your case.",
    ],
    "hi": [
        "1930 पर कॉल करें या cybercrime.gov.in खोलकर 'Report financial fraud' चुनें।",
        "सारांश तैयार रखें। इस ऐप में कॉपी बटन दबाएँ।",
        "सारांश में दिए गए लेन-देन ID, रकम और संदिग्ध UPI ID बताएँ।",
        "शिकायत की पावती संख्या लिख लें और इस ऐप में दर्ज करें।",
        "हमारी फ्रॉड टीम आपके मामले की समीक्षा कर रही है।",
    ],
    "te": [
        "1930 కు కాల్ చేయండి లేదా cybercrime.gov.in తెరిచి 'Report financial fraud' ఎంచుకోండి.",
        "సారాంశాన్ని సిద్ధంగా ఉంచండి. ఈ యాప్‌లో కాపీ బటన్ నొక్కండి.",
        "సారాంశంలో ఉన్న లావాదేవీ ID లు, మొత్తాలు, అనుమానిత UPI ID లను చెప్పండి.",
        "మీకు వచ్చే రసీదు (acknowledgement) నంబర్‌ను నోట్ చేసుకుని ఈ యాప్‌లో నమోదు చేయండి.",
        "మా ఫ్రాడ్ బృందం మీ కేసును సమీక్షిస్తోంది.",
    ],
}


# --- helpers --------------------------------------------------------------
def norm_lang(lang: str) -> str:
    return lang if lang in LANGS else "en"


def signals_text(codes, lang: str) -> str:
    lang = norm_lang(lang)
    phrases = [SIGNAL_TEXT[lang][c] for c in codes if c in SIGNAL_TEXT[lang]]
    if not phrases:
        return NO_SIGNALS[lang]
    if len(phrases) == 1:
        return phrases[0]
    return ", ".join(phrases[:-1]) + JOINER[lang] + phrases[-1]


def action_phrase(action: Action) -> str:
    return ACTION_PHRASE.get(action, action.value.replace("_", " "))


_PH = re.compile(r"\{([a-z_]+)\}")


def fill(text: str, values: Mapping[str, str], lang: str = "en") -> str:
    """Replace {name} for every key in `values`; {city} defaults per language. Unknown names stay."""
    lang = norm_lang(lang)

    def sub(m: re.Match[str]) -> str:
        name = m.group(1)
        if name == "city" and not values.get("city"):
            return DEFAULT_CITY[lang]
        return str(values[name]) if name in values else m.group(0)

    return _PH.sub(sub, text)


def has_unfilled(text: str) -> bool:
    return bool(_PH.search(text))
