// web/sw.js — BR JARVIS Progressive Web App Service Worker v41.0.3
const CACHE_NAME = "brjarvis-v41.0.3";
const ASSETS_TO_CACHE = [
  "/",
  "/web/index.html",
  "/web/style.css",
  "/web/app.js",
  "/web/manifest.json",
  "/web/galaxy.html",
  "/web/graph-data.js"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[ServiceWorker] Caching core PWA shell assets for v41.0.3");
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log("[ServiceWorker] Clearing legacy cache", cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Always bypass Service Worker cache for API routes, WebSockets, health, and dynamic endpoints
  if (
    event.request.method !== "GET" ||
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/v1/") ||
    url.pathname.startsWith("/ws") ||
    url.pathname.startsWith("/mobile/") ||
    url.pathname === "/health" ||
    event.request.headers.get("Accept")?.includes("text/event-stream")
  ) {
    return; // Pass through to network natively
  }

  // Network-first for JavaScript and HTML to ensure immediate upgrade propagation
  if (url.pathname.endsWith(".js") || url.pathname.endsWith(".html") || url.pathname === "/") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request, { ignoreSearch: true }))
    );
    return;
  }

  // Handle other static assets with cache-first
  event.respondWith(
    caches.match(event.request, { ignoreSearch: true }).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).catch((err) => {
        if (
          event.request.mode === "navigate" ||
          (event.request.headers.get("Accept") && event.request.headers.get("Accept").includes("text/html"))
        ) {
          return caches.match("/web/index.html", { ignoreSearch: true });
        }
        throw err;
      });
    })
  );
});
