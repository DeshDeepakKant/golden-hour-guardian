#!/usr/bin/env bash
# Connect the Android phone to the local Guardian server and open the victim app.
# Usage: bash scripts/android.sh [user_id] [device_id]   (default: usr_ravi on its seeded trusted phone)
set -euo pipefail
USER_ID="${1:-usr_ravi}"
# Seeded trusted device id is dev_<name>_phone (mocks/seed.py device_id_for). The server checks it.
DEVICE_ID="${2:-dev_${USER_ID#usr_}_phone}"
PORT=8000
URL="http://localhost:${PORT}/victim/?user=${USER_ID}&device=${DEVICE_ID}"

command -v adb >/dev/null || { echo "adb not found: sudo apt install adb"; exit 1; }
STATE=$(adb get-state 2>/dev/null || true)
if [ "$STATE" != "device" ]; then
  echo "No authorised phone. On the phone: Settings > Developer options > USB debugging ON,"
  echo "then plug in USB and tap 'Allow' on the RSA prompt. Current: $(adb devices | tail -n +2)"
  exit 1
fi

curl -s --max-time 2 "http://127.0.0.1:${PORT}/health" >/dev/null \
  || echo "Warning: server not answering on :${PORT} — run 'make run' in another terminal."

# Phone's localhost:8000 -> laptop's 127.0.0.1:8000 over USB (no Wi-Fi needed, and it's a secure context)
adb reverse tcp:${PORT} tcp:${PORT}
# Keep the screen on while plugged in (reset after the demo: adb shell svc power stayon false)
adb shell svc power stayon usb || true
# Open in Chrome; fall back to the default browser
adb shell am start -a android.intent.action.VIEW -d "${URL}" com.android.chrome >/dev/null 2>&1 \
  || adb shell am start -a android.intent.action.VIEW -d "${URL}" >/dev/null

echo "Opened ${URL} on $(adb shell getprop ro.product.model | tr -d '\r')."
echo "On the phone: tap 'Enable security alerts' once (unlocks voice + vibration)."

if command -v scrcpy >/dev/null; then
  (scrcpy --window-title "Guardian phone" --stay-awake >/dev/null 2>&1 &)
  echo "scrcpy mirroring started (record a backup: scrcpy --record demo.mp4)."
fi
echo "Screenshot for checking: adb exec-out screencap -p > /tmp/phone.png"
