/* Ачаалагч: өгөгдөл, app.js, supabase-г зэрэг татаж, ачаалах дэлгэц харуулна.
   Орчуулгын том JSON-ууд (en/ru/ja) зөвхөн тэр хэл сонгосон үед л татагдана. */
(function(){
  var CORE={
    HSKRAW:'data/hsk-words-a.json', HSKRAW3:'data/hsk-words-b.json',
    HSKMN_RAW:'data/hsk-mongolian.json', GRAM_RAW:'data/grammar.json',
    LESSONS:'data/course-lessons.json', EXD:'data/examples.json',
    SCN:'data/scenarios.json', RAD:'data/radicals.json'
  };
  var I18N={
    HSKI18N_RAW:'data/hsk-translations.json',
    GRAMI18N:'data/grammar-translations.json',
    CI18N:'data/course-translations.json'
  };
  var SUPABASE='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js';
  var DATA=window.DATA={};
  window.HSKI18N_RAW={}; window.GRAMI18N={}; window.__i18nReady=false;

  var $=function(i){return document.getElementById(i)};
  var total=0,done=0;
  function tick(){done++;var b=$('bootBar'),t=$('bootT');
    if(b)b.style.width=Math.min(96,Math.round(done*100/total))+'%';
    if(t)t.textContent='Ачаалж байна… '+done+'/'+total}
  function track(p){total++;return p.then(function(v){tick();return v},function(e){tick();throw e})}

  function getJSON(f){return fetch(f).then(function(r){
    if(!r.ok)throw new Error(f+' → '+r.status);return r.json()})}
  function getText(f){return fetch(f).then(function(r){
    if(!r.ok)throw new Error(f+' → '+r.status);return r.text()})}
  function loadScript(src,ms){return new Promise(function(res){
    var s=document.createElement('script'),t=setTimeout(res,ms||15000);
    s.src=src;s.onload=s.onerror=function(){clearTimeout(t);res()};
    document.head.appendChild(s)})}
  function loadSet(map){var keys=Object.keys(map);
    return Promise.all(keys.map(function(k){return getJSON(map[k]).then(function(v){DATA[k]=v})}))}
  function exposeI18N(){window.HSKI18N_RAW=DATA.HSKI18N_RAW||{};window.GRAMI18N=DATA.GRAMI18N||{};window.__i18nReady=true}

  /* хэл солиход шаардлагатай орчуулгыг дараа нь татна */
  var i18nWait=null;
  window.loadI18N=function(cb){
    if(window.__i18nReady){cb();return}
    if(i18nWait){i18nWait.push(cb);return}
    i18nWait=[cb];
    loadSet(I18N).catch(function(){}).then(function(){
      exposeI18N();
      if(window.__applyI18N)window.__applyI18N();
      var q=i18nWait;i18nWait=null;q.forEach(function(f){f()})
    })};

  var booted=false;
  window.__bootDone=function(){
    if(booted)return;booted=true;
    var b=$('boot');if(!b)return;
    b.classList.add('hide');setTimeout(function(){b.parentNode&&b.parentNode.removeChild(b)},350)};

  var failed=false;
  function fail(e){
    failed=true;
    var b=$('boot');if(!b)return;
    b.innerHTML='<div class="bt">Ачаалж чадсангүй.<br><small>'+String(e&&e.message||e)+
      '</small><br><small>(file:// биш, сервер / GitHub Pages дээр нээнэ үү)</small></div>'+
      '<button onclick="location.reload()">Дахин оролдох</button>'}

  var saved=null;try{saved=localStorage.getItem('hsk-lang')}catch(e){}
  var needI18N=saved==='en'||saved==='ru'||saved==='ja';

  var jobs=[
    track(loadSet(CORE)),
    track(getText('js/app.js')),
    track(loadScript(SUPABASE))
  ];
  if(needI18N)jobs.push(track(loadSet(I18N).then(exposeI18N)));

  Promise.all(jobs).then(function(r){
    window.HSKRAW=DATA.HSKRAW;window.HSKRAW3=DATA.HSKRAW3;   /* апп эдгээрийг глобалаар уншдаг */
    window.addEventListener('error',function(ev){            /* эхлэхэд унавал хоосон биш, алдааг харуулна */
      if(!booted)fail(ev.error||ev.message)});
    var s=document.createElement('script');
    s.text=r[1]+'\n//# sourceURL=js/app.js';
    document.body.appendChild(s);
    var b=$('bootBar');if(b)b.style.width='100%';
    setTimeout(function(){if(!failed)window.__bootDone()},12000);   /* аюулгүйн хугацаа */
  }).catch(fail);
})();
