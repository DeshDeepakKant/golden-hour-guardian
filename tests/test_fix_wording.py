"""REVIEW fixes S1 (guard gaps), S4 (genuine-caller line), S6 (narrative city/time range)."""
import os

os.environ.setdefault("GUARDIAN_LLM_MODEL", "none")

import pytest

from app import texts
from app.brain import facts as F, guard, templates as T
from app.brain.api import brain
from app.brain.samples import sample_pack

# REVIEW S1 probes: each passed the old guard.
S1_PROBES = [
    ("आपका पैसा वापस आ जाएगा।", "hi"),
    ("Your money will come back soon.", "en"),
    ("We have recovered your money.", "en"),
    ("Call our desk on 98 76 54 32 10 now.", "en"),
]


@pytest.mark.parametrize("text,lang", S1_PROBES + [
    ("Your account has been blocked.", "en"),
    ("Call 98-76-54-32-10.", "en"),
    ("Call 1930 or 98 76 54 32 10.", "en"),
])
def test_s1_probes_rejected(text, lang):
    ok, reason = guard.check(text, lang)
    assert ok is False and reason, text


@pytest.mark.parametrize("text,lang", [
    ("Between {first} and {time}, {count} payments of {amount} went to {payees}.", "en"),
    ("Call 1930 or open cybercrime.gov.in and choose 'Report financial fraud'.", "en"),
    ("1930 पर कॉल करें या cybercrime.gov.in खोलें।", "hi"),
    ("{count} payments of {amount} at {time}, 1930 helpline.", "en"),
])
def test_s1_legit_text_still_passes(text, lang):
    assert guard.check(text, lang) == (True, ""), text


@pytest.mark.parametrize("lang", ["en", "hi", "te"])
def test_s4_close_messages_explain_genuine_caller(lang):
    for table in (texts.CALLBACK, texts.DONE):
        msg = table[lang]
        assert "OTP" in msg and "PIN" in msg and "1930" in msg
        assert msg.endswith(texts.CALLER_CHECK[lang])


def test_s6_city_from_first_untrusted_device_and_time_range():
    pack = sample_pack().model_copy(update={"device_timeline": [
        {"device_id": "d_home", "geo_city": "Hyderabad", "trusted": True, "first_seen": "2026-01-01T00:00:00+00:00"},
        {"device_id": "d_late", "geo_city": "Kolkata", "trusted": False, "first_seen": "2026-03-14T09:00:00+00:00"},
        {"device_id": "d_new", "geo_city": "Jamtara", "trusted": False, "first_seen": "2026-03-14T08:30:00+00:00"},
    ]})
    f = F.pack_facts(pack)
    assert f.values["city"] == "Jamtara"
    assert f.values["first"] == "02:16 PM" and f.values["time"] == "02:18 PM"
    _, en = brain.evidence_narratives(pack, "en")
    assert en.startswith("Between 02:16 PM and 02:18 PM,") and "Jamtara" in en


def test_s6_only_trusted_device_uses_default_city():
    pack = sample_pack().model_copy(update={"device_timeline": [
        {"device_id": "d_home", "geo_city": "Hyderabad", "trusted": True, "first_seen": "2026-01-01T00:00:00+00:00"}]})
    assert F.pack_facts(pack).values["city"] == ""
    for lang in ("en", "hi", "te"):
        victim, _ = brain.evidence_narratives(pack, lang)
        assert "Hyderabad" not in victim and T.DEFAULT_CITY[lang] in victim
