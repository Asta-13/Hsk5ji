/* Ханзи багш (汉字老师) — аппын сахиус. Бүх мэдэгдлийг тэр хэлнэ.
   Улаан тамга (印) биетэй, нүдний шилтэй, малгайтай багш. Сэтгэл санаа: hi · cheer · oops · think · sleep
   API: Hanzi.say(текст, сэтгэл?)  Hanzi.mount(элемент, сэтгэл?)  Hanzi.mood(элемент, сэтгэл?)  Hanzi.hush() */
(function () {
  'use strict';
  var NAMES = { mn: 'Ханзи багш', en: 'Teacher Hanzi', ru: 'Учитель Ханзи', ja: 'ハンジ先生' };
  var RM = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  var MOODS = ['hi', 'cheer', 'oops', 'think', 'sleep'];

  /* ── SVG: нэг л зураг, сэтгэл санаа нь data-mood-оор солигдоно ── */
  var BODY =
    '<g class="hz-bob">' +
    '<ellipse class="hz-sh" cx="50" cy="107" rx="27" ry="3.6"/>' +
    '<g class="hz-feet"><ellipse cx="36" cy="102" rx="9" ry="4.4"/><ellipse cx="64" cy="102" rx="9" ry="4.4"/></g>' +
    '<g class="hz-arm hz-al"><path d="M17 72Q8 74 7 80"/><circle cx="7" cy="81" r="6"/></g>' +
    '<g class="hz-arm hz-ar"><path d="M83 72Q92 74 93 80"/><circle cx="93" cy="81" r="6"/></g>' +
    '<g class="hz-body" transform="rotate(-3 50 66)">' +
    '<rect class="hz-seal" x="14" y="28" width="72" height="72" rx="21"/>' +
    '<text class="hz-glyph" x="50" y="90" text-anchor="middle">字</text>' +
    '<path class="hz-sheen" d="M22 48Q22 35 36 34L54 34Q31 39 27 60Z"/>' +
    '<rect class="hz-rim" x="20" y="34" width="60" height="60" rx="15"/>' +
    '<g class="hz-cheek"><circle cx="26" cy="78" r="4.4"/><circle cx="74" cy="78" r="4.4"/></g>' +
    '<g class="hz-gl"><circle cx="37" cy="62" r="10.5"/><circle cx="63" cy="62" r="10.5"/>' +
    '<path d="M47.5 61.5Q50 59.5 52.5 61.5M26.5 60L21 57.5M73.5 60L79 57.5"/></g>' +
    '<g class="hz-eyes" data-m="hi think oops"><g class="hz-pup"><circle cx="37" cy="63" r="3.8"/><circle cx="63" cy="63" r="3.8"/>' +
    '<circle class="hz-hl" cx="38.4" cy="61.6" r="1.2"/><circle class="hz-hl" cx="64.4" cy="61.6" r="1.2"/></g></g>' +
    '<g class="hz-arc" data-m="cheer"><path d="M31 65Q37 55 43 65M57 65Q63 55 69 65"/></g>' +
    '<g class="hz-arc" data-m="sleep"><path d="M31 62Q37 68 43 62M57 62Q63 68 69 62"/></g>' +
    '<g class="hz-brow" data-m="oops"><path d="M28 47L43 43M72 47L57 43"/></g>' +
    '<g class="hz-brow" data-m="think"><path d="M57 45Q64 40 71 44"/></g>' +
    '<g class="hz-mouth">' +
    '<path class="hz-line" data-m="hi" d="M43 80Q50 87 57 80"/>' +
    '<path class="hz-open" data-m="cheer" d="M41 78Q50 95 59 78Z"/>' +
    '<path class="hz-line" data-m="oops" d="M42 85Q45.5 80 49 84Q52.5 88 56 83"/>' +
    '<path class="hz-line" data-m="think" d="M45 83H55"/>' +
    '<ellipse class="hz-open" data-m="sleep" cx="50" cy="83" rx="3" ry="3.4"/></g>' +
    '<g class="hz-cap"><path class="hz-cap2" d="M29 30v7Q50 45 71 37v-7z"/>' +
    '<path class="hz-cap1" d="M50 9L91 23L50 37L9 23Z"/><circle class="hz-gold" cx="50" cy="23" r="2.6"/>' +
    '<g class="hz-tas"><path d="M84 25L86 43"/><circle class="hz-gold" cx="86" cy="46" r="3.2"/></g></g>' +
    '</g>' +
    '<g class="hz-x hz-spk" data-m="cheer"><path d="M10 38l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/><path d="M92 30l1.6 4 4 1.6-4 1.6-1.6 4-1.6-4-4-1.6 4-1.6z"/></g>' +
    '<g class="hz-x hz-q" data-m="think"><text x="84" y="22">?</text></g>' +
    '<g class="hz-x hz-z" data-m="sleep"><text x="80" y="24">z</text><text x="90" y="12">z</text></g>' +
    '<g class="hz-x hz-sw" data-m="oops"><path d="M14 50Q10 56 14 59Q18 56 14 50Z"/></g>' +
    '</g>';

  function norm(m) { return MOODS.indexOf(m) > -1 ? m : 'hi'; }
  function svg(m) {
    return '<svg class="hz" viewBox="0 0 100 112" data-mood="' + norm(m) + '" focusable="false" aria-hidden="true">' + BODY + '</svg>';
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  /* ── мэдэгдлийн эмоцийг үгнээс таах (тодорхой заагаагүй үед) ── */
  function guess(t) {
    t = String(t || '');
    if (/📴/.test(t)) return 'sleep';
    if (/🎉|🔥|✅|🎁|🏆|⭐/.test(t)) return 'cheer';
    if (/алдаа|чадсангүй|буруу|боломжгүй|error|fail|invalid|ошибк|エラー/i.test(t)) return 'oops';
    return 'hi';
  }

  /* ── сахиусыг ямар ч элемент дотор байрлуулах / сэтгэл санааг нь солих ── */
  function mount(el, m) { if (!el) return null; el.innerHTML = svg(m); return el.firstChild; }
  function mood(el, m, hop) {
    var s = el && el.querySelector && el.querySelector('svg.hz');
    if (!s) s = mount(el, m);
    s.setAttribute('data-mood', norm(m));
    if (hop && !RM) { s.classList.remove('go'); void s.getBoundingClientRect(); s.classList.add('go'); }
    return s;
  }

  /* ── мэдэгдлийн бөмбөлөг ── */
  var box, av, avSvg, nameEl, txt, sr, hideT, typeT, ready = false;
  function lang() { var l = (document.documentElement.lang || 'mn').slice(0, 2); return NAMES[l] ? l : 'mn'; }
  function ensure() {
    if (ready) return true;
    box = document.getElementById('toast');
    if (!box) return false;
    box.innerHTML = '<div class="hzav"></div><div class="hzbub"><b class="hzname"></b><span class="hzt" aria-hidden="true"></span><span class="hzsr"></span></div>';
    av = box.querySelector('.hzav'); nameEl = box.querySelector('.hzname'); txt = box.querySelector('.hzt'); sr = box.querySelector('.hzsr');
    avSvg = mount(av, 'hi');
    box.addEventListener('click', hush);
    ready = true;
    return true;
  }
  function hush() {
    clearTimeout(hideT); clearInterval(typeT);
    if (box) { box.classList.remove('on'); if (avSvg) avSvg.classList.remove('talk'); }
  }
  function typeIn(text) {
    clearInterval(typeT);
    var cs = Array.from(text);
    if (RM || cs.length > 150) { txt.textContent = text; avSvg.classList.remove('talk'); return; }
    var i = 0, step = Math.max(1, Math.ceil(cs.length / 34));
    avSvg.classList.add('talk');
    function paint() {
      txt.textContent = '';
      txt.appendChild(document.createTextNode(cs.slice(0, i).join('')));
      var g = document.createElement('span'); g.className = 'hzg'; g.textContent = cs.slice(i).join(''); txt.appendChild(g);
    }
    paint();
    typeT = setInterval(function () {
      i += step; paint();
      if (i >= cs.length) { clearInterval(typeT); avSvg.classList.remove('talk'); }
    }, 24);
  }
  function say(text, m) {
    text = String(text == null ? '' : text);
    if (!text || !ensure()) return;
    m = norm(m || guess(text));
    clearTimeout(hideT);
    nameEl.textContent = NAMES[lang()];
    box.setAttribute('data-mood', m);
    sr.textContent = '';
    setTimeout(function () { sr.textContent = text; }, 30);       /* дэлгэц уншигч дахин уншина */
    box.classList.remove('on'); void box.offsetWidth; box.classList.add('on');
    mood(av, m, true);
    avSvg = av.querySelector('svg.hz');
    typeIn(text);
    var len = Array.from(text).length;
    hideT = setTimeout(hush, Math.min(9000, 2600 + len * 55 + (m === 'oops' ? 900 : 0)));
  }

  window.Hanzi = { say: say, hush: hush, mount: mount, mood: mood, svg: svg, guess: guess, esc: esc };
})();
