// Өдрийн сануулга илгээгч (GitHub Action цаг тутамд ажиллуулна).
// Хэрэглэгчийн сонгосон орон нутгийн цагт, тэр өдөр сураагүй бол л мэдэгдэл явуулна.
import webpush from 'web-push';

const { SUPABASE_URL, SUPABASE_SERVICE_KEY, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT, SITE_URL } = process.env;
if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY || !VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) {
  console.log('Secrets тохируулаагүй тул алгаслаа.');
  process.exit(0);
}
webpush.setVapidDetails(VAPID_SUBJECT || 'mailto:admin@example.com', VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

const H = { apikey: SUPABASE_SERVICE_KEY, Authorization: `Bearer ${SUPABASE_SERVICE_KEY}`, 'Content-Type': 'application/json' };
const rest = (path, init = {}) => fetch(`${SUPABASE_URL}/rest/v1/${path}`, { ...init, headers: { ...H, ...(init.headers || {}) } });

const MSG = {
  mn: { title: '汉字 HSK', one: 'Өнөөдөр 5 минут: шинэ үгээ сурах цаг боллоо.', streak: (n) => `🔥 ${n} өдрийн цуврал! Өнөөдөр 5 минут сураад үргэлжлүүл.` },
  en: { title: '汉字 HSK', one: 'Time for your 5 minutes of Chinese today.', streak: (n) => `🔥 ${n}-day streak! Study 5 minutes to keep it going.` },
  ru: { title: '汉字 HSK', one: 'Время для 5 минут китайского сегодня.', streak: (n) => `🔥 Серия ${n} дн.! Позанимайтесь 5 минут, чтобы продолжить.` },
  ja: { title: '汉字 HSK', one: '今日の5分、中国語を学びましょう。', streak: (n) => `🔥 ${n}日連続！今日も5分で続けましょう。` },
};

const iso = (d) => d.toISOString().slice(0, 10);
const on = (act, d) => { const a = act && act[iso(d)]; return !!(a && (a.w > 0 || a.m > 0)); };
function streakBefore(act, localDay) { // өнөөдрөөс өмнөх тасралтгүй өдрүүд
  let n = 0, d = new Date(localDay.getTime() - 864e5);
  while (on(act, d)) { n++; d = new Date(d.getTime() - 864e5); }
  return n;
}

const subs = await (await rest('push_subs?select=*')).json();
if (!Array.isArray(subs)) { console.error('subs уншиж чадсангүй', subs); process.exit(1); }
console.log(`${subs.length} бүртгэл`);
if (!subs.length) process.exit(0);

const uids = [...new Set(subs.map((s) => s.uid))];
const profs = await (await rest(`profiles?select=id,data&id=in.(${uids.join(',')})`)).json();
const act = Object.fromEntries((Array.isArray(profs) ? profs : []).map((p) => [p.id, (p.data && p.data.act) || {}]));

let sent = 0, gone = 0;
for (const s of subs) {
  const local = new Date(Date.now() + s.tzo * 60000);
  const day = iso(local);
  if (local.getUTCHours() !== s.hour || s.last_sent === day) continue;
  const a = act[s.uid] || {};
  if (on(a, local)) continue; // өнөөдөр аль хэдийн сурсан
  const n = streakBefore(a, local), m = MSG[s.lang] || MSG.mn;
  try {
    await webpush.sendNotification(
      { endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } },
      JSON.stringify({ title: m.title, body: n >= 2 ? m.streak(n) : m.one, url: SITE_URL || './' }),
      { TTL: 6 * 3600 }
    );
    await rest(`push_subs?endpoint=eq.${encodeURIComponent(s.endpoint)}`, { method: 'PATCH', body: JSON.stringify({ last_sent: day }) });
    sent++;
  } catch (e) {
    if (e.statusCode === 404 || e.statusCode === 410) {
      await rest(`push_subs?endpoint=eq.${encodeURIComponent(s.endpoint)}`, { method: 'DELETE' });
      gone++;
    } else console.error('илгээж чадсангүй', e.statusCode || e.message);
  }
}
console.log(`илгээсэн ${sent}, хүчингүй болсон ${gone}`);
