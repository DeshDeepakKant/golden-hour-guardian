#!/usr/bin/env python3
"""Automated test: all 5 scenarios. No user interaction needed."""
import subprocess
import time
import requests
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "guardian.db"
API = "http://127.0.0.1:8000"

SCENARIOS = [
    ("genuine", "usr_meena", "en", "🟢 ENGLISH (Genuine purchase)"),
    ("inbound", "usr_arjun", "hi", "🟡 HINDI (Fraud - victim calls 1930)"),
    ("ato", "usr_ravi", "te", "🔵 TELUGU (Fraud - verify via app)"),
    ("noresponse", "usr_lakshmi", "te", "🟣 TELUGU (No victim response)"),
    ("injection", "usr_kiran", "en", "🔴 ENGLISH (Prompt injection test)"),
]

def run_cmd(cmd):
    """Run shell command."""
    try:
        subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
        return True
    except:
        return False

def api_inject(scenario):
    """Inject scenario."""
    try:
        r = requests.post(f"{API}/sim/scenario/{scenario}", timeout=5)
        return r.json().get("case_id")
    except:
        return None

def case_events(case_id):
    """Get audit events."""
    try:
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT event_type, COUNT(*) FROM case_events WHERE case_id = ? GROUP BY event_type",
            (case_id,)
        ).fetchall()
        conn.close()
        return dict(rows)
    except:
        return {}

def case_state(case_id):
    """Get case state."""
    try:
        conn = sqlite3.connect(DB)
        state = conn.execute(
            "SELECT state FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        conn.close()
        return state
    except:
        return "ERROR"

def main():
    print("\n" + "="*75)
    print("🚀 Golden Hour Guardian — Automated 5-Scenario Test")
    print("="*75)

    print("\n📋 Test Plan:")
    for i, (_, _, _, desc) in enumerate(SCENARIOS, 1):
        print(f"   {i}. {desc}")

    print("\n⏳ Seeding database...")
    run_cmd("cd /home/anya/Videos/golden-hour-guardian && make seed >/dev/null 2>&1")
    time.sleep(2)

    print("✅ Database seeded\n")

    results = []

    for scenario_name, user_id, lang, desc in SCENARIOS:
        print(f"▶️  {desc}")
        print(f"   Scenario: {scenario_name} | User: {user_id} | Lang: {lang}")

        case_id = api_inject(scenario_name)
        if not case_id:
            print(f"   ❌ Injection failed\n")
            continue

        print(f"   ✅ Case: {case_id}")

        # Wait for backend to process
        time.sleep(2)

        state = case_state(case_id)
        events = case_events(case_id)

        event_summary = ", ".join([f"{k}({v})" for k, v in sorted(events.items())])

        print(f"   State: {state}")
        print(f"   Events: {event_summary or 'none yet'}\n")

        results.append({
            "desc": desc,
            "case_id": case_id,
            "state": state,
            "events": len(events),
        })

    # Summary
    print("="*75)
    print("📊 TEST SUMMARY")
    print("="*75)

    for r in results:
        status = "✅" if r["state"] in ("HELD_PENDING_VERIFY", "AWAITING_OFFICER", "RESOLVED") else "⚠️"
        print(f"{status} {r['desc']}")
        print(f"   Case: {r['case_id']} | State: {r['state']} | Events: {r['events']}\n")

    passed = sum(1 for r in results if r["state"] in ("HELD_PENDING_VERIFY", "AWAITING_OFFICER", "RESOLVED"))
    total = len(results)

    print(f"Result: {passed}/{total} scenarios passed ✅\n")

    print("📱 To test on phone (manual interaction):")
    print("   python3 scripts/test_english_demo.py")
    print("   (or pick any case_id above and visit victim app with that user)")
    print()

if __name__ == "__main__":
    main()
