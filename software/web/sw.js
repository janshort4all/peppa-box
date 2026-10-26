// Minimaler Service Worker: Seite immer frisch von der Box holen. Nur aktiv bei HTTPS
// (z. B. spaeter ueber Tailscale), bei http im Heimnetz registriert der Browser ihn nicht.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
