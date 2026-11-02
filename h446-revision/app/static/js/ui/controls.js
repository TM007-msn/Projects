// Reusable controls: the 3-state rating buttons and the verify / flag buttons
// that sit on every generated content item.

import { h, toast } from "../lib/dom.js";
import { RATING_LABELS, formatDateUK } from "../lib/derive.js";
import { isFlagged, isVerified, record, store } from "../store.js";

const SHORT = { need: "Need", once: "Once", got: "Got it" };

/**
 * Three buttons (Need to revise / Revised once / Got it) for a spec point or
 * sub-item. Behaves like a radio group: arrow keys move between options.
 */
export function ratingControl(targetId, label) {
  const current = store.ratings.get(targetId);
  const group = h("div", { class: "rating", role: "radiogroup", "aria-label": `Rate ${label}` });
  const values = ["need", "once", "got"];
  for (const value of values) {
    const checked = current?.value === value;
    const btn = h("button", {
      type: "button",
      class: `rating-btn rating-${value}`,
      role: "radio",
      "aria-checked": checked ? "true" : "false",
      tabindex: checked || (!current && value === "need") ? "0" : "-1",
      title: RATING_LABELS[value],
      onclick: () => {
        if (current?.value !== value) record("rating", targetId, { value });
      },
      onkeydown: (e) => {
        const i = values.indexOf(value);
        const step = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1
          : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
        if (!step) return;
        e.preventDefault();
        group.children[(i + step + values.length) % values.length].focus();
      },
    }, SHORT[value]);
    group.append(btn);
  }
  return group;
}

/** "Reviewed 02/11/2026" or "Not reviewed". */
export function reviewedLabel(ts) {
  return h("span", { class: "reviewed" }, ts ? `Reviewed ${formatDateUK(ts)}` : "Not reviewed");
}

/** Badge plus Verify and Flag buttons for one content item. */
export function itemActions(item) {
  const verified = isVerified(item);
  const flag = store.flags.get(item.id);
  const wrap = h("div", { class: "item-actions" });

  if (flag) {
    wrap.append(h("span", { class: "badge badge-flag", title: flag.note || "Flagged" },
      flag.note ? `Flagged: ${flag.note}` : "Flagged"));
  }
  if (!verified) wrap.append(h("span", { class: "badge badge-unverified" }, "Unverified"));

  wrap.append(
    h("button", {
      type: "button",
      class: `chip ${verified ? "chip-on" : ""}`,
      "aria-pressed": verified ? "true" : "false",
      disabled: item.verified === true,           // verified in the JSON itself
      title: item.verified === true ? "Verified in the content file" : "Mark as checked and correct",
      onclick: () => {
        record(verified ? "unverify" : "verify", item.id);
        toast(verified ? "Marked unverified" : "Marked verified");
      },
    }, verified ? "✓ Verified" : "Verify"),
    flag
      ? h("button", {
        type: "button", class: "chip chip-warn",
        onclick: () => { record("unflag", item.id); toast("Flag removed"); },
      }, "Unflag")
      : h("button", { type: "button", class: "chip", onclick: () => openFlagDialog(item) }, "⚑ Flag as wrong"),
  );
  return wrap;
}

/** Modal asking for an optional note, then records a flag event. */
function openFlagDialog(item) {
  const note = h("textarea", { id: "flag-note", rows: "3", maxlength: "500",
    placeholder: "What's wrong? (optional)" });
  const dialog = h("dialog", { class: "dialog", "aria-labelledby": "flag-title" },
    h("form", { method: "dialog" },
      h("h2", { id: "flag-title" }, "Flag as wrong"),
      h("p", { class: "muted" }, "Flagged items are hidden from tests until you fix them."),
      h("label", { for: "flag-note" }, "Note"),
      note,
      h("div", { class: "dialog-buttons" },
        h("button", { type: "submit", value: "cancel", class: "btn btn-ghost" }, "Cancel"),
        h("button", { type: "submit", value: "flag", class: "btn btn-warn" }, "Flag"))));
  dialog.addEventListener("close", () => {
    if (dialog.returnValue === "flag") {
      record("flag", item.id, { note: note.value.trim() });
      toast("Flagged");
    }
    dialog.remove();
  });
  document.body.append(dialog);
  dialog.showModal();
  note.focus();
}

// ---- theme ----------------------------------------------------------------

const THEME_KEY = "h446.theme";

/** Apply the saved theme (light / dark) or follow the system setting. */
export function applySavedTheme() {
  let saved = null;
  try { saved = localStorage.getItem(THEME_KEY); } catch { /* blocked */ }
  if (saved) document.documentElement.dataset.theme = saved;
}

export function toggleTheme() {
  const root = document.documentElement;
  const isDark = root.dataset.theme
    ? root.dataset.theme === "dark"
    : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = isDark ? "light" : "dark";
  try { localStorage.setItem(THEME_KEY, root.dataset.theme); } catch { /* blocked */ }
}
