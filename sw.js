const CACHE='hs7000-v1.5.1';
const ASSETS=['./','./index.html','./styles.css','./app.js','./manifest.webmanifest','./data/gsat-corpus-stats.json','./data/vocabulary-zh.json','./data/vocabulary-details.json','./data/vocabulary-examples.json','./icons/icon-192.png','./icons/icon-512.png'];
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)))});
self.addEventListener('activate',e=>e.waitUntil(Promise.all([self.clients.claim(),caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))])));
self.addEventListener('fetch',e=>{e.respondWith(caches.match(e.request).then(hit=>hit||fetch(e.request).then(res=>{if(e.request.method==='GET'&&res.ok){const copy=res.clone();caches.open(CACHE).then(c=>c.put(e.request,copy))}return res}).catch(()=>caches.match('./index.html'))))});
