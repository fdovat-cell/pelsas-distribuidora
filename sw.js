// Network-only: siempre sirve desde la red, sin caché local
const CACHE_NAME = 'pelsas-v3';

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', e => {
  // Borrar TODOS los caches viejos
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Siempre red, nunca caché
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(fetch(e.request));
});
