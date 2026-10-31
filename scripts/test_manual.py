#!/usr/bin/env python3
"""Manual end-to-end test: script automates server, you test victim app on phone."""
import subprocess
import time
import requests
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
DB = ROOT / "app" / "db.sqlite"
API = "http://127.0.0.1:8000"

SCENARIOS = {
    "1": ("genuine", "usr_meena", "en", "English (genuine purchase)"),
    "2": ("inbound", "usr_arjun", "hi", "Hindi (fraud - victim calls 1930)"),
    "3": ("ato", "usr_ravi", "te", "Telugu (fraud - verify via app)"),
    "4": ("noresponse", "usr_lakshmi", "te", "Telugu (no victim response)"),
    "5": ("injection", "usr_kiran", "en", "English (prompt injection test)"),
}

def run(cmd, shell=False):
    """Run command, return output."""
    try:
        result = subprocess.run(
            cmd if shell else cmd.split(),
            capture_output=True,
            text=True,
            shell=shell,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception as e:
        print(f"⚠️  Command failed: {e}")
        return None

def api_health():
    """Check if server is running."""
    try:
        r = requests.get(f"{API}/health", timeout=2)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def api_inject(scenario_name):
    """Inject a scenario, return case_id."""
    try:
        r = requests.post(f"{API}/sim/scenario/{scenario_name}", timeout=5)
        data = r.json()
        return data.get("case_id")
    except Exception as e:
        print(f"⚠️  Inject failed: {e}")
        return None

def case_state(case_id):
    """Fetch case state from DB."""
    try:
        conn = sqlite3.connect(DB)
        row = conn.execute(
            "SELECT case_id, state, created_at, updated_at FROM cases WHERE case_id = ?",
            (case_id,)
        ).fetchone()
        conn.close()
        return row
    except:
        return None

def case_events(case_id):
    """Fetch audit events for case."""
    try:
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT event_type, actor, payload, created_at FROM case_events WHERE case_id = ? ORDER BY created_at",
            (case_id,)
        ).fetchall()
        conn.close()
        return rows
    except:
        return []

def case_decision(case_id):
    """Fetch decision for case."""
    try:
        conn = sqlite3.connect(DB)
        row = conn.execute(
            "SELECT decision_id, fraud_classification, rationale FROM decisions WHERE case_id = ?",
            (case_id,)
        ).fetchone()
        conn.close()
        return row
    except:
        return None

def print_case_summary(case_id):
    """Print case state and events."""
    state = case_state(case_id)
    if not state:
        print(f"❌ Case {case_id} not found")
        return

    print(f"\n{'='*70}")
    print(f"📋 Case: {state[0]}")
    print(f"   State: {state[1]}")
    print(f"   Created: {state[2]} | Updated: {state[3]}")
    print(f"{'='*70}")

    events = case_events(case_id)
    if events:
        print(f"\n📌 Audit Trail ({len(events)} events):")
        for event_type, actor, payload, ts in events:
            print(f"   [{ts}] {event_type} (by {actor})")
            if payload:
                print(f"      → {payload[:100]}")

    decision = case_decision(case_id)
    if decision:
        print(f"\n✅ Decision: {decision[1]}")
        print(f"   Rationale: {decision[2][:100]}...")
    else:
        print(f"\n⏳ Decision: Pending (awaiting officer approval)")

    print()

def main():
    print("\n🚀 Golden Hour Guardian — Manual E2E Test")
    print(f"   API: {API}")
    print(f"   DB:  {DB}\n")

    # Check server
    print("⏳ Checking server...")
    health = api_health()
    if not health:
        print("❌ Server not running. Start with:")
        print("   make demo-run")
        sys.exit(1)
    print(f"✅ Server is {health.get('llm', 'unknown')}\n")

    while True:
        print("┌─ Scenario Menu ─────────────────────────────────────────────┐")
        for key, (scenario, user_id, lang, desc) in SCENARIOS.items():
            print(f"│  {key} → {desc}")
        print("│  0 → Exit")
        print("└─────────────────────────────────────────────────────────────┘")

        choice = input("\nSelect scenario (0-5): ").strip()
        if choice == "0":
            print("✋ Goodbye!")
            break
        if choice not in SCENARIOS:
            print("❌ Invalid choice")
            continue

        scenario_name, user_id, lang, desc = SCENARIOS[choice]
        print(f"\n▶️  Injecting: {desc}")
        print(f"   Scenario: {scenario_name} | User: {user_id} ({lang})\n")

        case_id = api_inject(scenario_name)
        if not case_id:
            print("❌ Injection failed")
            continue
        print(f"✅ Case created: {case_id}\n")

        print("📱 Instructions for Phone:")
        print(f"   1. Open: http://127.0.0.1:8000/victim/?user={user_id}")
        print(f"   2. Tap 'Enable security alerts'")
        print(f"   3. Read the {lang.upper()} prompt + English companion")
        print(f"   4. Tap your response (Yes/No/Unsure)")
        print(f"   5. See 'Protected' or 'All clear' screen")
        print(f"   6. Return here and press Enter\n")

        input("Press Enter when victim app interaction is complete...")

        print(f"\n⏳ Waiting 2 sec for backend to process...")
        time.sleep(2)

        print_case_summary(case_id)

        print("📊 Next Steps:")
        print(f"   Officer: http://127.0.0.1:8000/officer")
        print(f"   Search for case {case_id[:8]}...")
        print(f"   Approve/deny the decision\n")

        again = input("Test another scenario? (y/n): ").strip().lower()
        if again != "y":
            break

    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
