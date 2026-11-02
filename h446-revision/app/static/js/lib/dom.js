// Tiny helper for building DOM elements without innerHTML.
//
//   h("button", { class: "btn", onclick: save, "aria-pressed": "true" }, "Save")
//
// Strings become text nodes, so user-typed text (flag notes) can never inject
// HTML. Attribute rules:
//   class / text      set className / textContent
//   on<event>         addEventListener(event, fn)
//   dataset           object copied onto el.dataset
//   true / false      boolean attribute present / absent
//   anything else     setAttribute(name, value)

export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") el.className = value;
    else if (key === "text") el.textContent = value;
    else if (key === "dataset") Object.assign(el.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2), value);
    else if (value === true) el.setAttribute(key, "");
    else el.setAttribute(key, String(value));
  }
  append(el, children);
  return el;
}

function append(el, children) {
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

/** Replace everything inside `el`. */
export function mount(el, ...children) {
  el.replaceChildren();
  append(el, children);
}

/** Show a short message at the bottom of the screen. */
export function toast(message) {
  const box = document.getElementById("toast");
  if (!box) return;
  box.textContent = message;
  box.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => box.classList.remove("show"), 2500);
}
