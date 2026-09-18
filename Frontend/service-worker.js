/* MEDIKOISK — Service Worker for PWA */

const CACHE_NAME = 'medikoisk-v6';
const STATIC_ASSETS = [
  './',
  './index.html',
  './api.js',
  './manifest.json',
  './icon.svg',
  './icon.png',
];

// ═══ Install — cache static assets ═══
self.addEventListener('install', (event) => {
  console.log('[SW] Installing…');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .catch((err) => console.warn('[SW] Cache addAll failed:', err))
  );
  self.skipWaiting();
});

// ═══ Activate — clean up old caches ═══
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating…');
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ═══ Fetch ═══
self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Don't intercept cross-origin requests (backend API calls)
  if (url.origin !== self.location.origin) return;

  // Don't cache API paths
  if (
    url.pathname.startsWith('/auth') ||
    url.pathname.startsWith('/bootstrap') ||
    url.pathname.startsWith('/appointments') ||
    url.pathname.startsWith('/prescriptions') ||
    url.pathname.startsWith('/reports') ||
    url.pathname.startsWith('/payments') ||
    url.pathname.startsWith('/vitals') ||
    url.pathname.startsWith('/change-requests') ||
    url.pathname.startsWith('/timeline') ||
    url.pathname.startsWith('/chats') ||
    url.pathname.startsWith('/users') ||
    url.pathname.startsWith('/ai')
  ) return;

  // ── CRITICAL FIX: Network-First for navigation ──
  // This prevents ERR_FAILED. It always tries to fetch the page from
  // Cloudflare first. Only if the network fails (offline) does it
  // fall back to serving index.html from the cache.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // If we got a valid response, save it to the cache and return it
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() => {
          // Network failed, serve index.html from cache
          return caches.match('./index.html');
        })
    );
    return;
  }

  // Cache-first for other static assets (CSS, JS, images)
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request)
        .then((response) => {
          if (response.ok && response.type === 'basic') {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        });
    })
  );
});
