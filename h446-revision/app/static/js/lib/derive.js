// Pure functions that turn the append-only event log into current state.
// No DOM, no network: tested with `node --test tests/js`.
//
// Rule used everywhere: for a given target, the event with the latest
// timestamp wins. Ties (same millisecond) are broken by event id so every
// device reaches the same answer from the same events.

export const RATING_ORDER = { need: 0, once: 1, got: 2 };
export const RATING_LABELS = { need: "Need to revise", once: "Revised once", got: "Got it" };

/** Compare two events chronologically (timestamp, then id). */
export function compareEvents(a, b) {
  const ta = Date.parse(a.ts);
  const tb = Date.parse(b.ts);
  if (ta !== tb) return ta - tb;
  return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
}

/**
 * For each target, the latest event whose type is in `types`.
 * Returns a Map: target -> event.
 */
export function latestByTarget(events, types) {
  const wanted = new Set(types);
  const latest = new Map();
  for (const e of events) {
    if (!wanted.has(e.type)) continue;
    const current = latest.get(e.target);
    if (!current || compareEvents(current, e) < 0) latest.set(e.target, e);
  }
  return latest;
}

/** Map: target -> { value, ts } for every rated point or sub-item. */
export function deriveRatings(events) {
  const out = new Map();
  for (const [target, e] of latestByTarget(events, ["rating"])) {
    out.set(target, { value: e.data.value, ts: e.ts });
  }
  return out;
}

/** Map: target -> { note, ts } for items whose latest flag/unflag is a flag. */
export function deriveFlags(events) {
  const out = new Map();
  for (const [target, e] of latestByTarget(events, ["flag", "unflag"])) {
    if (e.type === "flag") out.set(target, { note: e.data.note || "", ts: e.ts });
  }
  return out;
}

/** Set of targets whose latest verify/unverify is a verify. */
export function deriveVerified(events) {
  const out = new Set();
  for (const [target, e] of latestByTarget(events, ["verify", "unverify"])) {
    if (e.type === "verify") out.add(target);
  }
  return out;
}

/**
 * Rating shown for a spec point.
 * - A point without sub-items: its own rating.
 * - A point with sub-items: the LOWEST rating among rated sub-items (you've
 *   only "got" ethics if you've got every part of it), with a count of how
 *   many sub-items are rated. The last-reviewed date is the most recent.
 * Returns { value, ts, rated, total } where value/ts may be null.
 */
export function pointStatus(point, ratings) {
  const subs = point.sub_items || [];
  if (subs.length === 0) {
    const r = ratings.get(point.id);
    return { value: r ? r.value : null, ts: r ? r.ts : null, rated: r ? 1 : 0, total: 1 };
  }
  let value = null;
  let ts = null;
  let rated = 0;
  for (const s of subs) {
    const r = ratings.get(s.id);
    if (!r) continue;
    rated += 1;
    if (value === null || RATING_ORDER[r.value] < RATING_ORDER[value]) value = r.value;
    if (ts === null || Date.parse(r.ts) > Date.parse(ts)) ts = r.ts;
  }
  return { value, ts, rated, total: subs.length };
}

/** Count points per rating (null = not rated) for a list of points. */
export function tally(points, ratings) {
  const counts = { need: 0, once: 0, got: 0, none: 0 };
  for (const p of points) {
    const { value } = pointStatus(p, ratings);
    counts[value || "none"] += 1;
  }
  return counts;
}

/** "02/11/2026" in UK format, using London time so late-night reviews land on the right day. */
export function formatDateUK(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { timeZone: "Europe/London" });
}

/** Local time as ISO 8601 with offset, e.g. 2026-11-02T08:15:30.123+00:00. */
export function isoWithOffset(date = new Date()) {
  const pad = (n, w = 2) => String(Math.abs(n)).padStart(w, "0");
  const off = -date.getTimezoneOffset(); // minutes east of UTC
  const sign = off >= 0 ? "+" : "-";
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(date.getMilliseconds(), 3)}` +
    `${sign}${pad(Math.floor(Math.abs(off) / 60))}:${pad(Math.abs(off) % 60)}`
  );
}

/**
 * Random v4 UUID. crypto.randomUUID() only exists on HTTPS or localhost, and
 * this app is usually opened over plain HTTP on the LAN, so build one from
 * crypto.getRandomValues(), which works everywhere.
 */
export function uuid4(cryptoObj = globalThis.crypto) {
  const b = cryptoObj.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40; // version 4
  b[8] = (b[8] & 0x3f) | 0x80; // RFC 4122 variant
  const hex = [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}
