// Login screen: one password field.

import { api } from "../api.js";
import { h, mount } from "../lib/dom.js";

export function renderLogin(root, onSuccess) {
  const input = h("input", {
    type: "password", id: "password", name: "password", autocomplete: "current-password",
    required: true, autofocus: true,
  });
  const error = h("p", { class: "error", role: "alert" });
  const button = h("button", { type: "submit", class: "btn btn-primary btn-block" }, "Log in");

  const form = h("form", {
    class: "card login",
    onsubmit: async (e) => {
      e.preventDefault();
      button.disabled = true;
      error.textContent = "";
      try {
        await api.login(input.value);
        onSuccess();
      } catch (err) {
        error.textContent = err.message;
        input.select();
      } finally {
        button.disabled = false;
      }
    },
  },
  h("h1", {}, "H446 Revision"),
  h("label", { for: "password" }, "Password"),
  input,
  error,
  button);

  mount(root, form);
  input.focus();
}
