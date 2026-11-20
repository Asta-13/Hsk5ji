#!/usr/bin/env python3
"""«5 шинэ үг» reel (9:16 mp4): энгийн (нэг үсэгт) үгсийг 5-аар нэг видеонд цуглуулна.
Жишээ өгүүлбэргүй — зөвхөн хятад үсэг + пиньинь + монгол орчуулга; үг бүрийг удаан, хэвийн хоёр удаа уншина.
Хэрэгтэй (олон үсэгт) үгс тусдаа `make_reel.py`-ээр жишээ өгүүлбэртэй гарна. Хуваалтыг `series.py` тодорхойлно.
Хэрэглээ: python3 Reel/make_words5.py [--silent] [--min-gap МИНУТ] [--level N]"""
import argparse, os, re, subprocess, sys, tempfile
import make_reel as M
import series as SR
from make_reel import W, H, PAD, FOOT_Y, cfont, font, bg, center, say, join, probe, silence, header, footer, SITE, ZH_VOICE, MN_VOICE, MN_RATE

OUT = M.OUT
ROW_TOP, ROW_H = 470, 176
COL = '#a78bfa'


def short(mn, n=34):
    t = re.split(r'[;,]', mn)[0]
    t = re.sub(r'\s*\(.*?\)', '', t).strip() or mn
    return t[:n]


def trunc(d, text, f, maxw):
    while len(text) > 3 and d.textlength(text, font=f) > maxw: text = text[:-2].rstrip() + '…'
    return text


def panel(path, lv, ws, upto, cur):
    """ws: [(хятад, пиньинь, монгол)]; upto: хэдэн мөр харагдах; cur: яг одоо дуугарч буй мөр (-1 = аль нь ч биш)"""
    im, d = bg(); header(d, lv, 'Өнөөдрийн шинэ үгс')
    for i, (han, py, mn) in enumerate(ws):
        if i >= upto: break
        on = i == cur; top = ROW_TOP + i * ROW_H
        d.rounded_rectangle([PAD - 30, top, W - PAD + 30, top + ROW_H - 18], 40, fill='white' if on else '#1e3a8a', outline=COL, width=8 if on else 4)
        hs = 104 if len(han) == 1 else 76 if len(han) == 2 else 54
        hw = d.textlength(han, font=font(hs)); d.text((PAD + 90 - hw / 2, top + (ROW_H - 18 - hs * 1.2) / 2), han, font=font(hs), fill='#0f172a' if on else 'white')
        x = PAD + 230; maxw = W - PAD + 10 - x
        pf = M.fit(d, py, cfont, 62, maxw, 38)
        d.text((x, top + 14), py, font=pf, fill='#2563eb' if on else '#fde68a')
        mf = cfont(38); d.text((x, top + 96), trunc(d, short(mn), mf, maxw), font=mf, fill='#475569' if on else '#bae6fd')
    footer(d); im.save(path)


def hook(path, lv, ws):
    im, d = bg(); header(d, lv, '')
    center(d, 'Өнөөдрийн', 440, cfont(96), 'white'); center(d, '5 шинэ үг', 560, cfont(104), '#fde68a')
    f = font(120 if all(len(w[0]) == 1 for w in ws) else 84); gap = 34
    ww = [d.textlength(w[0], font=f) for w in ws]; x = (W - sum(ww) - gap * (len(ws) - 1)) / 2
    for (han, _, _), w in zip(ws, ww): d.text((x, 780), han, font=f, fill='#fde68a'); x += w + gap
    center(d, 'Чи хэдийг нь мэднэ?', 1040, cfont(60), '#bfdbfe'); footer(d); im.save(path)


def cta(path, lv):
    im, d = bg(); header(d, lv, 'Өнөөдрийн шинэ үгс')
    for i, l in enumerate(['Хэдийг нь мэдэж байсан бэ?', 'Комментдоо тоогоо бичээрэй']): center(d, l, 640 + i * 100, cfont(60), '#bfdbfe')
    center(d, 'Хадгалаад дараа дахин үзээрэй', 960, cfont(56), '#facc15')
    center(d, 'Өдөр бүр шинэ үгс', 1130, cfont(54), 'white'); footer(d); im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--silent', action='store_true'); ap.add_argument('--min-gap', type=int, default=0); ap.add_argument('--level', type=int)
    a = ap.parse_args(); M.start_watchdog()
    st = SR.load()
    if SR.too_soon(st, 'group', a.min_gap):
        print('Алгасав'); SR.skip_out(); return
    words, _ = M.load(); seq = M.ordered(words)
    SR.init(st, seq)
    _, simple = SR.split_words(seq, st)
    g = SR.next_group(simple, a.level or st['level'])
    if not g:
        print('Энгийн үг дууссан'); SR.skip_out(); return
    lv, ws = g; num = SR.num(st, 'group'); M.BADGE = ('group', num)
    print('Энгийн үгс:', [w[0] for w in ws], '(HSK', lv, ')', '#' + str(num))
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        P = lambda n: os.path.join(tmp, n)
        c = lambda t, v, r, i: say(t, v, r, tmp, i, a.silent)
        intro = c('Сайн уу, би Ханзи багш. Өнөөдөр таван шинэ үг хамт сурцгаая.', MN_VOICE, MN_RATE, 1)
        zs = [c(w[0], ZH_VOICE, '-30%', 10 + i) for i, w in enumerate(ws)]
        zn = [c(w[0], ZH_VOICE, '+0%', 20 + i) for i, w in enumerate(ws)]
        ms = [c(short(w[2], 40), MN_VOICE, MN_RATE, 30 + i) for i, w in enumerate(ws)]
        if M.TTS_FAIL and not a.silent: sys.exit('Дуу үүсгэж чадсангүй: ' + ', '.join(M.TTS_FAIL))
        gap = P('g.wav'); silence(gap, 0.45); segs = []
        M.TEACHER_MOOD = 'hi'; hook(P('h0.png'), lv, ws); ai = P('ai.wav'); join([intro], 0, ai)
        segs.append(M.segment(tmp, 'hook', [P('h0.png')], ai))
        for i in range(len(ws)):
            aud = P(f'a{i}.wav'); join([zs[i], gap, zn[i], gap, ms[i]], 0, aud)
            M.TEACHER_MOOD = 'think'; panel(P(f'p{i}.png'), lv, ws, i + 1, i)               # нэг зураг, аудио дуустал барина (давхар зурахгүй)
            segs.append(M.segment(tmp, f's{i}', [P(f'p{i}.png')], aud))
        # давталт: 5-ыг хурдан дараалан (хариуг мэдэх)
        g2 = P('g2.wav'); silence(g2, 0.4); parts = []
        for i, z in enumerate(zn): parts += [z] + ([g2] if i < len(zn) - 1 else [])
        rep = P('rep.wav'); join(parts, 0, rep)
        M.TEACHER_MOOD = 'cheer'; panel(P('r.png'), lv, ws, len(ws), -1)
        segs.append(M.segment(tmp, 'rep', [P('r.png')], rep))
        M.TEACHER_MOOD = 'cheer'; cta(P('cta.png'), lv); ac = P('ac.wav'); silence(ac, 3); segs.append(M.segment(tmp, 'cta', [P('cta.png')], ac))
        lst = P('l.txt'); open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
        out = os.path.join(OUT, SR.file_name('group', num))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'copy', '-af', M.LOUDNORM,
                        '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-movflags', '+faststart', out], check=True)
    lines = '\n'.join(f'{i + 1}) {h}  [{p}]  —  {short(m, 60)}' for i, (h, p, m) in enumerate(ws))
    cap = (f'📚 Өнөөдрийн 5 шинэ үг — HSK {lv} · №{num}\n\n{lines}\n\n🎯 Хэдийг нь мэдэж байсан бэ? Комментд тоогоо бичээрэй!\n'
           f'💾 Хадгалаад дараа давтаарай\n📩 Хятад хэл сурч буй найздаа илгээгээрэй\n\n{SR.series_line({**st, "level": lv}, "group", num)}\n\n'
           f'🔗 Үнэгүй сурах сайт — профайлын линкээс (bio)\n\n{M.TAGS[0]} #HSK{lv} #хятадүг ' + ' '.join(M.TAGS[2:]))
    open(out[:-4] + '.txt', 'w', encoding='utf8').write(cap)
    if not a.silent or os.environ.get('REEL_TEST_STATE') == '1':
        for h, _, _ in ws: SR.mark(st, 'word', h)           # эдгээр үг заагдсан → шалгалтад орно, дахин гарахгүй
        SR.finish(st, 'group'); SR.save(st)
    print('Бэлэн:', out, round(probe(out), 1), 'сек')


if __name__ == '__main__': main()
