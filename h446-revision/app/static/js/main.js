// Entry point: checks the session, loads content, and routes between views.
//
// Routes (hash-based so the server only ever serves index.html):
//   #/              home
//   #/spec          spec map
//   #/topic/1.1.1   summary for a subtopic

import { api, AuthError } from "./api.js";
import { h, mount, toast } from "./lib/dom.js";
import { loadAll, store, subscribe } from "./store.js";
import { applySavedTheme, toggleTheme } from "./ui/controls.js";
import { renderHome } from "./views/home.js";
import { renderLogin } from "./views/login.js";
import { refreshSpecMap, renderSpecMap } from "./views/specmap.js";
import { renderSummary } from "./views/summary.js";

const root = document.getElementById("app");
const nav = document.getElementById("nav");
const syncStatus = document.getElementById("sync-status");
let current = null; // { refresh(), destroy() } for the view on screen

applySavedTheme();
document.getElementById("theme-toggle").addEventListener("click", toggleTheme);
document.getElementById("logout").addEventListener("click", async () => {
  await api.logout().catch(() => {});
  showLogin();
});
window.addEventListener("auth-required", showLogin);

function showLogin() {
  nav.hidden = true;
  current?.destroy?.();
  current = null;
  renderLogin(root, start);
}

async function start() {
  try {
    const { authenticated } = await api.session();
    if (!authenticated) return showLogin();
    await loadAll();
  } catch (err) {
    if (err instanceof AuthError) return showLogin();
    mount(root, h("div", { class: "card" },
      h("h1", {}, "Couldn't load"),
      h("p", {}, err.message),
      h("button", { class: "btn btn-primary", onclick: start }, "Try again")));
    return;
  }
  nav.hidden = false;
  route();
}

async function route() {
  current?.destroy?.();
  current = null;
  const path = location.hash.replace(/^#/, "") || "/";
  const topic = path.match(/^\/topic\/(\d\.\d\.\d)$/);
  // Highlight the nav link for this page (summary pages count as Home).
  const activeHref = path === "/spec" ? "#/spec" : "#/";
  for (const a of nav.querySelectorAll("a")) {
    a.setAttribute("aria-current", a.getAttribute("href") === activeHref ? "page" : "false");
  }
  try {
    if (path === "/spec") {
      renderSpecMap(root);
      current = { refresh: () => refreshSpecMap(root) };
    } else if (topic) {
      current = await renderSummary(root, topic[1]);
    } else {
      await renderHome(root);
      current = { refresh: () => renderHome(root) };
    }
  } catch (err) {
    if (err instanceof AuthError) return showLogin();
    toast(err.message);
  }
  root.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

window.addEventListener("hashchange", () => { if (store.spec) route(); });

subscribe(() => {
  current?.refresh?.();
  const n = store.pending.length;
  syncStatus.hidden = n === 0;
  syncStatus.textContent = n === 1 ? "1 change waiting to sync" : `${n} changes waiting to sync`;
});

start();
