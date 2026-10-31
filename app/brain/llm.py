"""Ollama client (sync, httpx). Returns parsed JSON dicts or None; never raises.

If settings llm.model == "none" the network is never touched.
Settings are read at call time so tests / env overrides take effect.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Optional

import httpx

from app.config import SETTINGS

_THINK_RE = re.compile(r"<think>.*?</think>", re.S | re.I)


def _cfg() -> dict[str, Any]:
    return SETTINGS.get("llm", {})


def extract_json(raw: str) -> Optional[dict[str, Any]]:
    """Strip reasoning text and return the first JSON object found in `raw`."""
    if not raw:
        return None
    raw = _THINK_RE.sub("", raw)
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


class OllamaClient:
    def __init__(self) -> None:
        self._up: Optional[bool] = None
        self._up_at: float = 0.0

    # -- config helpers ---------------------------------------------------
    @property
    def model(self) -> str:
        return str(_cfg().get("model", "none"))

    @property
    def enabled(self) -> bool:
        return self.model.lower() != "none"

    # -- health -----------------------------------------------------------
    def is_up(self) -> bool:
        """True if the model is enabled and the Ollama server answers /api/tags (cached 10 s)."""
        if not self.enabled:
            return False
        now = time.monotonic()
        if self._up is not None and now - self._up_at < 10:
            return self._up
        try:
            r = httpx.get(f"{_cfg().get('base_url', 'http://127.0.0.1:11434')}/api/tags", timeout=2.0)
            self._up = r.status_code == 200
        except Exception:
            self._up = False
        self._up_at = now
        return self._up

    def _mark_down(self) -> None:
        self._up, self._up_at = False, time.monotonic()

    # -- warm-up ----------------------------------------------------------
    def warm(self) -> bool:
        """Load the model into memory with one tiny chat (+ keep_alive). Never raises."""
        if not self.enabled:
            return False
        try:
            if not self.is_up():
                return False
            cfg = _cfg()
            r = httpx.post(f"{cfg.get('base_url', 'http://127.0.0.1:11434')}/api/chat", json={
                "model": self.model, "messages": [{"role": "user", "content": "ok"}], "stream": False,
                "keep_alive": cfg.get("keep_alive", "30m"), "options": {"num_predict": 1},
            }, timeout=float(cfg.get("warm_timeout_s", 60)))
            return r.status_code == 200
        except Exception:
            return False

    # -- chat -------------------------------------------------------------
    def chat_json(self, system: str, user: str, schema: dict[str, Any]) -> Optional[dict[str, Any]]:
        """One structured chat call. Returns the parsed JSON object or None on any problem."""
        if not self.enabled or not self.is_up():
            return None
        cfg = _cfg()
        timeout = float(cfg.get("timeout_s", 8))
        deadline = time.monotonic() + timeout
        url = f"{cfg.get('base_url', 'http://127.0.0.1:11434')}/api/chat"
        send_think = True
        fmt: Any = schema
        for _ in range(3):  # initial + up to 2 compatibility retries
            remaining = deadline - time.monotonic()
            if remaining <= 0.2:
                return None
            body: dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "format": fmt,
                "stream": False,
                "options": {
                    "temperature": cfg.get("temperature", 0.2),
                    "num_predict": cfg.get("max_tokens", 300),
                },
            }
            if send_think:
                body["think"] = bool(cfg.get("think", False))
            try:
                r = httpx.post(url, json=body, timeout=remaining)
            except httpx.ConnectError:
                self._mark_down()
                return None
            except Exception:
                return None
            if r.status_code == 400:
                if send_think:
                    send_think = False        # server rejects `think`: retry without it
                    continue
                if not isinstance(fmt, str):
                    fmt = "json"              # server rejects schema format: plain json mode
                    continue
                return None
            if r.status_code != 200:
                return None
            try:
                content = r.json().get("message", {}).get("content", "")
            except Exception:
                return None
            return extract_json(content)
        return None


llm = OllamaClient()
