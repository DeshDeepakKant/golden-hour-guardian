import os

os.environ.setdefault("GUARDIAN_LLM_MODEL", "none")

import pytest

from app.brain import guard, templates as T
from app.brain.api import brain
from app.brain.samples import sample_case, sample_pack, sample_txns
from app.contracts import Action, SignalCode

LANGS = ["en", "hi", "te"]


@pytest.mark.parametrize("lang", LANGS)
def test_templates_exist_for_every_method_and_lang(lang):
    assert lang in T.SAFETY_LINE and lang in T.VERIFY_WHAT and lang in T.VERIFY_WHAT_NEWDEV
    assert lang in T.VERIFY_QUESTION and lang in T.NARRATIVE and lang in T.DEFAULT_CITY
    assert 4 <= len(T.NCRP_STEPS[lang]) <= 6
    for code in SignalCode:
        assert code in T.SIGNAL_TEXT[lang]
    assert T.EXPLAIN_RISK and T.RATIONALE


@pytest.mark.parametrize("lang", LANGS)
def test_every_method_returns_filled_text(lang):
    case, txns, pack = sample_case(lang), sample_txns(), sample_pack()
    msgs = brain.verification_messages(case, txns)
    assert 2 <= len(msgs) <= 4 and msgs[-1] == T.SAFETY_LINE[lang]
    assert any("₹24,999" in m for m in msgs) and any("3" in m for m in msgs)
    victim, en = brain.evidence_narratives(pack, lang)
    steps = brain.ncrp_guidance(pack, lang)
    assert "₹24,999" in victim and "₹24,999" in en
    outs = msgs + [victim, en, brain.explain_risk(case, txns), *steps]
    outs += [brain.decision_rationale(case, a) for a in Action]
    for o in outs:
        assert not T.has_unfilled(o), o


@pytest.mark.parametrize("lang", LANGS)
def test_templates_pass_guard_except_fixed_safety_line(lang):
    # Check the unfilled templates: filled ones legitimately contain code-supplied amounts.
    raw = [T.VERIFY_WHAT[lang], T.VERIFY_WHAT_NEWDEV[lang], T.VERIFY_QUESTION[lang],
           T.NARRATIVE[lang].replace("{signals}", "x"), *T.NCRP_STEPS[lang]]
    for r in raw:
        ok, why = guard.check(r.replace("{signals}", "x"), lang)
        assert ok, (r, why)


def test_hindi_telugu_are_in_native_script():
    assert any("ऀ" <= c <= "ॿ" for c in T.VERIFY_QUESTION["hi"])
    assert any("ఀ" <= c <= "౿" for c in T.VERIFY_QUESTION["te"])


def test_amount_formatting_indian_grouping():
    from app.brain.facts import format_inr
    assert format_inr(2_499_900) == "₹24,999"
    assert format_inr(12_345_600) == "₹1,23,456"
    assert format_inr(50) == "₹0.50"
