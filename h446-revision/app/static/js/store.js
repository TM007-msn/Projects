// App state: content JSON plus the event log, with derived state kept up to date.
//
// Writes are optimistic: a new event is applied locally straight away, then
// sent to the server. If sending fails (no signal on the train), the event
// waits in a small localStorage queue and is resent on the next write or when
// the browser comes back online. Resending is safe because the server ignores
// event ids it already has. (Phase 6 replaces this queue with IndexedDB.)

import { api, AuthError } from "./api.js";
import { deriveFlags, deriveRatings, deriveVerified, isoWithOffset, uuid4 } from "./lib/derive.js";

const QUEUE_KEY = "h446.pendingEvents";
const listeners = new Set();

export const store = {
  spec: null,
  keywords: new Map(),     // id -> keyword
  summaries: new Map(),    // subtopic id -> summary JSON, or null if not written yet
  events: [],
  ratings: new Map(),
  flags: new Map(),
  verified: new Set(),
  pending: loadQueue(),
};

function loadQueue() {
  try {
    return JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveQueue() {
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(store.pending));
  } catch { /* storage full or blocked: events stay in memory */ }
}

function recompute() {
  store.ratings = deriveRatings(store.events);
  store.flags = deriveFlags(store.events);
  store.verified = deriveVerified(store.events);
  for (const fn of listeners) fn();
}

/** Call fn whenever state changes. Returns an unsubscribe function. */
export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

/** Load spec, keywords and events after login. */
export async function loadAll() {
  const [spec, kw, ev] = await Promise.all([
    api.content("spec.json"),
    api.content("keywords.json"),
    api.events(),
  ]);
  store.spec = spec;
  store.keywords = new Map((kw?.keywords || []).map((k) => [k.id, k]));
  const seen = new Set(ev.events.map((e) => e.id));
  // Include queued events the server hasn't got yet.
  store.events = [...ev.events, ...store.pending.filter((e) => !seen.has(e.id))];
  recompute();
  flush();
}

/** Summary JSON for a subtopic (cached). null means not written yet. */
export async function getSummary(subtopicId) {
  if (!store.summaries.has(subtopicId)) {
    store.summaries.set(subtopicId, await api.content(`summaries/${subtopicId}.json`));
  }
  return store.summaries.get(subtopicId);
}

/** Record something that happened. type/target/data as in app/events.py. */
export function record(type, target, data = {}) {
  const event = { id: uuid4(), ts: isoWithOffset(), type, target, data };
  store.events.push(event);
  store.pending.push(event);
  saveQueue();
  recompute();
  flush();
  return event;
}

let flushing = false;

/** Send queued events. Safe to call any time; does nothing if already sending. */
export async function flush() {
  if (flushing || store.pending.length === 0) return;
  flushing = true;
  const batch = store.pending.slice(0, 200);
  try {
    await api.postEvents(batch);
    const sent = new Set(batch.map((e) => e.id));
    store.pending = store.pending.filter((e) => !sent.has(e.id));
    saveQueue();
  } catch (err) {
    if (err instanceof AuthError) window.dispatchEvent(new CustomEvent("auth-required"));
    // Otherwise offline or server down: keep the queue and try later.
  } finally {
    flushing = false;
    for (const fn of listeners) fn();
  }
  if (store.pending.length && navigator.onLine) setTimeout(flush, 5000);
}

window.addEventListener("online", flush);

// ---- lookups --------------------------------------------------------------

export const findPoint = (id) => store.spec.points.find((p) => p.id === id);
export const findSubtopic = (id) => store.spec.subtopics.find((s) => s.id === id);
export const pointsOf = (subtopicId) => store.spec.points.filter((p) => p.subtopic === subtopicId);
export const isFlagged = (id) => store.flags.has(id);

/** Verified if the JSON says so or the latest verify/unverify event says so. */
export function isVerified(item) {
  return item.verified === true || store.verified.has(item.id);
}
