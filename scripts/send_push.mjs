// Өдрийн сануулга илгээгч (GitHub Action цаг тутамд ажиллуулна).
// Хэрэглэгчийн сонгосон орон нутгийн цагт, тэр өдөр сураагүй бол л мэдэгдэл явуулна.
import webpush from 'web-push';

// Secret буулгахад тааралдсан зай/мөр шилжилтийг цэвэрлэнэ
const E = Object.fromEntries(Object.entries(process.env).map(([k, v]) => [k, (v || '').trim()]));
const SUPABASE_URL = (E.SUPABASE_URL || '').replace(/\/+$/, '');
const { SUPABASE_SERVICE_KEY, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT, SITE_URL } = E;
if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY || !VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) {
  console.log('Secrets тохируулаагүй тул алгаслаа.');
  process.exit(0);
}
webpush.setVapidDetails(VAPID_SUBJECT || 'mailto:admin@example.com', VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

// Шинэ `sb_secret_...` түлхүүр JWT биш тул зөвхөн apikey толгойгоор; хуучин service_role (JWT) бол Authorization-тай нь.
const H = { apikey: SUPABASE_SERVICE_KEY, 'Content-Type': 'application/json' };
if (!SUPABASE_SERVICE_KEY.startsWith('sb_')) H.Authorization = `Bearer ${SUPABASE_SERVICE_KEY}`;
const rest = (path, init = {}) => fetch(`${SUPABASE_URL}/rest/v1/${path}`, { ...init, headers: { ...H, ...(init.headers || {}) } });

const NAME = { mn: 'Ханзи багш 汉字', en: 'Teacher Hanzi 汉字', ru: 'Учитель Ханзи 汉字', ja: 'ハンジ先生 汉字' };
const MSG = {
  mn: {
    one: ['你好！Өнөөдөр 5 минут л хэрэгтэй. Би хүлээж байна 👀', 'Үгнүүд чамайг санаад байна 🥺 5 минут өгөөч!', 'Ханзи шинэ үг бэлдчихсэн. Чи яасан бэ? 😏', 'Утсаа нээсэн бол хятад хэл рүү нэг орчих. Би шалгана! 📝', '5 минут = 5 үг. Ийм хямд наймаа хаана байх вэ? 😄'],
    streak: (n) => [`🔥 ${n} өдөр дараалсан! Одоо тасалбал би уйлна 😭 5 минут л болно.`, `🔥 ${n} өдрийн цуврал аюулд байна! Аваръя, 5 минут!`, `${n} өдөр шүү дээ! Хамт үргэлжлүүлье 💪 汉字`],
    due: (d) => `${d} үг давтлага хүлээж байна. Мартахаас өмнө ирээрэй! 🧠`,
  },
  en: {
    one: ['你好! Just 5 minutes today. I\'m waiting 👀', 'Your words miss you 🥺 Give them 5 minutes!', 'I prepared new words. Where are you? 😏', 'Phone already in hand? Open Chinese for a sec. I\'ll quiz you! 📝', '5 minutes = 5 words. Best deal ever 😄'],
    streak: (n) => [`🔥 ${n} days in a row! Break it and I cry 😭 Just 5 minutes.`, `🔥 Your ${n}-day streak is in danger! Save it!`, `${n} days! Let\'s keep going 💪 汉字`],
    due: (d) => `${d} words are due for review. Come before you forget! 🧠`,
  },
  ru: {
    one: ['你好! Сегодня нужно всего 5 минут. Я жду 👀', 'Слова по тебе скучают 🥺 Дай им 5 минут!', 'Я приготовил новые слова. Ты где? 😏', 'Телефон в руках? Загляни в китайский на минутку. Проверю! 📝', '5 минут = 5 слов. Выгоднее не бывает 😄'],
    streak: (n) => [`🔥 ${n} дн. подряд! Прервёшь — я заплачу 😭 Всего 5 минут.`, `🔥 Серия ${n} дн. в опасности! Спаси её!`, `${n} дн.! Продолжаем 💪 汉字`],
    due: (d) => `Слов на повторение: ${d}. Приходи, пока не забыл! 🧠`,
  },
  ja: {
    one: ['你好！今日は5分だけ。待ってるよ 👀', '単語がさみしがってるよ 🥺 5分ください！', '新しい単語を用意したよ。どこ？ 😏', 'スマホを持ってるなら中国語をちょっと開いて！テストするよ 📝', '5分＝5単語。お得でしょ 😄'],
    streak: (n) => [`🔥 ${n}日連続！途切れたら泣いちゃう 😭 5分だけ。`, `🔥 ${n}日の連続記録がピンチ！守って！`, `${n}日も！一緒に続けよう 💪 汉字`],
    due: (d) => `復習が${d}語たまってるよ。忘れる前においで！🧠`,
  },
};
const DONE = {
  mn: ['Өнөөдрийн даалгавраа хийчихсэн байна, гоё! 👏 Бас 1 удаа давтах уу?', 'Чи өнөөдөр сайн ажиллалаа 💪 Мартахаас өмнө хурдан давтчихъя!', '汉字 багш бахархаж байна 🥹 Нэг л карт нэм!'],
  en: ['Today\'s goal done, nice! 👏 One more round?', 'Great work today 💪 A quick review before you forget!', 'Teacher Hanzi is proud 🥹 Just one more card!'],
  ru: ['Цель на сегодня выполнена! 👏 Ещё один круг?', 'Отлично поработал 💪 Быстрое повторение, пока не забыл!', 'Учитель Ханзи гордится 🥹 Ещё одну карточку!'],
  ja: ['今日の目標達成！👏 もう1回やる？', '今日もえらい 💪 忘れる前にサクッと復習！', 'ハンジ先生は誇らしいよ 🥹 あと1枚だけ！'],
};
const hash = (str) => { let h = 2166136261; for (const c of str) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };
// freq>1: 1-р нь сонгосон цагт, үлдсэн нь сонгосон цагаас 22:00 хүртэл санамсаргүй (өдөр бүр өөр) цагт
function slotsOf(s, day) {
  const start = s.hour * 60 + (s.minute || 0), f = Math.max(1, s.freq || 1), end = Math.max(start + 60 * f, 22 * 60);
  const seg = Math.floor((Math.min(end, 23 * 60 + 30) - start) / f), out = [start];
  for (let i = 1; i < f; i++) out.push(start + i * seg + (hash(`${s.endpoint}${day}${i}`) % Math.max(1, seg - 20)));
  return out;
}
const pick = (a) => a[Math.floor(Math.random() * a.length)];

const iso = (d) => d.toISOString().slice(0, 10);
const on = (act, d) => { const a = act && act[iso(d)]; return !!(a && (a.w > 0 || a.m > 0)); };
function streakBefore(act, localDay) { // өнөөдрөөс өмнөх тасралтгүй өдрүүд
  let n = 0, d = new Date(localDay.getTime() - 864e5);
  while (on(act, d)) { n++; d = new Date(d.getTime() - 864e5); }
  return n;
}

if (!E.TEST_ALLOW_ANY_URL && !/^https:\/\/[a-z0-9]+\.supabase\.co$/.test(SUPABASE_URL)) {
  console.error('SUPABASE_URL буруу хэлбэртэй. Жишээ: https://xxxx.supabase.co (зөвхөн хаяг, /rest/v1 нэмэхгүй)');
  process.exit(1);
}
let res;
try { res = await rest('push_subs?select=*'); } catch (e) { console.error('Supabase руу холбогдож чадсангүй:', e.message); process.exit(1); }
const subs = await res.json().catch(() => null);
if (!res.ok || !Array.isArray(subs)) {
  console.error(`push_subs уншиж чадсангүй: HTTP ${res.status}`, JSON.stringify(subs).slice(0, 300));
  console.error(res.status === 401 || res.status === 403 ? 'SUPABASE_SERVICE_KEY буруу эсвэл secret түлхүүр биш байна.' : 'SUPABASE_URL болон хүснэгтийг шалгана уу.');
  process.exit(1);
}
console.log(`${subs.length} бүртгэл`);
if (!subs.length) process.exit(0);

const uids = [...new Set(subs.map((s) => s.uid))];
const profs = await (await rest(`profiles?select=id,data&id=in.(${uids.join(',')})`)).json();
const act = Object.fromEntries((Array.isArray(profs) ? profs : []).map((p) => [p.id, (p.data && p.data.act) || {}]));

const base = (SITE_URL || '').replace(/\/?$/, '/');
let sent = 0, gone = 0;
for (const s of subs) {
  const local = new Date(Date.now() + s.tzo * 60000);
  const day = iso(local);
  const nowM = local.getUTCHours() * 60 + local.getUTCMinutes();
  const slots = slotsOf(s, day), n0 = s.last_sent === day ? (s.sent_n || 0) : 0;
  if (n0 >= slots.length || nowM < slots[n0]) continue;
  const nextN = n0 + 1;
  if (nowM >= slots[n0] + 150) { // хоцорсон цонх: алгасаад дараагийнхыг хүлээнэ
    await rest(`push_subs?endpoint=eq.${encodeURIComponent(s.endpoint)}`, { method: 'PATCH', body: JSON.stringify({ last_sent: day, sent_n: nextN }) });
    continue;
  }
  const a = act[s.uid] || {};
  const done = on(a, local);
  const n = streakBefore(a, local), m = MSG[s.lang] || MSG.mn;
  try {
    await webpush.sendNotification(
      { endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } },
      JSON.stringify({ title: NAME[s.lang] || NAME.mn, body: done ? pick(DONE[s.lang] || DONE.mn) : pick(n >= 2 ? m.streak(n) : m.one), icon: `${base}icons/hz-${done || n >= 2 ? 'cheer' : 'think'}.png`, url: SITE_URL || './' }),
      { TTL: 6 * 3600 }
    );
    await rest(`push_subs?endpoint=eq.${encodeURIComponent(s.endpoint)}`, { method: 'PATCH', body: JSON.stringify({ last_sent: day, sent_n: nextN }) });
    sent++;
  } catch (e) {
    if (e.statusCode === 404 || e.statusCode === 410) {
      await rest(`push_subs?endpoint=eq.${encodeURIComponent(s.endpoint)}`, { method: 'DELETE' });
      gone++;
    } else console.error('илгээж чадсангүй', e.statusCode || e.message);
  }
}
console.log(`илгээсэн ${sent}, хүчингүй болсон ${gone}`);
