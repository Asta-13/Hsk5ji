/* HSK app service worker: stale-while-revalidate.
   Кэшээс шууд нээгдэнэ (хурдан), ард нь шинэчлэлийг татна → шинэ хувилбар дараагийн нээлтээр гарна.
   Supabase API дуудлагыг хэзээ ч кэшлэхгүй. Бүх зүйлийг шууд шинэчлэхийг хүсвэл VER-ийг нэмж өгнө. */
var VER='hsk-v4',CORE=['./','./index.html','./manifest.json','./icon-192.png','./icon-512.png',
  './css/style.css','./js/loader.js','./js/hw-lite.js','./js/app.js','./js/sw-register.js','./data/hsk-words-a.json','./data/hsk-words-b.json','./data/hsk-mongolian.json','./data/grammar.json','./data/course-lessons.json','./data/examples.json','./data/scenarios.json','./data/radicals.json'];
self.addEventListener('install',function(e){e.waitUntil(caches.open(VER).then(function(c){return c.addAll(CORE)}).then(function(){return self.skipWaiting()}))});
self.addEventListener('activate',function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.filter(function(k){return k!==VER}).map(function(k){return caches.delete(k)}))}).then(function(){return self.clients.claim()}))});
self.addEventListener('fetch',function(e){
  var r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.hostname.indexOf('supabase.co')>-1)return;
  e.respondWith(caches.open(VER).then(function(c){
    return c.match(r).then(function(m){
      var net=fetch(r).then(function(res){
        if(res&&(res.status===200||res.type==='opaque')){c.put(r,res.clone()).catch(function(){})}
        return res;
      }).catch(function(){
        return m||(r.mode==='navigate'?c.match('./index.html'):undefined);
      });
      if(m){e.waitUntil(net.catch(function(){}));return m}
      return net;
    });
  }));
});
