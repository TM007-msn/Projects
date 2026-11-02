// Thin wrappers around fetch. All requests send the session cookie
// (same-origin) and POST JSON, which the server requires.

export class AuthError extends Error {}

async function request(method, url, body) {
  const res = await fetch(url, {
    method,
    credentials: "same-origin",
    headers: body !== undefined ? { "Content-Type": "application/json" } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch { /* not JSON */ }
    if (typeof detail !== "string") detail = "Request failed";
    // 401 means "log in" everywhere except the login call itself, where the
    // server's message ("Wrong password") is what the user needs to see.
    if (res.status === 401) throw new AuthError(detail);
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  session: () => request("GET", "/api/session"),
  login: (password) => request("POST", "/api/login", { password }),
  logout: () => request("POST", "/api/logout", {}),
  events: () => request("GET", "/api/events"),
  postEvents: (events) => request("POST", "/api/events", { events }),
  /** Content JSON, e.g. content("spec.json"). Resolves to null on 404. */
  content: async (path) => {
    try {
      return await request("GET", `/content/${path}`);
    } catch (err) {
      if (err instanceof AuthError) throw err;
      if (/not found/i.test(err.message)) return null;
      throw err;
    }
  },
};
