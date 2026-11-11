/* Бүх JSON-г зэрэг татаад, дараа нь app.js-ийг ачаална. */
(function(){
  var FILES={
  "HSKRAW": "data/hsk-words-a.json",
  "HSKRAW3": "data/hsk-words-b.json",
  "HSKI18N_RAW": "data/hsk-translations.json",
  "GRAMI18N": "data/grammar-translations.json",
  "HSKMN_RAW": "data/hsk-mongolian.json",
  "GRAM_RAW": "data/grammar.json",
  "CI18N": "data/course-translations.json",
  "LESSONS": "data/course-lessons.json",
  "RAD": "data/radicals.json",
  "EXD": "data/examples.json",
  "SCN": "data/scenarios.json"
};
  var GLOBALS=["HSKRAW", "HSKRAW3", "HSKI18N_RAW", "GRAMI18N"];
  var names=Object.keys(FILES);
  Promise.all(names.map(function(k){
    return fetch(FILES[k]).then(function(r){
      if(!r.ok) throw new Error(FILES[k]+' '+r.status);
      return r.json();
    });
  })).then(function(vals){
    var DATA={};
    names.forEach(function(k,i){DATA[k]=vals[i]});
    window.DATA=DATA;
    GLOBALS.forEach(function(k){window[k]=DATA[k]});   // HSKRAW гэх мэт глобал хувьсагчид
    var s=document.createElement('script');
    s.src='js/app.js';
    document.body.appendChild(s);
  }).catch(function(e){
    document.body.insertAdjacentHTML('afterbegin',
      '<pre style="padding:16px;color:#b00">Өгөгдөл ачаалж чадсангүй: '+e.message+
      '\n(file:// биш, сервер/GitHub Pages/Live Server дээр нээнэ үү)</pre>');
  });
})();
