// 最小限のサービスワーカー。アプリシェルをキャッシュし、
// データ(index.json / history)は常にネットワーク優先で最新を取得する。
const CACHE = "price-monitor-v1";
const SHELL = ["./", "index.html", "manifest.json", "icon-192.png", "icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // データは network-first（古い価格を見せない）
  if (url.pathname.includes("/data/")) {
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    return;
  }
  // それ以外（アプリシェル）は cache-first
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
