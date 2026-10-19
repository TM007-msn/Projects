#!/usr/bin/env bash
# Nightly backup, run by the "Nightly backup" automation at 02:30.
#
# 1. `openclaw backup create` archives config, state databases and the
#    workspace to the offsite target you configured
#    (see guides/09-security-reliability.md), keeping 7 daily, 4 weekly and
#    6 monthly copies, and verifies the archive.
# 2. Commits and pushes the workspace to its private git repo, so memory
#    files have readable history.
#
# Prints NO_REPLY on success (nothing is sent to Telegram). On failure it
# prints what failed and exits 1, which triggers the automation failure alert.

set -uo pipefail

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
failed=()

if ! openclaw backup create --to offsite --verify \
     --keep-daily 7 --keep-weekly 4 --keep-monthly 6 >/dev/null 2>&1; then
  failed+=("openclaw backup create (run it by hand to see the error)")
fi

if [ -d "$WORKSPACE/.git" ]; then
  (
    cd "$WORKSPACE" || exit 1
    git add -A
    git diff --cached --quiet || git commit -qm "backup $(date +%F)"
    git push -q
  ) >/dev/null 2>&1 || failed+=("workspace git push")
fi

if [ "${#failed[@]}" -eq 0 ]; then
  echo "NO_REPLY"
  exit 0
fi
echo "Nightly backup problem:"
printf -- '- %s\n' "${failed[@]}"
exit 1
