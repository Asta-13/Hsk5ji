/* HSK app service worker: stale-while-revalidate.
   Кэшээс шууд нээгдэнэ (хурдан), ард нь шинэчлэлийг татна → шинэ хувилбар дараагийн нээлтээр гарна.
   Supabase API дуудлагыг хэзээ ч кэшлэхгүй. Бүх зүйлийг шууд шинэчлэхийг хүсвэл VER-ийг нэмж өгнө. */
var VER='hsk-v12',CORE=['./','./index.html','./manifest.json','./icon-192.png','./icon-512.png',
  './css/style.css','./js/loader.js','./js/hw-lite.js','./js/vendor/supabase.min.js','./js/vendor/hanzi-writer.min.js','./js/app.js','./js/sw-register.js','./data/hsk-words-a.json','./data/hsk-words-b.json','./data/hsk-mongolian.json','./data/grammar.json','./data/course-lessons.json','./data/examples.json','./data/scenarios.json','./data/radicals.json'];
var OPT=['./data/hsk-translations.json','./data/grammar-translations.json','./data/course-translations.json'];
/* Орчуулгын том файлуудыг offline-д зориулж ард нь (алдаа гарвал үл тоон) кэшлэнэ */
self.addEventListener('install',function(e){e.waitUntil(caches.open(VER).then(function(c){return c.addAll(CORE).then(function(){return Promise.all(OPT.map(function(u){return c.add(u).catch(function(){})}))})}).then(function(){return self.skipWaiting()}))});
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
