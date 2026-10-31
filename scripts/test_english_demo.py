#!/usr/bin/env python3
"""Demo test: English scenario (genuine). You interact on phone, script shows results."""
import subprocess
import time
import requests
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "app" / "db.sqlite"
API = "http://127.0.0.1:8000"

def api_inject(scenario):
    """Inject scenario, return case_id."""
    try:
        r = requests.post(f"{API}/sim/scenario/{scenario}", timeout=5)
        return r.json().get("case_id")
    except Exception as e:
        print(f"❌ Inject failed: {e}")
        return None

def case_state(case_id):
    """Fetch case from DB."""
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
    """Fetch audit events."""
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
    """Fetch decision."""
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

def main():
    print("\n" + "="*70)
    print("🚀 Golden Hour Guardian — English Demo Test")
    print("="*70)

    print("\n⏳ Injecting GENUINE scenario (English, usr_meena)...")
    case_id = api_inject("genuine")
    if not case_id:
        return
    print(f"✅ Case created: {case_id}\n")

    print("📱 ON YOUR PHONE:")
    print("━" * 70)
    print(f"   1️⃣  Open in Chrome browser:")
    print(f"      http://127.0.0.1:8000/victim/?user=usr_meena")
    print(f"")
    print(f"   2️⃣  Tap 'Tap to enable security alerts' button")
    print(f"")
    print(f"   3️⃣  Wait 2-3 seconds, you'll see:")
    print(f"      ✓ English security check prompt")
    print(f"      ✓ Amount: ₹82,000 to goldmart.store@demo")
    print(f"      ✓ English companion lines (since it's a genuine purchase)")
    print(f"")
    print(f"   4️⃣  Tap: 'Yes, I made it' (genuine user confirming)")
    print(f"")
    print(f"   5️⃣  See 'Your account is now secured' screen")
    print(f"━" * 70)

    input("\n⏸️  Press ENTER here after you've tapped on the phone...")

    print(f"\n⏳ Waiting 3 seconds for backend to process...\n")
    time.sleep(3)

    # Show case state
    state = case_state(case_id)
    if state:
        print("📋 CASE STATE:")
        print(f"   ID:      {state[0]}")
        print(f"   State:   {state[1]}")
        print(f"   Created: {state[2]}")
        print(f"   Updated: {state[3]}\n")

    # Show events
    events = case_events(case_id)
    if events:
        print(f"📌 AUDIT TRAIL ({len(events)} events):")
        for i, (event_type, actor, payload, ts) in enumerate(events, 1):
            print(f"   {i}. [{ts}] {event_type}")
            print(f"      Actor: {actor}")
            if payload:
                print(f"      Data: {payload[:80]}...")
        print()

    # Show decision
    decision = case_decision(case_id)
    if decision:
        print("✅ DECISION RECORDED:")
        print(f"   ID: {decision[0]}")
        print(f"   Classification: {decision[1]}")
        print(f"   Rationale: {decision[2][:120]}...\n")
    else:
        print("⏳ DECISION: Pending (victim responded, awaiting officer review)\n")

    # Officer console instructions
    print("👮 OFFICER CONSOLE (Optional - to approve decision):")
    print("━" * 70)
    print(f"   Open: http://127.0.0.1:8000/officer")
    print(f"   Find case: {case_id[:8]}...")
    print(f"   Click: 'Mark as GENUINE' or 'Approve Release'")
    print(f"   Case will move to RESOLVED")
    print("━" * 70)

    print("\n✅ Demo complete!\n")

if __name__ == "__main__":
    main()
