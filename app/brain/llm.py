"""Claude API client (Anthropic Python SDK). Returns parsed JSON dicts or None; never raises.

If settings llm.model == "none" the network is never touched (tests, offline demos).
Credentials come from the environment (ANTHROPIC_API_KEY, or an `ant auth login` profile).
No key / no network / timeout / refusal / bad JSON -> None, and the caller uses templates.
Settings are read at call time so tests / env overrides take effect.
"""
from __future__ import annotations

import json
import threading
import time
from typing import Any, Optional

from app.config import SETTINGS

_UP_TTL_S = 60.0     # cache a successful health check
_DOWN_TTL_S = 15.0   # retry a failed one sooner
_UNSUPPORTED = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "minItems", "maxItems",
                "minLength", "maxLength", "multipleOf")


def _cfg() -> dict[str, Any]:
    return SETTINGS.get("llm", {})


def extract_json(raw: str) -> Optional[dict[str, Any]]:
    """Return the first JSON object found in `raw` (structured outputs normally give pure JSON)."""
    if not raw:
        return None
    dec = json.JSONDecoder()
    i = raw.find("{")
    while i != -1:
        try:
            obj, _ = dec.raw_decode(raw[i:])
            if isinstance(obj, dict):
                return obj
        except ValueError:
            pass
        i = raw.find("{", i + 1)
    return None


def strict_schema(schema: Any) -> Any:
    """Make a JSON schema acceptable to structured outputs: closed objects, and none of the
    unsupported bounds (the API 400s on minItems > 1 and on numeric min/max). Callers already
    validate array lengths and clamp numbers in code."""
    if isinstance(schema, list):
        return [strict_schema(s) for s in schema]
    if not isinstance(schema, dict):
        return schema
    out = {k: strict_schema(v) for k, v in schema.items() if k not in _UNSUPPORTED}
    if out.get("type") == "object":
        out.setdefault("additionalProperties", False)
    return out


class ClaudeClient:
    def __init__(self) -> None:
        self._client: Any = None
        self._lock = threading.Lock()
        self._up: Optional[bool] = None
        self._up_at: float = 0.0

    # -- config helpers ---------------------------------------------------
    @property
    def model(self) -> str:
        return str(_cfg().get("model", "none"))

    @property
    def enabled(self) -> bool:
        return self.model.lower() != "none"

    def _get_client(self) -> Any:
        with self._lock:
            if self._client is None:
                import anthropic  # imported lazily: tests with model "none" never load it
                self._client = anthropic.Anthropic(max_retries=0)
            return self._client

    # -- health -----------------------------------------------------------
    def is_up(self) -> bool:
        """True if the model is enabled and the API accepts our credentials (cached)."""
        if not self.enabled:
            return False
        now = time.monotonic()
        if self._up is not None and now - self._up_at < (_UP_TTL_S if self._up else _DOWN_TTL_S):
            return self._up
        try:
            self._get_client().with_options(timeout=3.0).models.retrieve(self.model)
            self._up = True
        except Exception:
            self._up = False
        self._up_at = now
        return self._up

    def _mark_down(self) -> None:
        self._up, self._up_at = False, time.monotonic()

    # -- warm-up ----------------------------------------------------------
    def warm(self) -> bool:
        """Open the HTTPS connection and validate the key once at startup. Never raises."""
        try:
            return self.is_up()
        except Exception:
            return False

    # -- chat -------------------------------------------------------------
    def chat_json(self, system: str, user: str, schema: dict[str, Any]) -> Optional[dict[str, Any]]:
        """One structured call. Returns the parsed JSON object or None on any problem."""
        if not self.enabled or not self.is_up():
            return None
        cfg = _cfg()
        try:
            import anthropic
            resp = self._get_client().with_options(timeout=float(cfg.get("timeout_s", 8))).messages.create(
                model=self.model,
                max_tokens=int(cfg.get("max_tokens", 2000)),
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={
                    "effort": str(cfg.get("effort", "low")),
                    "format": {"type": "json_schema", "schema": strict_schema(schema)},
                },
            )
        except anthropic.AuthenticationError:
            self._mark_down()
            return None
        except anthropic.APIConnectionError:  # includes APITimeoutError
            return None
        except Exception:
            return None
        if resp.stop_reason != "end_turn":  # refusal, max_tokens, ... -> template
            return None
        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            out = json.loads(text)
            return out if isinstance(out, dict) else None
        except ValueError:
            return extract_json(text)


llm = ClaudeClient()
