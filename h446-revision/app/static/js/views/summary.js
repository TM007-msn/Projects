// Summary page for one subtopic, e.g. #/topic/1.1.1
//
// Read mode shows everything. Cover mode hides each keyword's definition
// behind a button so you can test yourself before revealing it.
// Shortcuts (desktop): R = read mode, C = cover mode, A = reveal all.

import { h, mount } from "../lib/dom.js";
import { findSubtopic, getSummary, pointsOf, store } from "../store.js";
import { itemActions, ratingControl, reviewedLabel } from "../ui/controls.js";

const MODE_KEY = "h446.summaryMode";

function loadMode() {
  try { return localStorage.getItem(MODE_KEY) === "cover" ? "cover" : "read"; } catch { return "read"; }
}

function saveMode(mode) {
  try { localStorage.setItem(MODE_KEY, mode); } catch { /* blocked */ }
}

export async function renderSummary(root, subtopicId) {
  const sub = findSubtopic(subtopicId);
  if (!sub) {
    mount(root, h("p", {}, `No subtopic ${subtopicId}.`), h("a", { href: "#/spec" }, "Back to the spec map"));
    return null;
  }
  mount(root, h("p", { class: "muted" }, "Loading…"));
  const summary = await getSummary(subtopicId);
  const items = new Map(); // content id -> item, for refreshing verify/flag slots
  let mode = loadMode();
  const revealed = new Set();

  const page = h("article", { class: `summary mode-${mode}` });

  const modeTabs = h("div", { class: "tabs", role: "tablist", "aria-label": "View" },
    [["read", "Read"], ["cover", "Cover"]].map(([value, label]) =>
      h("button", {
        type: "button", role: "tab", class: "tab", dataset: { mode: value },
        "aria-selected": mode === value ? "true" : "false",
        onclick: () => setMode(value),
      }, label)));

  const revealAll = h("button", { type: "button", class: "btn btn-ghost cover-only",
    onclick: () => toggleAll() }, "Reveal all");

  function setMode(value) {
    mode = value;
    saveMode(value);
    page.className = `summary mode-${mode}`;
    for (const t of modeTabs.children) t.setAttribute("aria-selected", t.dataset.mode === mode ? "true" : "false");
  }

  function toggleAll() {
    const cards = page.querySelectorAll(".kw");
    const allShown = [...cards].every((c) => c.classList.contains("revealed"));
    for (const c of cards) setRevealed(c, !allShown);
    revealAll.textContent = allShown ? "Reveal all" : "Hide all";
  }

  function setRevealed(card, on) {
    card.classList.toggle("revealed", on);
    card.querySelector(".kw-reveal").setAttribute("aria-expanded", on ? "true" : "false");
    card.querySelector(".kw-reveal").textContent = on ? "Hide" : "Show definition";
    on ? revealed.add(card.dataset.id) : revealed.delete(card.dataset.id);
  }

  const actionsSlot = (item) => {
    items.set(item.id, item);
    return h("div", { class: "slot", dataset: { actions: item.id } }, itemActions(item));
  };

  // ---- sections ------------------------------------------------------------
  const topic = store.spec.topics.find((t) => t.id === sub.topic);
  const head = h("header", { class: "page-head" },
    h("p", { class: "crumbs muted" }, `Paper ${sub.paper} · ${topic.id} ${topic.title}`),
    h("h1", {}, `${sub.id} ${sub.title}`),
    h("div", { class: "filters" }, modeTabs, revealAll));

  const sections = [];
  if (!summary) {
    sections.push(h("section", { class: "card" },
      h("p", {}, "This summary hasn't been written yet."),
      h("p", { class: "muted" }, "The spec points and resources below are still available.")));
  } else {
    sections.push(h("section", {},
      h("h2", {}, "Key points"),
      h("ol", { class: "key-points" }, summary.key_points.map((kp) =>
        h("li", { class: "content-item" }, h("p", {}, kp.text), actionsSlot(kp))))));

    const keywords = summary.keyword_ids.map((id) => store.keywords.get(id)).filter(Boolean);
    sections.push(h("section", {},
      h("h2", {}, "Keywords"),
      h("p", { class: "muted small cover-only" }, "Say the definition out loud, then reveal it."),
      h("ul", { class: "keywords" }, keywords.map((kw) => keywordCard(kw)))));

    if (summary.dont_confuse?.length) {
      sections.push(h("section", {},
        h("h2", {}, "Don't confuse"),
        h("ul", { class: "confuse" }, summary.dont_confuse.map((dc) =>
          h("li", { class: "content-item" }, h("p", {}, dc.text), actionsSlot(dc))))));
    }
  }

  sections.push(h("section", {},
    h("h2", {}, "Spec points"),
    h("ul", { class: "points" }, pointsOf(sub.id).map((p) => h("li", { class: "point" },
      h("div", { class: "point-text" }, h("span", { class: "point-id" }, p.id),
        h("span", {}, p.spec_wording.split("\n")[0])),
      p.sub_items.length
        ? h("p", { class: "muted small" }, "Rate the parts of this point on the spec map.")
        : h("div", { class: "slot point-meta", dataset: { rating: p.id, label: p.id } },
          ratingControl(p.id, p.id), reviewedLabel(store.ratings.get(p.id)?.ts)))))));

  sections.push(resourcesSection(sub));
  sections.push(prevNext(sub));

  function keywordCard(kw) {
    const id = `def-${kw.id}`;
    const card = h("li", { class: "kw content-item", dataset: { id: kw.id } },
      h("div", { class: "kw-head" },
        h("span", { class: "kw-term" }, kw.term),
        kw.acronym ? h("span", { class: "kw-acronym" }, kw.acronym) : null,
        h("button", {
          type: "button", class: "chip kw-reveal cover-only", "aria-expanded": "false", "aria-controls": id,
          onclick: () => setRevealed(card, !card.classList.contains("revealed")),
        }, "Show definition")),
      h("div", { class: "kw-body", id },
        h("p", { class: "kw-def" }, kw.definition),
        kw.dont_confuse_with ? h("p", { class: "kw-confuse small" }, h("strong", {}, "Don't confuse with "), kw.dont_confuse_with) : null),
      actionsSlot(kw));
    return card;
  }

  mount(page, head, sections);
  mount(root, page);

  // Keyboard shortcuts while this page is shown.
  const onKey = (e) => {
    if (e.target.closest("input, textarea, dialog") || e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key.toLowerCase();
    if (k === "r") setMode("read");
    else if (k === "c") setMode("cover");
    else if (k === "a" && mode === "cover") toggleAll();
  };
  document.addEventListener("keydown", onKey);

  // Called by main.js when state changes; returns a clean-up function.
  return {
    refresh() {
      for (const slot of page.querySelectorAll(".slot[data-actions]")) {
        mount(slot, itemActions(items.get(slot.dataset.actions)));
      }
      for (const slot of page.querySelectorAll(".slot[data-rating]")) {
        const pid = slot.dataset.rating;
        mount(slot, ratingControl(pid, slot.dataset.label), reviewedLabel(store.ratings.get(pid)?.ts));
      }
    },
    destroy() { document.removeEventListener("keydown", onKey); },
  };
}

function resourcesSection(sub) {
  const ext = (url, text) => h("a", { href: url, target: "_blank", rel: "noopener noreferrer" }, text || url);
  const video = sub.checklist_topic?.video_url;
  return h("section", {},
    h("h2", {}, "Resources"),
    video ? h("p", {}, "Craig'n'Dave video: ", ext(video, sub.checklist_topic.title)) : null,
    sub.resource_urls.length
      ? h("div", {},
        h("h3", {}, "Links from the OCR guide"),
        h("p", { class: "muted small" }, "From 2017; some may no longer work."),
        h("ul", { class: "links" }, sub.resource_urls.map((u) => h("li", {}, ext(u)))))
      : null,
    sub.cross_topic_links.length
      ? h("div", {},
        h("h3", {}, "Links to other topics"),
        h("ul", { class: "links" }, sub.cross_topic_links.map((l) =>
          h("li", {}, h("a", { href: `#/topic/${l.id}` }, l.label)))))
      : null);
}

function prevNext(sub) {
  const subs = store.spec.subtopics;
  const i = subs.findIndex((s) => s.id === sub.id);
  const prev = subs[i - 1];
  const next = subs[i + 1];
  return h("nav", { class: "prev-next", "aria-label": "Other subtopics" },
    prev ? h("a", { href: `#/topic/${prev.id}`, class: "btn btn-ghost" }, `← ${prev.id}`) : h("span"),
    next ? h("a", { href: `#/topic/${next.id}`, class: "btn btn-ghost" }, `${next.id} →`) : h("span"));
}
