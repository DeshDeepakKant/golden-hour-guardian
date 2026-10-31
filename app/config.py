"""Load the three YAML config files once into plain dicts.

Env overrides:
  GUARDIAN_DB         -> SETTINGS["app"]["db_path"]
  GUARDIAN_LLM_MODEL  -> SETTINGS["llm"]["model"]   (tests set it to "none")
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def _load(name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


SETTINGS: dict[str, Any] = _load("settings.yaml")
POLICY: dict[str, Any] = _load("policy.yaml")
BASELINE: dict[str, Any] = _load("baseline.yaml")

if os.environ.get("GUARDIAN_DB"):
    SETTINGS["app"]["db_path"] = os.environ["GUARDIAN_DB"]
if os.environ.get("GUARDIAN_LLM_MODEL"):
    SETTINGS["llm"]["model"] = os.environ["GUARDIAN_LLM_MODEL"]


def db_path() -> Path:
    """Resolved DB path. GUARDIAN_DB is re-read at call time so tests can point at a tmp file."""
    p = Path(os.environ.get("GUARDIAN_DB") or SETTINGS["app"]["db_path"])
    return p if p.is_absolute() else ROOT / p
