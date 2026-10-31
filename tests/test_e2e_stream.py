"""E2E: GET /events (SSE) delivers a `case` message after a scenario is launched.

TestClient buffers whole responses, so it cannot read an open SSE stream. This test runs uvicorn on
an ephemeral 127.0.0.1 port in a background thread (never 8000) and reads the stream over HTTP with a
read timeout.
"""
import json
import socket
import threading
import time

import httpx
import pytest
import uvicorn


@pytest.fixture
def live_server(tmp_path, monkeypatch):
    monkeypatch.setenv("GUARDIAN_DB", str(tmp_path / "stream.db"))
    monkeypatch.setenv("GUARDIAN_LLM_MODEL", "none")
    from mocks import seed

    seed.main(["--reset"])
    from app.main import app

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="on"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    end = time.time() + 15
    while not server.started and time.time() < end:
        time.sleep(0.05)
    assert server.started, "uvicorn did not start"
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)


def test_events_stream_yields_case_message_after_scenario(live_server):
    launched = None
    case_msg = None
    kinds_seen = set()
    with httpx.Client(base_url=live_server, timeout=httpx.Timeout(10.0)) as client:
        with client.stream("GET", "/events") as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            for line in resp.iter_lines():
                if line.startswith(": connected") and launched is None:
                    r = client.post("/sim/scenario/genuine")
                    assert r.status_code == 200, r.text
                    launched = r.json()["case_id"]
                elif line.startswith("data:") and launched is not None:
                    msg = json.loads(line[len("data:"):].strip())
                    kinds_seen.add(msg["kind"])
                    if msg["kind"] == "case" and msg["data"].get("case_id") == launched:
                        case_msg = msg
                        break
    assert launched is not None, "never saw the connected comment"
    assert case_msg is not None, f"no case message for {launched}; kinds seen: {sorted(kinds_seen)}"
    assert case_msg["data"]["user_id"] == "usr_meena"
    assert "case" in kinds_seen
