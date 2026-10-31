"""Latest victim prompt per user (served by GET /victim/{user_id}/pending). In-memory by design."""
from __future__ import annotations

from typing import Any, Optional

_PENDING: dict[str, dict[str, Any]] = {}


def set_prompt(user_id: str, prompt: dict[str, Any]) -> None:
    _PENDING[user_id] = prompt


def get_prompt(user_id: str) -> Optional[dict[str, Any]]:
    return _PENDING.get(user_id)


def clear(user_id: str) -> None:
    _PENDING.pop(user_id, None)


def reset() -> None:
    _PENDING.clear()
