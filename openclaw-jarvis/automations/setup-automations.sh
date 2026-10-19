#!/usr/bin/env bash
# Create (or update) every Jarvis automation on the OptiPlex Gateway.
#
# Safe to re-run: each job has a --declaration-key, so running this again
# converges the existing job instead of creating a duplicate.
#
# Usage (on the OptiPlex, Gateway running):
#   export TELEGRAM_CHAT_ID=123456789      # your numeric Telegram user ID
#   bash automations/setup-automations.sh
#
# Then check:  openclaw automations list --all
#
# Design notes
# - Conversational jobs (briefing, check-ins, reviews, nudges) use
#   `--session main --system-event`: they run inside Jarvis's main session,
#   the same conversation as your Telegram DMs and the room speaker, so when
#   you reply "done" or "snooze to 9" Jarvis knows what you are replying to.
#   Each event text tells Jarvis to deliver on Telegram with the message tool,
#   so delivery doesn't depend on which channel you used last.
# - Housekeeping jobs (health, backup) are command payloads: no model call,
#   no cost. They print NO_REPLY when there is nothing to say.

set -euo pipefail

: "${TELEGRAM_CHAT_ID:?Set TELEGRAM_CHAT_ID to your numeric Telegram user ID}"
TZ_NAME="Europe/London"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
OC="${OPENCLAW_BIN:-openclaw}"

DELIVER="Deliver to Taylor on Telegram with the message tool (channel telegram, to ${TELEGRAM_CHAT_ID}); if presence is home and it's not quiet hours, also speak a one-sentence version with room-speak. Then reply NO_REPLY."

# Every job names the agent explicitly: two agents (main, researcher) are configured.
add() { "$OC" automations add --agent main "$@" >/dev/null && echo "  ok  $2"; }

echo "Creating Jarvis automations (timezone ${TZ_NAME})..."

# 1. Morning briefing: short version on Telegram, full version on request.
add --name "Morning briefing (weekdays)" --declaration-key jarvis.morning.weekday \
  --cron "0 7 * * 1-5" --tz "$TZ_NAME" --exact \
  --session main --wake now \
  --system-event "Scheduled: morning briefing. Use the morning-briefing skill (short version) and offer the full one. ${DELIVER}"

add --name "Morning briefing (weekend)" --declaration-key jarvis.morning.weekend \
  --cron "0 9 * * 0,6" --tz "$TZ_NAME" --exact \
  --session main --wake now \
  --system-event "Scheduled: weekend morning briefing. Use the morning-briefing skill (short version) and offer the full one. ${DELIVER}"

# 2. Commitment watcher: the trigger script fires only when a ladder stage is due.
add --name "Commitment watcher" --declaration-key jarvis.commitments.watcher \
  --every 5m \
  --trigger-script "$HERE/commitment-watcher.js" \
  --session main --wake now \
  --system-event "Scheduled: commitment nudges are due. Follow the commitment-checkin skill for each item below (it decides voice vs Telegram from presence and records each nudge after sending). Reply NO_REPLY when done."

# 3. Evening check-in fallback, in case the arrive-home shortcut didn't fire.
add --name "Evening check-in fallback" --declaration-key jarvis.evening.fallback \
  --cron "0 19 * * *" --tz "$TZ_NAME" --exact \
  --session main --wake now \
  --system-event "Scheduled: evening check-in fallback. Follow the evening-checkin skill; it stops if the check-in already happened today. ${DELIVER}"

# 4. End-of-day summary and plan for tomorrow.
add --name "End-of-day summary" --declaration-key jarvis.eod \
  --cron "0 22 * * *" --tz "$TZ_NAME" --exact \
  --session main --wake now \
  --system-event "Scheduled: end-of-day review. Follow the end-of-day-summary skill. ${DELIVER}"

# 5. Sunday memory review, then weekly review.
add --name "Memory review" --declaration-key jarvis.memory.review \
  --cron "0 17 * * 0" --tz "$TZ_NAME" --exact \
  --session main --wake now \
  --system-event "Scheduled: weekly memory review. Follow the memory-review skill. Deliver to Taylor on Telegram with the message tool (channel telegram, to ${TELEGRAM_CHAT_ID}); never speak memory items aloud. Then reply NO_REPLY."

add --name "Weekly review" --declaration-key jarvis.weekly.review \
  --cron "0 18 * * 0" --tz "$TZ_NAME" --exact \
  --session main --wake now \
  --system-event "Scheduled: weekly review. Follow the weekly-review skill. ${DELIVER}"

# 6. Server health: command job, no model call; silent unless something is wrong.
add --name "Server health" --declaration-key jarvis.health \
  --every 30m \
  --command "bash '$WORKSPACE/skills/server-health/scripts/health.sh'" \
  --timeout-seconds 120 \
  --announce --channel telegram --to "$TELEGRAM_CHAT_ID"

# 7. Nightly backup: OpenClaw archive to the offsite target, plus a workspace git push.
#    Configure the offsite target first (guides/09-security-reliability.md).
add --name "Nightly backup" --declaration-key jarvis.backup \
  --cron "30 2 * * *" --tz "$TZ_NAME" --exact \
  --command "bash '$HERE/nightly-backup.sh'" \
  --timeout-seconds 1800 \
  --announce --channel telegram --to "$TELEGRAM_CHAT_ID"

# 8. Weekly update and security check (isolated, cheap, silent when nothing is wrong).
add --name "Update & security check" --declaration-key jarvis.update.check \
  --cron "0 9 * * 1" --tz "$TZ_NAME" --exact \
  --session isolated --light-context --model sonnet --tools exec,read \
  --message "Run \`openclaw update status\` and \`openclaw security audit\`. If an OpenClaw update is available, or the audit has any critical or high finding, reply with at most 4 lines: what's wrong, and the exact command to fix it (don't run upgrades yourself). Otherwise reply NO_REPLY." \
  --announce --channel telegram --to "$TELEGRAM_CHAT_ID"

echo "Done. Review with: $OC automations list --all"
