#!/usr/bin/env bash
# Back up the planner database to life-planner/backups/planner-YYYY-MM-DD.db and keep the last 14 days.
# Run it by hand (./scripts/backup.sh) or nightly from cron (see SETUP.md).

# Stop at the first error (-e), treat unset variables as errors (-u),
# and fail a pipeline if any command in it fails (-o pipefail).
set -euo pipefail

# Work from the life-planner folder, wherever the script is called from (cron starts in your home folder).
cd "$(dirname "$0")/.."

mkdir -p backups
target="backups/planner-$(date +%F).db"   # %F is YYYY-MM-DD, so files sort by date

# Inside the running container: use SQLite's own backup API (safe even while the app is writing),
# write the copy to /tmp, then print it to stdout. Outside, we save that output to the backups folder.
# Streaming it out avoids file-permission problems with the root-owned data/ folder.
docker compose exec -T planner sh -c '
python -c "
import sqlite3
source = sqlite3.connect(\"/srv/data/planner.db\")
copy = sqlite3.connect(\"/tmp/planner-backup.db\")
source.backup(copy)
copy.close()
source.close()
" && cat /tmp/planner-backup.db && rm /tmp/planner-backup.db
' > "$target.part"

# Only replace today's backup once the copy has fully arrived and isn't empty.
if [ ! -s "$target.part" ]; then
    echo "Backup failed: empty file" >&2
    rm -f "$target.part"
    exit 1
fi
mv "$target.part" "$target"

# Delete backups older than 14 days.
find backups -name 'planner-*.db' -mtime +14 -delete

echo "$(date '+%d/%m/%Y %H:%M') backed up to $target"
