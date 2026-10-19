#!/usr/bin/env bash
# Jarvis server health check for the OptiPlex.
#
# Run by the "Server health" automation every 30 minutes as a command job,
# so it costs no model calls. Output rules:
#   - everything fine  -> prints NO_REPLY, which OpenClaw treats as "say nothing"
#   - something wrong  -> prints one short line per problem, delivered to Telegram
# It always exits 0, so a problem is reported once as a message rather than
# also tripping the automation failure alerts.
#
# Thresholds can be overridden with environment variables.

set -u

DISK_WARN_PCT="${DISK_WARN_PCT:-90}"
MEM_WARN_PCT="${MEM_WARN_PCT:-92}"
SERVICES="${SERVICES:-openclaw-gateway jarvis-voice}"   # systemd --user units
STATE_DIR="${JARVIS_STATE_DIR:-$HOME/.openclaw/workspace/state}"

problems=()

# 1. Disk space on / and on the OpenClaw state directory.
for mount in / "$HOME/.openclaw"; do
  [ -e "$mount" ] || continue
  used=$(df -P "$mount" | awk 'NR==2 {gsub("%", "", $5); print $5}')
  if [ "${used:-0}" -ge "$DISK_WARN_PCT" ]; then
    problems+=("Disk ${used}% full on $(df -P "$mount" | awk 'NR==2 {print $6}')")
  fi
done

# 2. Memory pressure (MemAvailable as a share of MemTotal).
if [ -r /proc/meminfo ]; then
  mem_used=$(awk '/MemTotal/ {t=$2} /MemAvailable/ {a=$2} END {printf "%d", (t-a)*100/t}' /proc/meminfo)
  if [ "$mem_used" -ge "$MEM_WARN_PCT" ]; then
    problems+=("Memory ${mem_used}% used")
  fi
fi

# 3. Long-running services. A unit that isn't installed yet is skipped,
#    so this works before the voice daemon exists.
if command -v systemctl >/dev/null 2>&1; then
  for svc in $SERVICES; do
    if systemctl --user cat "${svc}.service" >/dev/null 2>&1; then
      if ! systemctl --user is-active --quiet "${svc}.service"; then
        problems+=("Service ${svc} is $(systemctl --user is-active "${svc}.service")")
      fi
    fi
  done
fi

# 4. The Gateway answers its health RPC.
if command -v openclaw >/dev/null 2>&1; then
  if ! timeout 20 openclaw health --json >/dev/null 2>&1; then
    problems+=("Gateway health check failed (run: openclaw health)")
  fi
fi

# 5. The commitments ledger is valid JSON (a corrupt file would silence the loop).
if [ -f "$STATE_DIR/commitments.json" ]; then
  if ! python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$STATE_DIR/commitments.json" 2>/dev/null; then
    problems+=("commitments.json is not valid JSON")
  fi
fi

if [ "${#problems[@]}" -eq 0 ]; then
  echo "NO_REPLY"
else
  echo "Server health: ${#problems[@]} problem(s)"
  printf -- '- %s\n' "${problems[@]}"
fi
exit 0
