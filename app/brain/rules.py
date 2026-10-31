"""Rules-first reply classification (en / hi / te / Hinglish / romanised Telugu).

Pure functions, no I/O. Victim text is data: instruction-like text never maps to YES_MINE/NOT_ME.
Order of precedence: injection > distress > refund > unsure > not_me > yes.
"""
from __future__ import annotations

import re
from typing import Optional

from app.contracts import ReplyIntent

INJECTION = [
    r"ignore (all |your |the |previous |above )*(rules|instructions|policy|policies|prompt)",
    r"disregard", r"override", r"system\s*:", r"assistant\s*:", r"developer\s*:",
    r"you are now", r"pretend", r"act as", r"jailbreak", r"new instructions?",
    r"i am (the |a )?(bank|branch|police|manager|officer|admin|ceo|rbi)",
    r"i'?m (the |a )?(bank|branch|police|manager|officer|admin)",
    r"(bank|branch) manager", r"mark (this|it|these|all) (as )?(genuine|safe|legit|verified|approved)",
    r"(release|unfreeze|unblock|approve) (the |my |all )?(hold|payments?|account|everything)",
    r"</?victim_text>", r"\bprompt\b", r"as an ai", r"reveal",
    r"सारे नियम भूल", r"निर्देश", r"బ్యాంకు మేనేజర్", r"నియమాలు పట్టించుకోవద్దు",
]
DISTRESS = [
    r"scared", r"afraid", r"crying", r"\bcry\b", r"panic", r"suicide", r"kill myself", r"help me",
    r"\bhelp\b", r"urgent", r"please save", r"i am dying", r"lost everything", r"no money left",
    r"bachao", r"bachaiye", r"bahut dar", r"\bdar lag", r"ro raha", r"ro rahi", r"ghabra",
    r"मदद", r"बचाओ", r"बचाइए", r"डर", r"रो रह", r"घबरा", r"परेशान",
    r"భయం", r"భయంగా", r"ఏడు", r"కాపాడండి", r"సహాయం", r"సాయం చేయండి",
    r"bhayam", r"kapadandi", r"sahayam",
]
REFUND = [
    r"refund", r"money back", r"get (my )?money", r"return (my )?money", r"reverse (the )?(payment|transaction|money)",
    r"paisa wapas", r"paise wapas", r"paisa lauta", r"wapas (do|chahiye|karo|milega)", r"mera paisa", r"mere paise",
    r"पैसा वापस", r"पैसे वापस", r"रिफंड", r"रकम वापस", r"वापस चाहिए", r"वापस दो",
    r"డబ్బులు వెనక్కి", r"డబ్బు వెనక్కి", r"రిఫండ్", r"వాపసు", r"డబ్బు తిరిగి",
    r"dabbulu venakki", r"dabbu venakki", r"refund kavali",
]
UNSURE = [
    r"not sure", r"don'?t know", r"do not know", r"no idea", r"maybe", r"confus", r"can'?t remember",
    r"cannot remember", r"don'?t remember", r"let me check", r"i think so",
    r"pata nahi", r"pata nahin", r"maloom nahi", r"yaad nahi", r"samajh nahi", r"shayad",
    r"पता नहीं", r"पता नही", r"याद नहीं", r"पक्का नहीं", r"शायद", r"समझ नहीं",
    r"తెలియదు", r"గుర్తు లేదు", r"బహుశా", r"తెలీదు",
    r"teliyadu", r"theliyadu", r"telidu", r"gurthu ledu", r"emo",
]
NOT_ME = [
    r"not me", r"wasn'?t me", r"was not me", r"it'?s not mine", r"not mine", r"didn'?t", r"did not",
    r"never (did|made|authori[sz]ed|sent)", r"\bi did ?n[o']t\b", r"unauthori[sz]ed", r"hacked", r"stolen",
    r"fraud", r"scam", r"cheat", r"^\s*no\b", r"\bno[,.! ]+(it|that|this|i)\b", r"not authori[sz]ed", r"don'?t recogni[sz]e",
    r"nahi kiya", r"nahin kiya", r"nahi ki\b", r"maine nahi", r"mai ne nahi", r"main ne nahi", r"mene nahi", r"meine nahi",
    r"mera nahi", r"meri taraf se nahi", r"nahi tha", r"dhokha", r"dhoka", r"thagi", r"^\s*(nahi|nahin|na)\b",
    r"मैंने नहीं", r"मैने नहीं", r"मैंने नही", r"नहीं किया", r"नही किया", r"मेरा नहीं", r"मैं नहीं", r"मेरी तरफ़? से नहीं",
    r"धोखा", r"ठगी", r"फ्रॉड", r"^\s*(नहीं|नही)(?![\u0900-\u097F])",
    r"నేను చేయలేదు", r"నేను చెయ్యలేదు", r"నేను కాదు", r"నాది కాదు", r"నేను చేయ లేదు", r"మోసం", r"^\s*(కాదు|లేదు)",
    r"nenu cheyaledu", r"nenu cheyyaledu", r"nenu kaadu", r"nenu kadu", r"nadi kaadu", r"mosam", r"^\s*(kaadu|kadu|ledu)\b",
]
YES_MINE = [
    r"^\s*(yes|yeah|yep|yup|ya|haan|han|haa|ha|hanji|ji haan|ok|okay)\b", r"\byes\b", r"it was me", r"it'?s me", r"that was me",
    r"\bi did\b", r"i made (it|them|these|the)", r"genuine", r"i authori[sz]ed",
    r"maine kiya", r"maine hi", r"mene kiya", r"meine kiya", r"main ne kiya", r"mera hi", r"sahi hai", r"theek hai",
    r"हाँ", r"हां", r"जी हाँ", r"जी हां", r"मैंने किया", r"मैंने ही", r"मैने ही", r"मैने किया", r"सही है", r"मेरा ही",
    r"అవును", r"నేనే", r"నేనే చేశాను", r"నేను చేశాను", r"నేను చేసాను", r"సరే",
    r"avunu", r"nenne", r"nenu chesanu", r"nenu chesaanu", r"nenu chesa",
]

_NON_ASCII = re.compile(r"[^\x00-\x7f]")


def _compile(pats: list[str]) -> list[re.Pattern[str]]:
    out = []
    for p in pats:
        # ASCII word-ish patterns that do not already anchor get letter boundaries.
        if not _NON_ASCII.search(p) and not p.startswith(("^", "\\b", "<", "(?")) :
            p = r"(?<![a-z])" + p
            if p[-1].isalpha():
                p += r"(?![a-z])"
        out.append(re.compile(p, re.I))
    return out


_RX = {name: _compile(pats) for name, pats in {
    "injection": INJECTION, "distress": DISTRESS, "refund": REFUND,
    "unsure": UNSURE, "not_me": NOT_ME, "yes": YES_MINE,
}.items()}


def normalize(text: str) -> str:
    t = (text or "").replace("’", "'").replace("‘", "'").lower()
    return re.sub(r"\s+", " ", t).strip()


def _hit(name: str, t: str) -> bool:
    return any(rx.search(t) for rx in _RX[name])


def is_instruction_like(text: str) -> bool:
    return _hit("injection", normalize(text))


def classify(text: str) -> Optional[tuple[ReplyIntent, float]]:
    """Return (intent, confidence) or None if the rules are inconclusive."""
    t = normalize(text)
    if not t:
        return ReplyIntent.OTHER, 0.0
    if _hit("injection", t):
        # Data, not a command. Refund wording -> officer; otherwise OTHER. Never YES_MINE/NOT_ME.
        return (ReplyIntent.ASKS_REFUND if _hit("refund", t) else ReplyIntent.OTHER), 0.5
    if _hit("distress", t):
        return ReplyIntent.DISTRESS, 0.85
    if _hit("refund", t):
        return ReplyIntent.ASKS_REFUND, 0.85
    if _hit("unsure", t):
        return ReplyIntent.UNSURE, 0.85
    spans = [m.span() for rx in _RX["not_me"] for m in rx.finditer(t)]
    nm = bool(spans)
    mask = [True] * len(t)
    for a, b in spans:                          # drop negated phrases so "I did not" is not a yes
        for i in range(a, b):
            mask[i] = False
    rest = "".join(c if keep else " " for c, keep in zip(t, mask))
    yes = _hit("yes", rest)
    if nm and yes:
        return ReplyIntent.UNSURE, 0.5   # contradictory: keep verifying, do not act
    if nm:
        return ReplyIntent.NOT_ME, 0.9
    if yes:
        return ReplyIntent.YES_MINE, 0.9
    return None
