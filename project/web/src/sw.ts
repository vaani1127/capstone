/// <reference lib="webworker" />

declare const self: ServiceWorkerGlobalScope;

// Vite PWA injection point
declare global {
  interface ServiceWorkerGlobalScope {
    __WB_MANIFEST: unknown;
  }
}

// eslint-disable-next-line @typescript-eslint/no-unused-expressions
self.__WB_MANIFEST;

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event: ExtendableEvent) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event: PushEvent) => {
  if (!event.data) return;

  let payload: { title?: string; body?: string; tag?: string } = {};
  try {
    payload = event.data.json() as { title?: string; body?: string; tag?: string };
  } catch {
    payload = { title: 'HealthSaathi', body: event.data.text() };
  }

  const title = payload.title || 'HealthSaathi';
  const options: NotificationOptions = {
    body: payload.body || '',
    tag: payload.tag,
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    vibrate: [200, 100, 200],
    requireInteraction: false,
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event: NotificationEvent) => {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      if (clients.length > 0) {
        return clients[0].focus();
      }
      return self.clients.openWindow('/');
    })
  );
});
