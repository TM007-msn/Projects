// Service worker: makes the dashboard installable and lets the page shell open offline.
// API calls always go to the network so you never see stale tasks.
const CACHE = "planner-shell-v1";
const SHELL = ["/", "/index.html", "/styles.css", "/app.js", "/manifest.json", "/icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.pathname.startsWith("/api") || url.pathname.startsWith("/mcp")) return;
  // Network first, cached shell as fallback.
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
