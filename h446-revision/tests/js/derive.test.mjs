import { test } from "node:test";
import assert from "node:assert/strict";
import {
  deriveRatings, deriveFlags, deriveVerified, pointStatus, tally,
  isoWithOffset, uuid4, formatDateUK, compareEvents,
} from "../../app/static/js/lib/derive.js";

const ev = (id, ts, type, target, data = {}) => ({ id, ts, type, target, data });

test("latest rating wins regardless of arrival order", () => {
  const events = [
    ev("b", "2026-11-02T10:00:00+00:00", "rating", "1.1.1a", { value: "got" }),
    ev("a", "2026-11-01T10:00:00+00:00", "rating", "1.1.1a", { value: "need" }),
  ];
  assert.equal(deriveRatings(events).get("1.1.1a").value, "got");
});

test("timestamps in different offsets are compared as instants", () => {
  // 09:30 BST (+01:00) is 08:30 UTC, so the 09:00 UTC event is later.
  const events = [
    ev("a", "2026-06-01T09:00:00+00:00", "rating", "p", { value: "once" }),
    ev("b", "2026-06-01T09:30:00+01:00", "rating", "p", { value: "got" }),
  ];
  assert.equal(deriveRatings(events).get("p").value, "once");
});

test("ties on timestamp are broken by id, deterministically", () => {
  const t = "2026-11-02T10:00:00.000+00:00";
  const x = ev("aaa", t, "rating", "p", { value: "need" });
  const y = ev("bbb", t, "rating", "p", { value: "got" });
  assert.equal(deriveRatings([x, y]).get("p").value, "got");
  assert.equal(deriveRatings([y, x]).get("p").value, "got");
  assert.ok(compareEvents(x, y) < 0);
});

test("flag then unflag clears; unflag then flag keeps note", () => {
  const a = [
    ev("1", "2026-11-02T10:00:00Z", "flag", "kw-mar", { note: "wrong" }),
    ev("2", "2026-11-02T11:00:00Z", "unflag", "kw-mar"),
    ev("3", "2026-11-02T10:00:00Z", "unflag", "kw-mdr"),
    ev("4", "2026-11-02T11:00:00Z", "flag", "kw-mdr", { note: "check" }),
  ];
  const flags = deriveFlags(a);
  assert.equal(flags.has("kw-mar"), false);
  assert.equal(flags.get("kw-mdr").note, "check");
});

test("verify / unverify", () => {
  const v = deriveVerified([
    ev("1", "2026-11-02T10:00:00Z", "verify", "kw-pc"),
    ev("2", "2026-11-02T10:00:00Z", "verify", "kw-acc"),
    ev("3", "2026-11-02T11:00:00Z", "unverify", "kw-acc"),
  ]);
  assert.deepEqual([...v], ["kw-pc"]);
});

test("point with sub-items shows lowest rated sub-item and counts", () => {
  const point = { id: "1.5.2a", sub_items: [{ id: "1.5.2a.1" }, { id: "1.5.2a.2" }, { id: "1.5.2a.3" }] };
  const ratings = deriveRatings([
    ev("1", "2026-11-01T10:00:00Z", "rating", "1.5.2a.1", { value: "got" }),
    ev("2", "2026-11-02T10:00:00Z", "rating", "1.5.2a.2", { value: "once" }),
  ]);
  const s = pointStatus(point, ratings);
  assert.equal(s.value, "once");
  assert.equal(s.rated, 2);
  assert.equal(s.total, 3);
  assert.equal(s.ts, "2026-11-02T10:00:00Z");
});

test("unrated point", () => {
  assert.deepEqual(pointStatus({ id: "x", sub_items: [] }, new Map()),
    { value: null, ts: null, rated: 0, total: 1 });
});

test("tally counts each point once", () => {
  const points = [{ id: "a" }, { id: "b" }, { id: "c" }];
  const ratings = new Map([["a", { value: "got", ts: "2026-01-01T00:00:00Z" }]]);
  assert.deepEqual(tally(points, ratings), { need: 0, once: 0, got: 1, none: 2 });
});

test("isoWithOffset produces a parseable timestamp with an offset", () => {
  const d = new Date("2026-07-01T12:34:56.789Z");
  const s = isoWithOffset(d);
  assert.match(s, /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}[+-]\d\d:\d\d$/);
  assert.equal(Date.parse(s), d.getTime());
});

test("uuid4 has the right shape and version bits, and doesn't repeat", () => {
  const seen = new Set();
  for (let i = 0; i < 1000; i++) {
    const u = uuid4();
    assert.match(u, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    seen.add(u);
  }
  assert.equal(seen.size, 1000);
});

test("UK date uses London time (23:30 UTC in summer is the next day in BST)", () => {
  assert.equal(formatDateUK("2026-07-01T23:30:00Z"), "02/07/2026");
  assert.equal(formatDateUK("2026-12-01T23:30:00Z"), "01/12/2026");
});
