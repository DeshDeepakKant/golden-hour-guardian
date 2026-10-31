#!/usr/bin/env bash
# Preflight for Golden Hour Guardian — run before Session 1 (checkpoint H0).
# Read-only checks; it installs nothing.
set -u
ok()   { printf '  \033[32m✔\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✘\033[0m %s\n' "$*"; FAIL=1; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
FAIL=0
MODEL="${GUARDIAN_LLM_MODEL:-qwen3:4b}"

echo "== Core tools"
if command -v python3 >/dev/null; then
  v=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
  python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)' && ok "python3 $v" || bad "python3 $v (need 3.11+)"
  python3 -c 'import venv' 2>/dev/null && ok "python venv module" || bad "python3-venv missing (sudo apt install python3-venv)"
else bad "python3 not found"; fi
for t in git make curl; do command -v $t >/dev/null && ok "$t" || bad "$t not found (sudo apt install $t)"; done
command -v claude >/dev/null && ok "claude CLI $(claude --version 2>/dev/null | head -1)" || bad "Claude Code CLI not found"

echo "== Local model (Ollama)"
if command -v ollama >/dev/null; then
  ok "ollama installed"
  if curl -s --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null; then
    ok "ollama server running"
    curl -s http://127.0.0.1:11434/api/tags | grep -q "\"${MODEL}\"" && ok "model ${MODEL} pulled" \
      || warn "model ${MODEL} not pulled — run: ollama pull ${MODEL}"
  else warn "ollama not running — start it: ollama serve (or systemctl start ollama)"; fi
else warn "ollama not installed — demo still works on templates; install from ollama.com for the SLM"; fi
if command -v nvidia-smi >/dev/null; then ok "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1)"
else warn "no NVIDIA GPU detected — a 4B model on CPU is slower; check 'make bench' latency"; fi
free -g 2>/dev/null | awk '/Mem:/{ if ($2>=8) print "  \033[32m✔\033[0m RAM " $2 " GB"; else print "  \033[33m!\033[0m RAM " $2 " GB (8+ recommended for a 4B model)"}'

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
