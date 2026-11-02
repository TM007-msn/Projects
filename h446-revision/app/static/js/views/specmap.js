// Spec map: every spec point with a 3-state self-rating and last-reviewed date.
//
// The page is built once. When a rating changes, only the small "slots"
// holding rating controls are rebuilt (see refreshSlots), so open sections and
// keyboard focus aren't lost.

import { h, mount } from "../lib/dom.js";
import { RATING_LABELS, pointStatus, tally } from "../lib/derive.js";
import { store } from "../store.js";
import { ratingControl, reviewedLabel } from "../ui/controls.js";

const FILTER_KEY = "h446.specFilter";
const openTopics = new Set(); // remembered while the app is open

function loadFilter() {
  try {
    return JSON.parse(localStorage.getItem(FILTER_KEY)) || { paper: "all", weakOnly: false };
  } catch {
    return { paper: "all", weakOnly: false };
  }
}

function saveFilter(f) {
  try { localStorage.setItem(FILTER_KEY, JSON.stringify(f)); } catch { /* blocked */ }
}

/** Weak = not rated yet, or rated "Need to revise". */
function isWeak(point) {
  const { value } = pointStatus(point, store.ratings);
  return value === null || value === "need";
}

export function renderSpecMap(root) {
  const filter = loadFilter();
  const { spec } = store;
  const body = h("div", { class: "specmap" });

  const paperTabs = h("div", { class: "tabs", role: "tablist", "aria-label": "Paper" },
    [["all", "Both papers"], ["1", "Paper 1"], ["2", "Paper 2"]].map(([value, label]) =>
      h("button", {
        type: "button", role: "tab", class: "tab", dataset: { paper: value },
        "aria-selected": filter.paper === value ? "true" : "false",
        onclick: () => { filter.paper = value; saveFilter(filter); build(); },
      }, label)));

  const weakToggle = h("label", { class: "toggle" },
    h("input", {
      type: "checkbox", checked: filter.weakOnly,
      onchange: (e) => { filter.weakOnly = e.target.checked; saveFilter(filter); build(); },
    }),
    " Only weak points (Need to revise or not rated)");

  function build() {
    for (const tab of paperTabs.children) {
      tab.setAttribute("aria-selected", tab.dataset.paper === filter.paper ? "true" : "false");
    }
    const sections = [];
    for (const paper of spec.papers) {
      if (filter.paper !== "all" && String(paper.paper) !== filter.paper) continue;
      const paperPoints = spec.points.filter((p) => p.paper === paper.paper);
      sections.push(h("section", { class: "paper" },
        h("h2", {}, `Paper ${paper.paper}: ${paper.title}`),
        h("div", { class: "slot", dataset: { tally: `paper-${paper.paper}` } }, tallyBar(paperPoints)),
        spec.topics.filter((t) => t.paper === paper.paper).map((t) => topicBlock(t, filter))));
    }
    mount(body, sections);
  }

  mount(root,
    h("header", { class: "page-head" },
      h("h1", {}, "Spec map"),
      h("p", { class: "muted" }, "Rate each point honestly. Points rated Need to revise come first in flashcards.")),
    h("div", { class: "filters" }, paperTabs, weakToggle),
    body);
  build();
}

function topicBlock(topic, filter) {
  const points = store.spec.points.filter((p) => p.topic === topic.id);
  const visible = filter.weakOnly ? points.filter(isWeak) : points;
  if (visible.length === 0) return null;
  const details = h("details", {
    class: "topic", open: openTopics.has(topic.id),
    ontoggle: (e) => (e.target.open ? openTopics.add(topic.id) : openTopics.delete(topic.id)),
  },
  h("summary", {},
    h("span", { class: "topic-title" }, `${topic.id} ${topic.title}`),
    h("span", { class: "slot", dataset: { tally: `topic-${topic.id}` } }, tallyBar(points, true))),
  store.spec.subtopics.filter((s) => s.topic === topic.id).map((sub) => {
    const subPoints = visible.filter((p) => p.subtopic === sub.id);
    if (subPoints.length === 0) return null;
    return h("div", { class: "subtopic" },
      h("div", { class: "subtopic-head" },
        h("h3", {}, `${sub.id} ${sub.title}`),
        h("a", { href: `#/topic/${sub.id}`, class: "link" }, "Summary →")),
      h("ul", { class: "points" }, subPoints.map(pointRow)));
  }));
  return details;
}

function pointRow(point) {
  const [stem, ...bullets] = point.spec_wording.split("\n");
  const hasSubs = point.sub_items.length > 0;
  return h("li", { class: "point" },
    h("div", { class: "point-text" },
      h("span", { class: "point-id" }, point.id),
      h("span", {}, stem)),
    hasSubs
      ? h("div", {},
        h("div", { class: "slot point-meta", dataset: { status: point.id } }, statusLine(point)),
        h("ul", { class: "sub-items" }, point.sub_items.map((s) =>
          h("li", { class: "sub-item" },
            h("span", {}, s.label),
            h("div", { class: "slot", dataset: { rating: s.id, label: s.label } },
              ratingControl(s.id, s.label), reviewedLabel(store.ratings.get(s.id)?.ts))))))
      : h("div", { class: "slot point-meta", dataset: { rating: point.id, label: point.id } },
        ratingControl(point.id, point.id), reviewedLabel(store.ratings.get(point.id)?.ts)),
    bullets.length && !hasSubs ? h("ul", { class: "bullets" }, bullets.map((b) => h("li", {}, b.slice(1).trim()))) : null,
    detailsBlock(point));
}

/** Summary line for a point with sub-items: lowest rating and how many rated. */
function statusLine(point) {
  const s = pointStatus(point, store.ratings);
  const label = s.value ? RATING_LABELS[s.value] : "Not rated";
  return [
    h("span", { class: `pill pill-${s.value || "none"}` }, label),
    h("span", { class: "muted" }, ` ${s.rated} of ${s.total} parts rated`),
    reviewedLabel(s.ts),
  ];
}

/** Collapsible clarification and checklist text for a point. */
function detailsBlock(point) {
  if (!point.clarification.length && !point.checklist_statements.length) return null;
  return h("details", { class: "point-details" },
    h("summary", {}, "Clarification and checklist"),
    point.clarification.length
      ? h("div", {},
        h("h4", {}, "OCR clarification"),
        point.clarification.map((p) => h("p", {}, p)),
        point.clarification_shared_with.length
          ? h("p", { class: "muted small" }, `Shared with ${point.clarification_shared_with.join(", ")}.`)
          : null)
      : null,
    point.checklist_statements.length
      ? h("div", {},
        h("h4", {}, "Checklist"),
        h("ul", {}, point.checklist_statements.map((s) => h("li", {}, s.text))))
      : null);
}

/** Small stacked bar: Got it / Revised once / Need to revise / not rated. */
function tallyBar(points, compact = false) {
  const c = tally(points, store.ratings);
  const total = points.length || 1;
  const bar = h("span", { class: `tally ${compact ? "tally-compact" : ""}`, role: "img",
    "aria-label": `${c.got} got it, ${c.once} revised once, ${c.need} need to revise, ${c.none} not rated` });
  for (const key of ["got", "once", "need", "none"]) {
    if (!c[key]) continue;
    const seg = h("span", { class: `tally-seg tally-${key}` });
    seg.style.flexGrow = String(c[key] / total); // CSSOM is allowed under the CSP
    bar.append(seg);
  }
  if (compact) return bar;
  return [bar, h("span", { class: "tally-text muted" },
    `${c.got} got it · ${c.once} once · ${c.need} need · ${c.none} not rated`)];
}

/** Rebuild just the rating controls, status lines and tallies after a change. */
export function refreshSpecMap(root) {
  const active = document.activeElement;
  const activeSlot = active?.closest?.(".slot");
  const activeIndex = activeSlot ? [...activeSlot.querySelectorAll("button")].indexOf(active) : -1;
  const activeKey = activeSlot ? JSON.stringify(activeSlot.dataset) : null;

  for (const slot of root.querySelectorAll(".slot[data-rating]")) {
    const id = slot.dataset.rating;
    mount(slot, ratingControl(id, slot.dataset.label), reviewedLabel(store.ratings.get(id)?.ts));
  }
  for (const slot of root.querySelectorAll(".slot[data-status]")) {
    mount(slot, statusLine(store.spec.points.find((p) => p.id === slot.dataset.status)));
  }
  for (const slot of root.querySelectorAll(".slot[data-tally]")) {
    const [kind, id] = slot.dataset.tally.split("-");
    const pts = store.spec.points.filter((p) => (kind === "paper" ? String(p.paper) === id : p.topic === id));
    mount(slot, tallyBar(pts, kind === "topic"));
  }
  // Put keyboard focus back on the same button.
  if (activeKey && activeIndex >= 0) {
    const slot = [...root.querySelectorAll(".slot")].find((s) => JSON.stringify(s.dataset) === activeKey);
    slot?.querySelectorAll("button")[activeIndex]?.focus();
  }
}
