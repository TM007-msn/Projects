// Condition script for the "Commitment watcher" automation.
//
// OpenClaw runs this every 5 minutes WITHOUT a model call. It asks the
// commitments ledger which escalation-ladder nudges are due. Only when there
// is at least one does it fire the job, which wakes Jarvis with the list
// appended to the job's message. Quiet ticks cost nothing.
//
// Read-only on purpose: the script only *reads* the ledger. Jarvis records
// each nudge (`commitments.py nudged ...`) after actually sending it, so if a
// send fails the same nudge is offered again later.
//
// Uses the trigger-script pattern from the OpenClaw docs: `exec` runs a shell
// command and `json` returns { fire, message?, state? }.
// If your workspace is not ~/.openclaw/workspace, change LEDGER below.

const LEDGER = "$HOME/.openclaw/workspace/skills/commitments/scripts/commitments.py";

const res = await exec({ command: `python3 "${LEDGER}" due` });
const raw = String(res?.aggregated ?? "").trim();

let due = null;
try {
  due = JSON.parse(raw);
} catch (err) {
  due = null;
}

if (!Array.isArray(due)) {
  // Fire so a broken ledger gets noticed instead of the loop going quiet.
  // The state check stops the same error being reported every 5 minutes.
  const errKey = `error:${raw.slice(0, 100)}`;
  json({
    fire: trigger.state?.lastKey !== errKey,
    message: `COMMITMENT WATCHER ERROR: the ledger output was not valid JSON. Run the server-health skill. Output:\n${raw.slice(0, 500)}`,
    state: { lastKey: errKey },
  });
} else {
  // Fingerprint of what is due (id + stage), so evaluations that happen
  // before Jarvis has recorded the nudge don't fire twice for the same thing.
  // If the same set is still due 15 minutes later, the send or the record
  // failed, so fire again (that's the retry).
  const RETRY_MS = 15 * 60 * 1000;
  const key = due.map((d) => `${d.id}:${d.stage}`).sort().join(",");
  const now = Date.now();
  const sameAsLast = key === trigger.state?.lastKey;
  const retryDue = now - (trigger.state?.lastFiredAt ?? 0) > RETRY_MS;
  const fire = due.length > 0 && (!sameAsLast || retryDue);
  json({
    fire,
    message: `Due nudges (JSON):\n${JSON.stringify(due, null, 2)}`,
    state: { lastKey: key, lastFiredAt: fire ? now : trigger.state?.lastFiredAt ?? 0 },
  });
}
