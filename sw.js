/* HSK app service worker: stale-while-revalidate.
   Кэшээс шууд нээгдэнэ (хурдан), ард нь шинэчлэлийг татна → шинэ хувилбар дараагийн нээлтээр гарна.
   Supabase API дуудлагыг хэзээ ч кэшлэхгүй. Бүх зүйлийг шууд шинэчлэхийг хүсвэл VER-ийг нэмж өгнө.
   Татахдаа браузерын HTTP кэшийг тойрч (no-cache / reload) шалгана: GitHub Pages 10 мин кэшлэдэг тул index.html шинэ, app.js хуучин гэсэн үл тохирол гарахаас сэргийлнэ. */
var VER='hsk-v51',CORE=['./','./index.html','./manifest.json','./icon-192.png','./icon-512.png',
  './css/style.css','./js/loader.js','./js/hanzi.js','./js/hw-lite.js','./js/vendor/supabase.min.js','./js/vendor/hanzi-writer.min.js','./js/app.js','./js/sw-register.js','./data/hsk-words.json','./data/hsk-mongolian.json','./data/grammar.json','./data/course-lessons.json','./data/examples.json','./data/scenarios.json','./data/radicals.json'];
var OPT=['./data/hsk-translations.json','./data/grammar-translations.json','./data/course-translations.json'];
/* Орчуулгын том файлуудыг offline-д зориулж ард нь (алдаа гарвал үл тоон) кэшлэнэ */
self.addEventListener('install',function(e){e.waitUntil(caches.open(VER).then(function(c){return Promise.all(CORE.map(function(u){return c.add(new Request(u,{cache:'reload'}))})).then(function(){return Promise.all(OPT.map(function(u){return c.add(new Request(u,{cache:'reload'})).catch(function(){})}))})}).then(function(){return self.skipWaiting()}))});
self.addEventListener('activate',function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.filter(function(k){return k!==VER&&k!=='hsk-books'}).map(function(k){return caches.delete(k)}))}).then(function(){return self.clients.claim()}))});
self.addEventListener('fetch',function(e){
  var r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.hostname.indexOf('supabase.co')>-1)return;
  /* mp3/mp4-ийг SW-ээр дамжуулахгүй: iOS/Safari Range(206) хүсэлтэд кэшийн 200 хариу өгвөл тоглохгүй */
  if(/\.(mp3|mp4|m4a|wav|ogg|webm)$/i.test(u.pathname))return;
  /* ном хуудасны зураг: кэшээс эхлээд (өөрчлөгддөггүй), офлайнд ч уншина */
  if(/\/data\/books\/.*\.webp$/.test(u.pathname)){
    e.respondWith(caches.open('hsk-books').then(function(c){return c.match(r).then(function(m){return m||fetch(r).then(function(res){if(res&&res.status===200)c.put(r,res.clone()).catch(function(){});return res})})}));return}
  /* media жагсаалт: эхлээд сүлжээнээс (шинэ файл шууд харагдана), офлайн бол кэшээс */
  if(/\/data\/(media|media-auto|stories|world|world-dict|news)\.json$/.test(u.pathname)||/\/data\/books\//.test(u.pathname)){
    e.respondWith(fetch(r,{cache:'no-store'}).then(function(res){var cp=res.clone();caches.open(VER).then(function(c){c.put(r,cp)}).catch(function(){});return res}).catch(function(){return caches.match(r)}));return}
  e.respondWith(caches.open(VER).then(function(c){
    return c.match(r).then(function(m){
      var net=fetch(r,{cache:'no-cache'}).then(function(res){
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
