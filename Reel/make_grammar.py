#!/usr/bin/env python3
"""Дүрмийн reel (9:16 mp4): 1 дүрэм = 1 видео. HSK 1 → 6 дарааллаар.
Загвар → монгол утга → жишээ өгүүлбэр (удаан, хэвийн, орчуулга) → давталт.
Хэрэглээ: python3 Reel/make_grammar.py [--silent] [--min-gap МИНУТ] [--index N]"""
import argparse, json, os, re, subprocess, sys, tempfile, time
import make_reel as M
import make_quiz as Q
from make_reel import W, H, cfont, font, bg, center, wrap, say, join, probe, silence, SITE, ZH_VOICE, MN_VOICE, MN_RATE

OUT = M.OUT
STATE = os.path.join(OUT, 'grammar-state.json')

def spoken(t):
    t = t.replace('……', '，').replace('...', '，').replace('…', '，')
    for k, v in (('V', '动词'), ('N', '名词'), ('A', '形容词')):
        t = re.sub(r'(?<![A-Za-z])' + k + r'(?![A-Za-z])', v, t)
    return t

def items():
    rows = []
    for ln in json.load(open(os.path.join(M.ROOT, 'data', 'grammar.json'), encoding='utf8')).split('\n'):
        a = ln.split('|')
        if len(a) >= 5 and a[0].isdigit(): rows.append((int(a[0]), a[1], a[2], a[3], a[4]))
    rows.sort(key=lambda r: r[0])           # түвшнээр (дотроо файлын дарааллаар)
    return rows

def panel(path, lv, stage, pat, py, mn, ex=None, ex_py='', ex_mn=''):
    im, d = bg()
    center(d, 'ДҮРМИЙН ХИЧЭЭЛ', 100, cfont(56), '#93c5fd')
    f = cfont(46); t = f'HSK {lv}'; tw = d.textlength(t, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 34, 185, (W + tw) / 2 + 34, 255], 35, fill='#facc15'); d.text(((W - tw) / 2, 192), t, font=f, fill='#1e293b')
    size = 140 if len(pat) <= 5 else 100 if len(pat) <= 9 else 76
    pf = font(size); y = 340
    for l in wrap(d, pat, pf, W - 140)[:3]:
        center(d, l, y, pf, 'white'); y += int(size * 1.25)
    y += 10
    if py:
        for l in wrap(d, py, cfont(46), W - 160)[:2]: center(d, l, y, cfont(46), '#fde68a'); y += 60
    y += 30
    if stage in ('meaning', 'example', 'repeat'):
        d.rounded_rectangle([60, y, W - 60, y + 40 + 66 * min(3, len(wrap(d, mn, cfont(54), W - 220)))], 40, fill='#1e3a8a', outline='#38bdf8', width=8)
        yy = y + 22
        for l in wrap(d, mn, cfont(54), W - 220)[:3]: center(d, l, yy, cfont(54), '#bae6fd'); yy += 66
        y = yy + 50
    if stage in ('example', 'repeat') and ex:
        ef = font(80 if len(ex) <= 10 else 66 if len(ex) <= 16 else 54); lines = wrap(d, ex, ef, W - 220)[:3]; hl = int(ef.size * 1.3)
        pl = wrap(d, ex_py, cfont(44), W - 220)[:3]; ml = wrap(d, ex_mn, cfont(50), W - 220)[:3]
        hh = 50 + len(lines) * hl + len(pl) * 58 + (len(ml) * 68 if stage == 'example' and ex_mn else 0)
        d.rounded_rectangle([50, y, W - 50, y + hh], 44, fill='white', outline='#facc15', width=8)
        yy = y + 28
        for l in lines: d.text((100, yy), l, font=ef, fill='#0f172a'); yy += hl
        for l in pl: d.text((100, yy), l, font=cfont(44), fill='#2563eb'); yy += 58
        if stage == 'example':
            for l in ml: d.text((100, yy), l, font=cfont(50), fill='#475569'); yy += 68
    center(d, 'Өдөр бүр шинэ дүрэм', 1700, cfont(44), '#bfdbfe'); center(d, SITE, 1775, cfont(42), '#facc15')
    im.save(path)

def cta(path):
    im, d = bg()
    for i, l in enumerate(['Өөрөө нэг өгүүлбэр', 'зохиогоод комментд бич!']): center(d, l, 640 + i * 100, cfont(64), '#bfdbfe')
    center(d, 'Хадгалаад давтаарай', 960, cfont(60), '#facc15')
    center(d, 'Өдөр бүр шинэ дүрэм', 1150, cfont(56), 'white'); center(d, SITE, 1775, cfont(42), '#facc15'); im.save(path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--silent', action='store_true'); ap.add_argument('--min-gap', type=int, default=0); ap.add_argument('--index', type=int)
    a = ap.parse_args(); M.start_watchdog()
    try: st = json.load(open(STATE))
    except Exception: st = {}
    if a.min_gap and time.time() - st.get('last', 0) < a.min_gap * 60:
        print('Алгасав'); go = os.environ.get('GITHUB_OUTPUT')
        if go: open(go, 'a').write('skipped=true\n')
        return
    rows = items(); idx = a.index if a.index is not None else st.get('next', 0)
    lv, pat, mn, ex, ex_mn = rows[idx % len(rows)]
    py = M.sent_pinyin(pat); ex_py = M.sent_pinyin(ex)
    print('Дүрэм:', lv, pat, '|', mn)
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        P = lambda n: os.path.join(tmp, n)
        c = lambda t, v, r, i: say(t, v, r, tmp, i, a.silent)
        z_pat = c(spoken(pat), ZH_VOICE, '-15%', 1)
        a_mn = c('Утга нь... ' + mn.replace('...', ',').replace('  ', ' '), MN_VOICE, MN_RATE, 2)
        z_slow, z_norm = c(ex, ZH_VOICE, '-25%', 3), c(ex, ZH_VOICE, '+0%', 4)
        a_tr = c('Орчуулбал... ' + ex_mn, MN_VOICE, MN_RATE, 5)
        if M.TTS_FAIL and not a.silent: sys.exit('Дуу үүсгэж чадсангүй: ' + ', '.join(M.TTS_FAIL))
        gap = P('g.wav'); silence(gap, 0.5)
        stages = [('hook', [z_pat, gap, z_pat]), ('meaning', [a_mn]), ('example', [z_slow, gap, z_norm, gap, a_tr]), ('repeat', [z_norm, gap, z_slow])]
        segs = []
        for n, (stg, ws) in enumerate(stages):
            aud = P(f'a{n}.wav'); join(ws, 0, aud); k = int(probe(aud)) + 1; imgs = []
            for i in range(k): panel(P(f'p{n}_{i}.png'), lv, stg, pat, py, mn, ex, ex_py, ex_mn); imgs.append(P(f'p{n}_{i}.png'))
            segs.append(Q.segment(tmp, f's{n}', imgs, aud))
        cta(P('cta.png')); ac = P('ac.wav'); silence(ac, 3); segs.append(Q.segment(tmp, 'cta', [P('cta.png')], ac))
        lst = P('l.txt'); open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
        out = os.path.join(OUT, f'grammar-{idx % len(rows) + 1:04d}.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'copy', '-af', M.LOUDNORM,
                        '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-movflags', '+faststart', out], check=True)
    cap = (f'📚 Дүрмийн хичээл — HSK {lv}\n\n📌 {pat}\n🇲🇳 {mn}\n\n🗣 Жишээ:\n{ex}\n{ex_py}\n{ex_mn}\n\n'
           f'✍️ Өөрөө нэг өгүүлбэр зохиогоод комментд бичээрэй!\n💾 Хадгалаад давтаарай ❤️ Найздаа илгээгээрэй\n👉 Үнэгүй сурах сайт: {SITE}\n\n'
           f'{M.TAGS[0]} #HSK{lv} #дүрэм #grammar ' + ' '.join(M.TAGS[1:]))
    open(out[:-4] + '.txt', 'w', encoding='utf8').write(cap)
    if not a.silent and a.index is None:
        json.dump({'next': idx + 1, 'last': int(time.time())}, open(STATE, 'w'))
    print('Бэлэн:', out, round(probe(out), 1), 'сек')

if __name__ == '__main__': main()
