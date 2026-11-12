#!/usr/bin/env python3
"""Шалгалтын reel (9:16 mp4): хятад үг + 3 хариулт + 5 секундын тоолуур + зөв хариулт.
Аль хэдийн заасан (make_reel-ээр гарсан) үгсээс давтлага болгон асууна.
Хэрэглээ: python3 Reel/make_quiz.py [--silent] [--min-gap МИНУТ] [--word 爱]"""
import argparse, datetime, json, math, os, random, re, subprocess, sys, tempfile, time, wave
from PIL import Image
import make_reel as M
from make_reel import W, H, cfont, font, bg, center, wrap, say, join, probe, silence, SITE, ZH_VOICE, MN_VOICE, MN_RATE

OUT = M.OUT
STATE = os.path.join(OUT, 'quiz-state.json')
LET = ['A', 'B', 'C']
COLS = ['#f472b6', '#38bdf8', '#facc15']

def short(mn):
    t = re.split(r'[;,]', mn)[0]
    t = re.sub(r'\s*\(.*?\)', '', t).strip() or mn
    return t[:38]

def build(words, num_learned, idx, forced=None):
    seq = M.ordered(words)
    if forced:
        hit = [x for x in seq if x[1][0] == forced]
        if not hit: sys.exit('Үг олдсонгүй: ' + forced)
        lv, w = hit[0]
    else:
        lv, w = seq[idx % max(1, min(num_learned, len(seq)))] if num_learned else seq[idx % len(seq)]
    rng = random.Random(idx * 7919 + 13)
    pool = [x[1] for x in seq if x[0] == lv and x[1][0] != w[0] and short(x[1][2]) != short(w[2])]
    if len(pool) < 2: pool = [x[1] for x in seq if x[1][0] != w[0] and short(x[1][2]) != short(w[2])]
    seen, wrong = {short(w[2])}, []
    rng.shuffle(pool)
    for p in pool:
        if short(p[2]) not in seen: seen.add(short(p[2])); wrong.append(p)
        if len(wrong) == 2: break
    opts = [w] + wrong; rng.shuffle(opts)
    return lv, w, opts, opts.index(w)

def frame(path, lv, w, opts, correct, state, count=None):
    """state: 'q' (асуулт) | 'a' (хариулт)"""
    im, d = bg()
    center(d, 'ШАЛГАЛТ', 100, cfont(56), '#93c5fd')
    f = cfont(46); t = f'HSK {lv}'; tw = d.textlength(t, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 34, 185, (W + tw) / 2 + 34, 255], 35, fill='#facc15'); d.text(((W - tw) / 2, 192), t, font=f, fill='#1e293b')
    hf = font(230 if len(w[0]) <= 2 else 170 if len(w[0]) <= 4 else 120)
    center(d, w[0], 330, hf, 'white')
    if state == 'a': center(d, w[1], 640, cfont(66), '#fde68a')   # пиньин зөвхөн хариулт үед гарна
    center(d, 'Утга нь юу вэ?', 760, cfont(58), '#bfdbfe')
    y = 880
    for i, o in enumerate(opts):
        ok = (i == correct); show_ok = state == 'a' and ok; dim = state == 'a' and not ok
        fill = '#16a34a' if show_ok else ('#1e3a8a' if dim else 'white')
        d.rounded_rectangle([70, y, W - 70, y + 190], 44, fill=fill, outline=('#bbf7d0' if show_ok else COLS[i]), width=10)
        d.ellipse([105, y + 45, 205, y + 145], fill=COLS[i] if not dim else '#475569')
        lf = cfont(66); lw = d.textlength(LET[i], font=lf); d.text((155 - lw / 2, y + 52), LET[i], font=lf, fill='#0f172a')
        fm = cfont(50); lines = wrap(d, short(o[2]), fm, W - 400)[:2]
        ty = y + 95 - len(lines) * 32
        for l in lines: d.text((240, ty), l, font=fm, fill='white' if (show_ok or dim) else '#0f172a'); ty += 64
        y += 220
    if state == 'q' and count is not None:
        cx, cy, r = W // 2, 1640, 90
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill='#facc15')
        cf = cfont(110); cw = d.textlength(str(count), font=cf); d.text((cx - cw / 2, cy - 68), str(count), font=cf, fill='#1e293b')
    elif state == 'q':
        center(d, 'Сонсоод хариулаарай', 1610, cfont(54), '#facc15')
    else:
        center(d, f'Зөв хариулт: {LET[correct]}', 1590, cfont(70), '#4ade80')
    center(d, SITE, 1775, cfont(42), '#facc15')
    im.save(path)

def cta(path):
    im, d = bg()
    center(d, 'Зөв хариулсан бол', 600, cfont(64), '#bfdbfe')
    center(d, 'комментд бич!', 700, cfont(64), '#bfdbfe')
    center(d, 'A  /  B  /  C', 880, cfont(120), '#facc15')
    center(d, 'Өдөр бүр шинэ шалгалт', 1150, cfont(56), 'white')
    center(d, 'Дагаад, хятад хэл сур', 1240, cfont(56), 'white')
    center(d, SITE, 1775, cfont(42), '#facc15'); im.save(path)

def tick(path, n):
    """n секунд: секунд бүрийн эхэнд богино «тик»."""
    sr = 24000
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        for s in range(n):
            buf = bytearray()
            for i in range(sr):
                v = int(9000 * math.sin(2 * math.pi * 1000 * i / sr) * (1 - i / 2400)) if i < 2400 else 0
                buf += int(v).to_bytes(2, 'little', signed=True)
            w.writeframes(bytes(buf))

def segment(tmp, name, imgs, wav):
    """imgs: секунд тутамд нэг зураг. Видео = хамгийн багадаа аудиотой тэнцүү."""
    dur = probe(wav); fd = os.path.join(tmp, name); os.makedirs(fd)
    for i, im in enumerate(imgs): os.replace(im, os.path.join(fd, f'f{i:03d}.png'))
    mp4 = os.path.join(tmp, name + '.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '1', '-i', os.path.join(fd, 'f%03d.png'), '-i', wav, '-r', '30', '-t', f'{dur:.2f}',
                    '-vf', 'tpad=stop_mode=clone:stop_duration=3', '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-ar', '44100', mp4], check=True)
    return mp4

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--silent', action='store_true'); ap.add_argument('--min-gap', type=int, default=0); ap.add_argument('--word')
    a = ap.parse_args(); M.start_watchdog()
    try: st = json.load(open(STATE))
    except Exception: st = {}
    if a.min_gap and time.time() - st.get('last', 0) < a.min_gap * 60:
        print('Алгасав'); go = os.environ.get('GITHUB_OUTPUT')
        if go: open(go, 'a').write('skipped=true\n')
        return
    try: learned = json.load(open(os.path.join(OUT, 'state.json'))).get('next', 0)
    except Exception: learned = 0
    words, _ = M.load(); idx = st.get('next', 0)
    lv, w, opts, ci = build(words, learned, idx, a.word)
    print('Шалгалт:', w[0], w[1], short(w[2]), '→', LET[ci], '(HSK', lv, ')')
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        P = lambda n: os.path.join(tmp, n)
        z1 = say(w[0], ZH_VOICE, '-15%', tmp, 1, a.silent)
        z2 = say(w[0], ZH_VOICE, '+0%', tmp, 2, a.silent)
        ans = say(f'Зөв хариулт, {LET[ci]}. {short(w[2])}.', MN_VOICE, MN_RATE, tmp, 3, a.silent)
        if M.TTS_FAIL and not a.silent: sys.exit('Дуу үүсгэж чадсангүй: ' + ', '.join(M.TTS_FAIL))
        # 1) асуулт: үгийг уншина
        aq = P('aq.wav'); gap = P('g.wav'); silence(gap, 0.6); join([z1, gap, z2], 0, aq)
        nq = int(probe(aq)) + 1; imgs = []
        for i in range(nq): frame(P(f'q{i}.png'), lv, w, opts, ci, 'q'); imgs.append(P(f'q{i}.png'))
        segs = [segment(tmp, 'q', imgs, aq)]
        # 2) тоолуур 5..1
        at = P('at.wav'); tick(at, 5); imgs = []
        for i, c in enumerate([5, 4, 3, 2, 1]): frame(P(f'c{i}.png'), lv, w, opts, ci, 'q', c); imgs.append(P(f'c{i}.png'))
        segs.append(segment(tmp, 'c', imgs, at))
        # 3) хариулт
        aa = P('aa.wav'); silence(gap, 0.4); join([ans, gap, z2], 0, aa); na = int(probe(aa)) + 1; imgs = []
        for i in range(na): frame(P(f'a{i}.png'), lv, w, opts, ci, 'a'); imgs.append(P(f'a{i}.png'))
        segs.append(segment(tmp, 'a', imgs, aa))
        # 4) CTA
        cta(P('cta.png')); ac = P('ac.wav'); silence(ac, 3); segs.append(segment(tmp, 'cta', [P('cta.png')], ac))
        lst = P('l.txt'); open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
        tag = f'{idx + 1:04d}'; out = os.path.join(OUT, f'quiz-{tag}.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'copy', '-af', M.LOUDNORM,
                        '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-movflags', '+faststart', out], check=True)
    opts_txt = '\n'.join(f'{LET[i]}) {short(o[2])}' for i, o in enumerate(opts))
    cap = (f'🧠 Энэ үгийн утга юу вэ? Хариулаад комментд бич!\n\n📌 {w[0]}\n\n{opts_txt}\n\n'
           f'✅ Зөв хариулт: {LET[ci]}) {short(w[2])}  [{w[1]}]\n🎓 HSK {lv}\n\n💾 Хадгалаад давтаарай ❤️ Найздаа илгээгээрэй\n'
           f'👉 Үнэгүй сурах сайт: {SITE}\n\n{M.TAGS[0]} #HSK{lv} #шалгалт #quiz ' + ' '.join(M.TAGS[1:]))
    open(out[:-4] + '.txt', 'w', encoding='utf8').write(cap)
    if not a.silent and not a.word:
        json.dump({'next': idx + 1, 'last': int(time.time())}, open(STATE, 'w'))
    print('Бэлэн:', out, round(probe(out), 1), 'сек')

if __name__ == '__main__': main()
