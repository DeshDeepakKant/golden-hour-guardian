"""Claude API client (app/brain/llm.py): request shape, fallbacks, no-key behaviour.
No real network: the SDK client is replaced by a fake, or credentials are absent."""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from app.brain import llm as llm_mod
from app.config import SETTINGS


class FakeMessages:
    def __init__(self, resp=None, exc=None):
        self.resp, self.exc, self.calls = resp, exc, []

    def create(self, **kw):
        self.calls.append(kw)
        if self.exc:
            raise self.exc
        return self.resp


class FakeClient:
    def __init__(self, messages, models_ok=True):
        self.messages = messages
        self.models = SimpleNamespace(retrieve=self._retrieve)
        self._models_ok = models_ok
        self.timeouts = []

    def _retrieve(self, model):
        if not self._models_ok:
            raise RuntimeError("auth")
        return SimpleNamespace(id=model)

    def with_options(self, timeout=None, **_):
        self.timeouts.append(timeout)
        return self


def _resp(text, stop="end_turn"):
    return SimpleNamespace(stop_reason=stop, content=[
        SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)])


@pytest.fixture
def claude(monkeypatch):
    monkeypatch.setitem(SETTINGS["llm"], "model", "claude-opus-5-5")
    c = llm_mod.ClaudeClient()
    return c


SCHEMA = {"type": "object", "properties": {"text": {"type": "string"},
                                           "confidence": {"type": "number", "minimum": 0, "maximum": 1}},
          "required": ["text", "confidence"]}


def test_strict_schema_drops_array_bounds_the_api_rejects():
    # Live API: "For 'array' type, 'minItems' values other than 0 or 1 are not supported" (HTTP 400)
    s = llm_mod.strict_schema({"type": "object", "required": ["lines"], "properties": {
        "lines": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 3}}})
    assert "minItems" not in s["properties"]["lines"] and "maxItems" not in s["properties"]["lines"]


def test_every_brain_schema_is_api_safe():
    """All schemas the brain sends must survive strict_schema with no unsupported keywords left."""
    import inspect
    import re
    from app.brain import api
    src = inspect.getsource(api)
    assert "minItems" in src                       # the brain does declare bounds ...
    from app.brain.llm import _UNSUPPORTED         # ... and strict_schema strips every unsupported keyword

    def walk(x):
        if isinstance(x, dict):
            assert not set(x) & set(_UNSUPPORTED), x
            [walk(v) for v in x.values()]
        elif isinstance(x, list):
            [walk(v) for v in x]
    walk(llm_mod.strict_schema(api._obj(lines={"type": "array", "items": api._STR, "minItems": 2, "maxItems": 3},
                                        steps={"type": "array", "items": api._STR, "minItems": 4, "maxItems": 6},
                                        confidence={"type": "number", "minimum": 0, "maximum": 1})))


def test_strict_schema_closes_objects_and_drops_bounds():
    s = llm_mod.strict_schema(SCHEMA)
    assert s["additionalProperties"] is False
    assert "minimum" not in s["properties"]["confidence"]
    assert SCHEMA["properties"]["confidence"]["minimum"] == 0  # input not mutated


def test_request_shape_and_json_parse(claude, monkeypatch):
    msgs = FakeMessages(_resp('{"text": "ok {amount}", "confidence": 0.4}'))
    fake = FakeClient(msgs)
    monkeypatch.setattr(claude, "_get_client", lambda: fake)
    out = claude.chat_json("sys", "user", SCHEMA)
    assert out == {"text": "ok {amount}", "confidence": 0.4}
    kw = msgs.calls[0]
    assert kw["model"] == "claude-opus-5-5"
    assert kw["system"] == "sys" and kw["messages"] == [{"role": "user", "content": "user"}]
    assert kw["output_config"]["format"]["type"] == "json_schema"
    assert kw["output_config"]["format"]["schema"]["additionalProperties"] is False
    assert kw["output_config"]["effort"] == "low"
    assert "temperature" not in kw and "thinking" not in kw
    assert fake.timeouts[-1] == float(SETTINGS["llm"]["timeout_s"])


@pytest.mark.parametrize("resp", [_resp('{"text": "x"}', stop="refusal"),
                                  _resp('{"text": "x"', stop="max_tokens"),
                                  _resp("not json at all")])
def test_refusal_truncation_and_garbage_give_none(claude, monkeypatch, resp):
    monkeypatch.setattr(claude, "_get_client", lambda: FakeClient(FakeMessages(resp)))
    assert claude.chat_json("s", "u", SCHEMA) is None


def test_timeout_gives_none(claude, monkeypatch):
    import anthropic
    import httpx2
    exc = anthropic.APITimeoutError(request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"))
    monkeypatch.setattr(claude, "_get_client", lambda: FakeClient(FakeMessages(exc=exc)))
    assert claude.chat_json("s", "u", SCHEMA) is None


def test_bad_credentials_mean_down_and_no_message_call(claude, monkeypatch):
    msgs = FakeMessages(_resp('{"text": "x"}'))
    monkeypatch.setattr(claude, "_get_client", lambda: FakeClient(msgs, models_ok=False))
    assert claude.is_up() is False
    assert claude.chat_json("s", "u", SCHEMA) is None
    assert msgs.calls == []


def test_no_key_falls_back_fast(claude, monkeypatch, tmp_path):
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))          # no `ant` profile on disk either
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    t0 = time.perf_counter()
    assert claude.warm() is False
    assert claude.chat_json("s", "u", SCHEMA) is None
    assert time.perf_counter() - t0 < 5.0


def test_model_none_never_builds_client(monkeypatch):
    monkeypatch.setitem(SETTINGS["llm"], "model", "none")
    c = llm_mod.ClaudeClient()
    monkeypatch.setattr(c, "_get_client", lambda: (_ for _ in ()).throw(AssertionError("client built")))
    assert c.is_up() is False and c.chat_json("s", "u", SCHEMA) is None


def test_classify_sends_no_digits_to_api(monkeypatch):
    from app.brain import api
    seen = []

    class Spy:
        def is_up(self):
            return True

        def chat_json(self, system, user, schema):
            seen.append(user)
            return {"intent": "UNSURE", "confidence": 0.5}
    monkeypatch.setattr(api, "llm", Spy())
    api.Brain().classify_reply("my brother used the phone, number was 4 5 6 7 8 9 or 98765 43210", "en")
    assert seen, "classifier should have consulted the API for an unclear reply"
    assert not any(ch.isdigit() for ch in seen[0])
