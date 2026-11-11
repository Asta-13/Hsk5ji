/* Зурж хайх (иероглиф). Апп ачаалагдахаас өмнө ч ажиллана — footbar-ын ✍ товчоор нээгдэнэ.
   Үгийн сан ачаалагдмагц апп HWL.lookup-г өгч, илэрцүүд гарна. */
(function(){
  var D={
    hwTitle:["Иероглифыг зураад хайх","Search by drawing","Поиск по рисунку иероглифа","文字を描いて検索"],
    hwDone:["Болсон","Done","Готово","完了"],
    hwUndo:["↶ Буцаах","↶ Undo","↶ Отменить","↶ 元に戻す"],
    hwClear:["Арилгах","Clear","Стереть","消去"],
    hwHint:["Иероглифыг хуруугаараа зураад, доороос зөвийг нь сонго.","Draw a character, then pick the right one below.","Нарисуйте иероглиф пальцем и выберите верный вариант ниже.","指で文字を描き、下から正しいものを選んでください。"],
    hwErr:["Таних үйлчилгээнд холбогдож чадсангүй. Интернетээ шалгана уу.","Could not reach the recognition service.","Не удалось подключиться к сервису распознавания. Проверьте интернет.","認識サービスに接続できません。"],
    tabDraw:["Зурах","Draw","Рисовать","描く"],
    hwLoading:["Үгийн сан ачаалж байна…","Loading the word list…","Загрузка словаря…","単語リストを読み込み中…"],
    hwNone:["Үг олдсонгүй","No matching word","Слов не найдено","該当する単語なし"]
  };
  var LI={mn:0,en:1,ru:2,ja:3};
  function lang(){var l=null;try{l=localStorage.getItem('hsk-lang')}catch(e){}return LI[l]!=null?l:'mn'}
  function t(k){return D[k][LI[lang()]]}
  var $=function(i){return document.getElementById(i)};
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function cssv(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim()||'#888'}

  var HWL=window.HWL={lookup:null,t:t,ready:function(){renderRes()}};
  var hwInk=[],hwCv=null,hwCx=null,hwDraw=false,hwT0=0,hwTm=null,hwK=1,hwSeq=0,hwAbort=null,q='',mode='foot';

  function fill(){
    var m=$('hwModal');if(!m)return;
    Array.prototype.forEach.call(m.querySelectorAll('[data-i18n]'),function(e){var k=e.getAttribute('data-i18n');if(D[k])e.textContent=t(k)});
    var s=document.querySelector('#hwTab span');if(s)s.textContent=t('tabDraw');
  }
  function hwPt(e){var r=hwCv.getBoundingClientRect();return [Math.round((e.clientX-r.left)*280/r.width),Math.round((e.clientY-r.top)*280/r.height),Math.round(performance.now()-hwT0)]}
  function hwStyle(){hwCx.strokeStyle=cssv('--fg');hwCx.lineWidth=Math.max(4,hwCv.width/40);hwCx.lineCap='round';hwCx.lineJoin='round'}
  function hwRedraw(){
    hwCx.clearRect(0,0,hwCv.width,hwCv.height);hwStyle();
    hwInk.forEach(function(st){hwCx.beginPath();st[0].forEach(function(x,i){i?hwCx.lineTo(x*hwK,st[1][i]*hwK):hwCx.moveTo(x*hwK,st[1][i]*hwK)});if(st[0].length===1)hwCx.lineTo(st[0][0]*hwK+.1,st[1][0]*hwK);hwCx.stroke()});
  }
  function hwSeg(st){var n=st[0].length;if(n<2)return;hwCx.beginPath();hwCx.moveTo(st[0][n-2]*hwK,st[1][n-2]*hwK);hwCx.lineTo(st[0][n-1]*hwK,st[1][n-1]*hwK);hwCx.stroke()}
  function hwSize(){
    if(!hwCv)return;
    var ar=$('hwArea'),w=ar.clientWidth,h=ar.clientHeight,side=Math.max(140,Math.floor(Math.min(w,h))),dpr=Math.min(window.devicePixelRatio||1,3);
    hwCv.style.width=hwCv.style.height=side+'px';hwCv.width=hwCv.height=Math.round(side*dpr);hwK=hwCv.width/280;hwRedraw();
  }
  function hwCandHint(){$('hwCand').innerHTML='<span class="hint" style="white-space:nowrap">'+esc(t('hwHint'))+'</span>'}
  function hwReset(){hwInk=[];hwT0=performance.now();clearTimeout(hwTm);hwSeq++;if(hwAbort)hwAbort.abort();if(hwCx)hwRedraw();hwCandHint()}

  function renderRes(){
    var box=$('hwRes');if(!box)return;
    if(!q){box.hidden=true;box.innerHTML='';setTimeout(hwSize,0);return}
    box.hidden=false;
    box.innerHTML=HWL.lookup?HWL.lookup(q):'<div class="hint">'+esc(t('hwLoading'))+'</div>';
    setTimeout(hwSize,0);
  }
  function setQ(v){
    q=v;$('hwQ').textContent=q;
    if(mode==='tab'){var i=$('hskQ');if(i){i.value=q;i.dispatchEvent(new Event('input',{bubbles:true}))}}
    renderRes();
  }
  function hwOpen(m){
    mode=m;fill();
    $('hwModal').hidden=false;document.body.style.overflow='hidden';
    if(!hwCv){
      hwCv=$('hwCv');hwCx=hwCv.getContext('2d');
      hwCv.addEventListener('pointerdown',function(e){e.preventDefault();hwCv.setPointerCapture(e.pointerId);hwDraw=true;clearTimeout(hwTm);if(!hwInk.length)hwT0=performance.now();var p=hwPt(e);hwInk.push([[p[0]],[p[1]],[p[2]]]);hwStyle();hwCx.beginPath();hwCx.arc(p[0]*hwK,p[1]*hwK,hwCx.lineWidth/2,0,6.3);hwCx.fillStyle=cssv('--fg');hwCx.fill()});
      hwCv.addEventListener('pointermove',function(e){if(!hwDraw)return;var ev=(e.getCoalescedEvents&&e.getCoalescedEvents())||[e];if(!ev.length)ev=[e];var st=hwInk[hwInk.length-1];ev.forEach(function(x){var p=hwPt(x);st[0].push(p[0]);st[1].push(p[1]);st[2].push(p[2]);hwSeg(st)})});
      var end=function(){if(!hwDraw)return;hwDraw=false;hwTm=setTimeout(hwRecog,120)};
      hwCv.addEventListener('pointerup',end);hwCv.addEventListener('pointercancel',end);
      window.addEventListener('resize',function(){if(!$('hwModal').hidden)hwSize()});
    }
    q=(m==='tab'&&$('hskQ'))?$('hskQ').value:'';
    $('hwQ').textContent=q;renderRes();hwSize();hwReset();
  }
  function hwClose(){$('hwModal').hidden=true;document.body.style.overflow=''}
  async function hwRecog(){
    if(!hwInk.length)return;
    var my=++hwSeq;if(hwAbort)hwAbort.abort();hwAbort=window.AbortController?new AbortController():null;
    var to=setTimeout(function(){hwAbort&&hwAbort.abort()},6000);
    try{
      var r=await fetch('https://inputtools.google.com/request?ime=handwriting&app=mobilesearch&cs=1&oe=UTF-8',{method:'POST',headers:{'Content-Type':'application/json'},signal:hwAbort?hwAbort.signal:undefined,body:JSON.stringify({options:'enable_pre_space',requests:[{writing_guide:{writing_area_width:280,writing_area_height:280},ink:hwInk,language:'zh_CN'}]})});
      var j=await r.json();if(my!==hwSeq)return;
      var c=(j&&j[0]==='SUCCESS'&&j[1]&&j[1][0]&&j[1][0][1])||[];
      $('hwCand').innerHTML=c.slice(0,16).map(function(x){return '<button class="btn ghost" type="button" data-hwpick="'+esc(x)+'" lang="zh" style="font-size:1.6rem">'+esc(x)+'</button>'}).join('')||'<span class="hint">—</span>';
      $('hwCand').scrollLeft=0;
    }catch(x){if(my!==hwSeq)return;if(x&&x.name==='AbortError'){hwCandHint();return}$('hwCand').innerHTML='<span class="hint" style="white-space:nowrap">'+esc(t('hwErr'))+'</span>'}
    finally{clearTimeout(to)}
  }
  document.addEventListener('click',function(e){
    if(e.target.closest('#hwTab')){hwOpen('foot');return}
    if(e.target.closest('#hwOpen')){hwOpen('tab');return}
    if(e.target.closest('#hwDone')){hwClose();return}
    if(e.target.closest('#hwClear')){hwReset();return}
    if(e.target.closest('#hwBack')){setQ(Array.from(q).slice(0,-1).join(''));return}
    if(e.target.closest('#hwUndo')){hwInk.pop();hwRedraw();clearTimeout(hwTm);if(hwInk.length)hwRecog();else{hwSeq++;hwCandHint()}return}
    var b=e.target.closest('[data-hwpick]');
    if(b){setQ(q+b.dataset.hwpick);hwReset()}
  });
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&$('hwModal')&&!$('hwModal').hidden)hwClose()});
  fill();   /* footbar-ын шошгыг шууд тавина */
})();
