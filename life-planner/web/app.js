// Life Planner dashboard. Talks to the REST API at /api; the AI changes the same data through /mcp.

const GROUPS = [
  ["overdue", "Overdue"],
  ["today", "Today"],
  ["this_week", "Next 7 days"],
  ["later", "Later"],
  ["no_date", "No date"],
];
const TZ = "Europe/London";
const fmtDue = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: TZ });
const fmtTime = new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: TZ });
const fmtToday = new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: TZ });

let tasksById = {};
let editingId = null;

// ---------- API helper (handles the optional PLANNER_TOKEN) ----------

async function api(path, options = {}) {
  const token = getToken();
  const headers = { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  const response = await fetch(`/api${path}`, { ...options, headers });
  if (response.status === 401) {
    const entered = prompt("Enter your planner token:");
    if (entered) { setToken(entered); return api(path, options); }
    throw new Error("Token required");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

function getToken() { try { return localStorage.getItem("planner-token"); } catch { return null; } }
function setToken(value) { try { localStorage.setItem("planner-token", value); } catch { /* private mode */ } }

// ---------- Rendering ----------

function relative(iso) {
  const days = Math.round((new Date(iso) - new Date()) / 86400000);
  if (days === 0) return "";
  if (days > 0) return days === 1 ? "tomorrow" : `in ${days} days`;
  return days === -1 ? "1 day late" : `${-days} days late`;
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  node.append(...children.filter((c) => c !== null && c !== undefined && c !== ""));
  return node;
}

function taskRow(task) {
  const due = task.due_at ? `${fmtDue.format(new Date(task.due_at))}${relative(task.due_at) ? " · " + relative(task.due_at) : ""}` : null;
  return el("div", { class: `task p${task.priority}` },
    el("input", { type: "checkbox", "aria-label": `Complete ${task.title}`, onchange: () => complete(task) }),
    el("div", {},
      el("button", { class: "title", type: "button", onclick: () => openEdit(task.id) }, task.title),
      el("div", { class: "meta" },
        task.module_code ? el("span", { class: "chip" }, task.module_code) : null,
        task.source === "ai" ? el("span", { class: "chip ai", title: "Added by the AI" }, "AI") : null,
        due ? el("span", {}, due) : null,
        task.estimate_mins ? el("span", {}, `~${task.estimate_mins} min`) : null,
      ),
    ),
  );
}

async function loadTasks() {
  const overview = await api("/overview");
  tasksById = {};
  const container = document.getElementById("tasks");
  container.replaceChildren();
  for (const [key, label] of GROUPS) {
    const items = overview[key];
    items.forEach((t) => (tasksById[t.id] = t));
    if (!items.length && (key === "overdue" || key === "later" || key === "no_date")) continue;
    container.append(el("div", { class: `group ${key}` },
      el("h2", {}, label, el("span", { class: "count" }, items.length ? `${items.length}` : "")),
      ...(items.length ? items.map(taskRow) : [el("p", { class: "empty" }, key === "today" ? "Nothing due today." : "Nothing here.")]),
    ));
  }
}

async function loadActivity() {
  const changes = await api("/activity?limit=15");
  const list = document.getElementById("activity");
  list.replaceChildren(...changes.map((c) =>
    el("li", { class: c.undone ? "undone" : "" },
      el("div", {},
        el("div", { class: "what" }, c.actor === "ai" ? el("span", { class: "chip ai" }, "AI") : null, " ", c.summary),
        el("div", { class: "when" }, `${fmtTime.format(new Date(c.at))} · ${c.actor}`),
      ),
      c.can_undo ? el("button", { class: "ghost", type: "button", onclick: () => undo(c.id) }, "Undo") : el("span"),
    ),
  ));
  if (!changes.length) list.append(el("li", {}, el("span", { class: "muted" }, "No changes yet.")));
}

async function refresh() {
  try {
    await Promise.all([loadTasks(), loadActivity()]);
  } catch (error) {
    toast(error.message);
  }
}

// ---------- Actions ----------

async function run(action, message) {
  try {
    await action();
    if (message) toast(message);
  } catch (error) {
    toast(error.message);
  }
  await refresh();
}

function complete(task) {
  return run(() => api(`/tasks/${task.id}`, { method: "PATCH", body: JSON.stringify({ status: "done" }) }), `Done: ${task.title}`);
}

function undo(changeId) {
  return run(() => api(`/activity/${changeId}/undo`, { method: "POST" }), "Undone");
}

// <input type="datetime-local"> wants "YYYY-MM-DDTHH:MM" in UK time.
function toInputValue(iso) {
  if (!iso) return "";
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23", timeZone: TZ })
      .formatToParts(new Date(iso)).map((p) => [p.type, p.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

function openEdit(id) {
  const task = tasksById[id];
  const form = document.getElementById("edit-form");
  editingId = id;
  form.elements.title.value = task.title;
  form.elements.due_at.value = toInputValue(task.due_at);
  form.elements.module_code.value = task.module_code || "";
  form.elements.priority.value = String(task.priority);
  form.elements.estimate_mins.value = task.estimate_mins ?? "";
  form.elements.notes.value = task.notes || "";
  document.getElementById("edit").showModal();
}

document.getElementById("edit").addEventListener("close", (event) => {
  const dialog = event.target;
  if (dialog.returnValue !== "save" || editingId === null) return;
  const form = document.getElementById("edit-form");
  const body = {
    title: form.elements.title.value.trim(),
    due_at: form.elements.due_at.value || null,
    module_code: form.elements.module_code.value.trim() || null,
    priority: Number(form.elements.priority.value),
    estimate_mins: form.elements.estimate_mins.value === "" ? null : Number(form.elements.estimate_mins.value),
    notes: form.elements.notes.value,
  };
  run(() => api(`/tasks/${editingId}`, { method: "PATCH", body: JSON.stringify(body) }), "Saved");
});

document.getElementById("delete-task").addEventListener("click", () => {
  const id = editingId;
  document.getElementById("edit").close("cancel");
  run(() => api(`/tasks/${id}`, { method: "DELETE" }), "Deleted (you can undo it)");
});

document.getElementById("add-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.target;
  const body = {
    title: form.elements.title.value.trim(),
    due_at: form.elements.due_at.value || null,
    module_code: form.elements.module_code.value.trim() || null,
    priority: Number(form.elements.priority.value),
  };
  run(async () => {
    await api("/tasks", { method: "POST", body: JSON.stringify(body) });
    form.reset();
    form.elements.title.focus();
  }, "Added");
});

let toastTimer;
function toast(message) {
  const node = document.getElementById("toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove("show"), 2500);
}

// ---------- Start-up ----------

document.getElementById("today").textContent = fmtToday.format(new Date());
document.getElementById("refresh").addEventListener("click", refresh);
// Pick up changes the AI made while the tab was in the background.
document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });
setInterval(refresh, 60_000);
refresh();

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
