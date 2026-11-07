#!/usr/bin/env python3
"""Киноны хэв маягийн богино харилцан яриа (reel, 9:16 mp4). scenes.json доторх 40 өөрийн зохиосон яриаг дарааллаар нь хийнэ.
Хэрэглээ: python3 reel/make_scene.py [--index N] [--silent] [--min-gap МИНУТ]"""
import argparse, json, os, subprocess, sys, tempfile, time
from PIL import Image, ImageDraw
import make_reel as M
from make_reel import W, H, cfont, font, bg, center, wrap, say, join, probe, silence, SITE

OUT = M.OUT
STATE = os.path.join(OUT, 'scene-state.json')
VOICE = {'A': 'zh-CN-XiaoxiaoNeural', 'B': 'zh-CN-YunxiNeural'}
COL = {'A': '#f472b6', 'B': '#38bdf8'}

def frame(sc, upto, path):
    im, d = bg()
    center(d, 'КИНОНЫ ХАРИЛЦАЛАГА', 95, cfont(52), '#93c5fd')
    f = cfont(44); t = f"HSK {sc['level']}"; w = d.textlength(t, font=f)
    d.rounded_rectangle([(W - w) / 2 - 30, 170, (W + w) / 2 + 30, 240], 35, fill='#facc15'); d.text(((W - w) / 2, 177), t, font=f, fill='#1e293b')
    center(d, sc['title_zh'], 275, font(76), 'white')
    center(d, sc['title_mn'], 375, cfont(42), '#fde68a')
    L = sc['lines']; cur = L[upto]
    # одоогийн мөр том, өмнөхүүд жижиг хэлбэрээр дээр нь
    y = 470
    prev = L[max(0, upto - 2):upto]
    for who, zh, mn in prev:
        fz = font(48); lines = wrap(d, zh, fz, W - 300); hh = len(lines) * 62 + 36
        x0, x1 = (70, W - 230) if who == 'A' else (230, W - 70)
        d.rounded_rectangle([x0, y, x1, y + hh], 36, fill='#334e8a')
        for i, l in enumerate(lines): d.text((x0 + 36, y + 18 + i * 62), l, font=fz, fill='#cbd5e1')
        y += hh + 24
    who, zh, mn = cur
    role = sc['role_a'] if who == 'A' else sc['role_b']
    y = max(y + 20, 700)
    d.text((90, y), role, font=cfont(44), fill=COL[who]); y += 70
    fz = font(78); zl = wrap(d, zh, fz, W - 240)
    from pypinyin import pinyin, Style
    py = ' '.join(x[0] for x in pinyin(zh, style=Style.TONE) if x[0].isalpha())
    fp = cfont(40); pl = wrap(d, py, fp, W - 240)[:2]
    fm = cfont(48); ml = wrap(d, mn, fm, W - 240)[:4]
    hh = len(zl) * 104 + len(pl) * 54 + len(ml) * 66 + 110
    d.rounded_rectangle([60, y, W - 60, y + hh], 50, fill='white', outline=COL[who], width=10)
    yy = y + 36
    for l in zl: d.text((120, yy), l, font=fz, fill='#0f172a'); yy += 104
    for l in pl: d.text((120, yy), l, font=fp, fill='#2563eb'); yy += 54
    yy += 16
    for l in ml: d.text((120, yy), l, font=fm, fill='#475569'); yy += 66
    # ахиц
    n = len(L); bw = (W - 240) / n
    for i in range(n):
        d.rounded_rectangle([120 + i * bw, 1640, 120 + (i + 1) * bw - 8, 1656], 8, fill='#facc15' if i <= upto else '#475569')
    center(d, 'Дагаж, өдөр бүр хятад хэл сур', 1700, cfont(44), '#bfdbfe'); center(d, SITE, 1775, cfont(42), '#facc15')
    im.save(path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', type=int); ap.add_argument('--silent', action='store_true'); ap.add_argument('--min-gap', type=int, default=0)
    a = ap.parse_args()
    try: st = json.load(open(STATE))
    except Exception: st = {}
    if a.min_gap and time.time() - st.get('last', 0) < a.min_gap * 60:
        print('Алгасав'); go = os.environ.get('GITHUB_OUTPUT')
        if go: open(go, 'a').write('skipped=true\n')
        return
    S = json.load(open(os.path.join(M.HERE, 'scenes.json'), encoding='utf8'))
    num = a.index if a.index is not None else st.get('next', 0)
    sc = S[num % len(S)]
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        segs = []
        for i, (who, zh, mn) in enumerate(sc['lines']):
            img = os.path.join(tmp, f'f{i}.png'); frame(sc, i, img)
            w1 = say(zh, VOICE[who], '-5%', tmp, i, a.silent)
            pause = os.path.join(tmp, f'p{i}.wav'); silence(pause, 0.5)
            aud = os.path.join(tmp, f'a{i}.wav'); join([w1, pause], 0, aud)
            mp4 = os.path.join(tmp, f's{i}.mp4')
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', '30', '-i', img, '-i', aud, '-t', f'{probe(aud):.2f}',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '44100', '-shortest', mp4], check=True)
            segs.append(mp4)
        lst = os.path.join(tmp, 'l.txt'); open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
        out = os.path.join(OUT, f'scene-{num % len(S) + 1:04d}.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out], check=True)
    zh_all = '\n'.join(f'{w}: {z}' for w, z, m in sc['lines'])
    mn_all = '\n'.join(f'{w}: {m}' for w, z, m in sc['lines'])
    cap = (f"🎬 {sc['title_zh']} — {sc['title_mn']}\n🎓 HSK {sc['level']}\n\n{zh_all}\n\n🇲🇳 Орчуулга:\n{mn_all}\n\n"
           f"💾 Хадгалаад давтаарай ❤️ Найздаа илгээгээрэй\n👉 Үнэгүй сурах сайт: {SITE}\n\n#HSK #HSK{sc['level']} #хятадхэл #хятадхэлсурах #learnchinese #mandarin #中文 #монгол")
    open(out[:-4] + '.txt', 'w', encoding='utf8').write(cap)
    if not a.silent and a.index is None:
        json.dump({'next': num + 1, 'last': int(time.time())}, open(STATE, 'w'))
    print('Бэлэн:', out, round(probe(out), 1), 'сек', 'TTS алдаа:' if M.TTS_FAIL else '', M.TTS_FAIL)
    if M.TTS_FAIL and not a.silent:
        os.remove(out); sys.exit('Дуу үүсгэж чадсангүй')

if __name__ == '__main__': main()
