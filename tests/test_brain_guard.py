import os

os.environ.setdefault("GUARDIAN_LLM_MODEL", "none")

import pytest

from app.brain import guard


@pytest.mark.parametrize("text", [
    "Please share your OTP to continue.",
    "Send us your PIN now.",
    "Tell us your password.",
    "Share the code you received.",
    "A refund is guaranteed.",
    "We will refund you today.",
    "Your money will be returned soon.",
    "Click this link to verify.",
    "Pay a fee to unlock your account.",
    "This is the police department here.",
    "Visit http://evil.example.com now",
    "Go to bank-help.in to verify",
    "Call 9876543210 now",
    "Your balance is 12000",
    "Use {secret} please",
    "",
    "x" * 700,
])
def test_guard_blocks(text):
    ok, reason = guard.check(text)
    assert not ok and reason


def test_guard_allows_safe_text():
    for t in ["Did you make {count} payments of {amount} at {time}?",
              "Call 1930 or open cybercrime.gov.in and choose 'Report financial fraud'.",
              "Visit https://cybercrime.gov.in/ to report."]:
        assert guard.check(t) == (True, ""), t


def test_guard_script_check():
    assert guard.check("Please answer this question quickly", "hi")[0] is False
    assert guard.check("क्या ये भुगतान आपने किए हैं?", "hi")[0] is True
    assert guard.check("ఈ చెల్లింపులు మీరు చేశారా?", "te")[0] is True
