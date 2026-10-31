"""Fixed victim-facing lines that are not LLM-worded (no amounts, IDs or promises beyond facts).
# TODO: native speaker check for hi and te lines.
"""
from __future__ import annotations

SAFETY = {
    "en": "Guardian will never ask for your OTP, PIN or password.",
    "hi": "Guardian आपसे कभी OTP, PIN या पासवर्ड नहीं माँगेगा।",
    "te": "Guardian మీ OTP, PIN లేదా పాస్‌వర్డ్ ఎప్పుడూ అడగదు.",
}

RETRY = {   # {amount} and {payee} are filled by code
    "en": "Just to be sure: did you make the payment of {amount} to {payee}? Please tap Yes or No.",
    "hi": "पक्का करने के लिए: क्या आपने {payee} को {amount} का भुगतान किया? कृपया हाँ या नहीं दबाएँ।",
    "te": "నిర్ధారించడానికి: మీరు {payee} కు {amount} చెల్లింపు చేశారా? దయచేసి అవును లేదా కాదు నొక్కండి.",
}

PROTECTED = {
    "outgoing_payments_paused": {
        "en": "Your outgoing payments are paused for now.",
        "hi": "आपके खाते से बाहर जाने वाले भुगतान अभी रोके गए हैं।",
        "te": "మీ ఖాతా నుండి వెళ్లే చెల్లింపులు ప్రస్తుతానికి నిలిపివేయబడ్డాయి.",
    },
    "device_signed_out": {
        "en": "The suspicious phone has been signed out.",
        "hi": "संदिग्ध फ़ोन को साइन-आउट कर दिया गया है।",
        "te": "అనుమానాస్పద ఫోన్ సైన్ అవుట్ చేయబడింది.",
    },
    "marketing_held": {
        "en": "Promotional messages are on hold while this case is open.",
        "hi": "यह मामला खुला रहने तक प्रचार संदेश रोके गए हैं।",
        "te": "ఈ కేసు తెరిచి ఉన్నంత వరకు ప్రచార సందేశాలు నిలిపివేయబడ్డాయి.",
    },
    "_review": {
        "en": "Our fraud team is reviewing your case. We will guide you on the next steps.",
        "hi": "हमारी फ़्रॉड टीम आपके मामले की समीक्षा कर रही है। हम आपको अगले कदम बताएँगे।",
        "te": "మా ఫ్రాడ్ బృందం మీ కేసును పరిశీలిస్తోంది. తదుపరి దశలను మేము మీకు చెబుతాము.",
    },
}

RELEASED = {
    "en": "Thank you. Your payments are back to normal.",
    "hi": "धन्यवाद। आपके भुगतान सामान्य हो गए हैं।",
    "te": "ధన్యవాదాలు. మీ చెల్లింపులు సాధారణ స్థితికి వచ్చాయి.",
}

# How to recognise the genuine caller (REVIEW S4): appended to every close / callback message.
CALLER_CHECK = {
    "en": "Our caller will never ask for OTP, PIN, to install an app, or to move money. "
          "If unsure, hang up and call 1930.",
    "hi": "हमारा कॉल करने वाला कभी OTP, PIN, कोई ऐप इंस्टॉल करने या पैसे ट्रांसफ़र करने को नहीं कहेगा। "
          "शक हो तो फ़ोन काटें और 1930 पर कॉल करें।",
    "te": "మా నుండి కాల్ చేసేవారు ఎప్పుడూ OTP, PIN, ఏదైనా యాప్ ఇన్‌స్టాల్ చేయమని లేదా డబ్బు బదిలీ చేయమని అడగరు. "
          "సందేహం ఉంటే, కాల్ కట్ చేసి 1930 కు కాల్ చేయండి.",
}

CALLBACK = {
    "en": "Thank you. A member of our fraud team will call you shortly. " + CALLER_CHECK["en"],
    "hi": "धन्यवाद। हमारी फ़्रॉड टीम का एक सदस्य जल्द ही आपको कॉल करेगा। " + CALLER_CHECK["hi"],
    "te": "ధన్యవాదాలు. మా ఫ్రాడ్ బృంద సభ్యుడు త్వరలో మీకు కాల్ చేస్తారు. " + CALLER_CHECK["te"],
}

DONE = {
    "en": "Thank you. Your report details are saved. Our fraud team is reviewing your case. " + CALLER_CHECK["en"],
    "hi": "धन्यवाद। आपकी रिपोर्ट की जानकारी सहेज ली गई है। हमारी फ़्रॉड टीम आपके मामले की समीक्षा कर रही है। "
          + CALLER_CHECK["hi"],
    "te": "ధన్యవాదాలు. మీ రిపోర్ట్ వివరాలు సేవ్ చేయబడ్డాయి. మా ఫ్రాడ్ బృందం మీ కేసును పరిశీలిస్తోంది. "
          + CALLER_CHECK["te"],
}

# Code-built trigger notes appended to decision rationales (facts from code, not the LLM).
TRIGGERS = {
    "ASKS_REFUND": "Trigger: the customer asked about a refund. No refund was promised or actioned.",
    "DISTRESS": "Trigger: the customer sounded distressed. Please call with a calm script.",
    "OTHER": "Trigger: the customer's reply could not be understood as yes or no.",
    "UNSURE": "Trigger: the customer was unsure twice.",
    "NO_RESPONSE": "Trigger: no reply to the verification within the time limit.",
    "UNTRUSTED_YES": "Trigger: the customer said it was them, but the channel is not trusted (recent SIM change). "
                     "The hold was not released automatically.",
}


def pick(table: dict[str, str], lang: str) -> str:
    return table.get(lang) or table["en"]
