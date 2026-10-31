#!/usr/bin/env bash
# Preflight for Golden Hour Guardian — run before Session 1 (checkpoint H0).
# Read-only checks; it installs nothing.
set -u
ok()   { printf '  \033[32m✔\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✘\033[0m %s\n' "$*"; FAIL=1; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
FAIL=0

echo "== Core tools"
if command -v python3 >/dev/null; then
  v=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
  python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)' && ok "python3 $v" || bad "python3 $v (need 3.11+)"
  python3 -c 'import venv' 2>/dev/null && ok "python venv module" || bad "python3-venv missing (sudo apt install python3-venv)"
else bad "python3 not found"; fi
for t in git make curl; do command -v $t >/dev/null && ok "$t" || bad "$t not found (sudo apt install $t)"; done
command -v claude >/dev/null && ok "claude CLI $(claude --version 2>/dev/null | head -1)" || bad "Claude Code CLI not found"

echo "== Claude API (optional — wording + reply classification)"
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then ok "ANTHROPIC_API_KEY is set"
else warn "ANTHROPIC_API_KEY not set — demo still works on templates"; fi
code=$(curl -s --max-time 3 -o /dev/null -w '%{http_code}' https://api.anthropic.com 2>/dev/null)
if [ -n "$code" ] && [ "$code" != "000" ]; then ok "api.anthropic.com reachable (HTTP $code)"
else warn "api.anthropic.com not reachable — demo still works on templates"; fi

echo "== Android"
if command -v adb >/dev/null; then
  ok "adb installed"
  n=$(adb devices | awk 'NR>1 && $2=="device"' | wc -l)
  u=$(adb devices | awk 'NR>1 && $2=="unauthorized"' | wc -l)
  [ "$n" -ge 1 ] && ok "$n phone(s) authorised" || { [ "$u" -ge 1 ] && bad "phone connected but unauthorised — accept the RSA prompt on the phone" || warn "no phone connected yet (needed in Session 2)"; }
else bad "adb not found (sudo apt install adb)"; fi
command -v scrcpy >/dev/null && ok "scrcpy (screen mirroring for the projector)" || warn "scrcpy not found — optional but great for the demo (sudo apt install scrcpy)"

echo "== Optional"
(command -v chromium >/dev/null || command -v chromium-browser >/dev/null || command -v google-chrome >/dev/null) \
  && ok "Chrome/Chromium (lets Claude screenshot the officer console)" || warn "no desktop Chrome/Chromium — UI screenshots by Claude won't work"
(ss -ltn 2>/dev/null | grep -q ':8000 ') && warn "port 8000 already in use" || ok "port 8000 free"

echo
[ "$FAIL" -eq 0 ] && echo "Preflight passed (warnings are optional)." || { echo "Fix the ✘ items, then rerun."; exit 1; }
