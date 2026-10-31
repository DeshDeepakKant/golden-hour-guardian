import os

# Must be set before app modules are imported (config reads env at import).
os.environ.setdefault("GUARDIAN_LLM_MODEL", "none")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GUARDIAN_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("GUARDIAN_LLM_MODEL", "none")
    from mocks import seed

    seed.main(["--reset"])
    from app.main import app

    with TestClient(app) as c:
        yield c
