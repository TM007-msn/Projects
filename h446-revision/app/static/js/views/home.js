// Home: progress at a glance and links into the summaries.

import { api } from "../api.js";
import { h, mount } from "../lib/dom.js";
import { tally } from "../lib/derive.js";
import { store } from "../store.js";

let available = null; // subtopic ids that have a summary written

export async function renderHome(root) {
  if (available === null) {
    const index = await api.content("summaries/index.json");
    available = new Set(index?.subtopics || []);
  }
  const { spec } = store;

  const paperCards = spec.papers.map((paper) => {
    const pts = spec.points.filter((p) => p.paper === paper.paper);
    const c = tally(pts, store.ratings);
    const pct = Math.round((c.got / pts.length) * 100);
    return h("div", { class: "card stat" },
      h("h2", {}, `Paper ${paper.paper}`),
      h("p", { class: "muted" }, paper.title),
      h("p", { class: "stat-big" }, `${pct}%`),
      h("p", { class: "muted small" }, `rated Got it (${c.got} of ${pts.length} points)`),
      h("p", { class: "small" }, `${c.need} need to revise · ${c.none} not rated yet`));
  });

  const topics = spec.topics.map((t) => h("div", { class: "topic-links" },
    h("h3", {}, `${t.id} ${t.title}`),
    h("ul", {}, spec.subtopics.filter((s) => s.topic === t.id).map((s) =>
      h("li", {}, available.has(s.id)
        ? h("a", { href: `#/topic/${s.id}` }, `${s.id} ${s.title}`)
        : h("span", { class: "muted" }, `${s.id} ${s.title} (summary coming)`))))));

  mount(root,
    h("header", { class: "page-head" }, h("h1", {}, "Revision")),
    h("div", { class: "stats" }, paperCards),
    h("p", {}, h("a", { href: "#/spec", class: "btn btn-primary" }, "Open the spec map")),
    h("section", {}, h("h2", {}, "Summaries"), topics));
}
