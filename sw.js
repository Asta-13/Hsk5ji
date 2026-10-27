/* HSK app service worker: network-first for the page (updates arrive at once), cache fallback when offline.
   Supabase API calls are never cached. Bump VER to force a refresh of old caches. */
var VER='hsk-v1',CORE=['./','./index.html','./manifest.json','./icon-192.png','./icon-512.png'];
self.addEventListener('install',function(e){e.waitUntil(caches.open(VER).then(function(c){return c.addAll(CORE)}).then(function(){return self.skipWaiting()}))});
self.addEventListener('activate',function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.filter(function(k){return k!==VER}).map(function(k){return caches.delete(k)}))}).then(function(){return self.clients.claim()}))});
self.addEventListener('fetch',function(e){
  var r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.hostname.indexOf('supabase.co')>-1)return;
  e.respondWith(fetch(r).then(function(res){
    if(res&&(res.ok||res.type==='opaque')){var cp=res.clone();caches.open(VER).then(function(c){c.put(r,cp)})}
    return res;
  }).catch(function(){return caches.match(r).then(function(m){return m||(r.mode==='navigate'?caches.match('./index.html'):undefined)})}));
});
