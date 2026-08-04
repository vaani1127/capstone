/// <reference lib="webworker" />
declare const self: ServiceWorkerGlobalScope;

// Vite PWA injection point - eslint-disable-next-line @typescript-eslint/no-unused-expressions
declare const __WB_MANIFEST: unknown;

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event: unknown) => {
  (event as ExtendableEvent).waitUntil(self.clients.claim());
});

self.addEventListener('push', (event: unknown) => {
  const pushEvent = event as PushEvent;
  if (!pushEvent.data) return;

  let payload: Record<string, unknown> = {};
  try {
    payload = pushEvent.data.json() as Record<string, unknown>;
  } catch {
    payload = { title: 'HealthSaathi', body: pushEvent.data.text() };
  }

  const title = (payload.title as string) || 'HealthSaathi';
  const notificationOptions = {
    body: (payload.body as string) || '',
    tag: (payload.tag as string) || undefined,
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    requireInteraction: false,
  };

  pushEvent.waitUntil(self.registration.showNotification(title, notificationOptions));
});

self.addEventListener('notificationclick', (event: unknown) => {
  const notifEvent = event as NotificationEvent;
  notifEvent.notification.close();
  notifEvent.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      if (clients.length > 0) {
        return clients[0].focus();
      }
      return self.clients.openWindow('/');
    })
  );
});
