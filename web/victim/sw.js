// Guardian victim app service worker: caches ONLY the static shell. Never touches API/SSE calls.
const CACHE = "guardian-victim-shell-v1";
const SHELL = ["./", "index.html", "style.css", "app.js", "manifest.webmanifest"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const SHELL_PATHS = new Set(SHELL.map((p) => new URL(p, self.registration.scope).pathname));

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (!SHELL_PATHS.has(url.pathname)) return;   // API, SSE, everything else: straight to network
  // Network first (so edits show up), fall back to the cached shell when offline.
  e.respondWith(
    fetch(req)
      .then((res) => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
        return res;
      })
      .catch(() => caches.match(req, { ignoreSearch: true }))
  );
});
