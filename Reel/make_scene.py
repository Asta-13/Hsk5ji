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


THEMES = [
    ('hospital', '医病药'), ('transport', '出租车路车站火车机场飞机票'), ('market', '水果价钱市场衣服买还价手机'),
    ('restaurant', '饭吃餐菜做饭厨'), ('school', '教室学图书馆大学专业考试面试工作电脑签证'), ('hotel', '酒店房间租住旅行'),
]
FALL = ['home', 'park', 'street']
def theme_of(sc, num):
    t = sc['title_zh']
    for name, keys in THEMES:
        if any(k in t for k in keys): return name
    return FALL[num % len(FALL)]

def set_bg(d, th):
    FL = 1610
    def rect(a, b, c, e, col, r=0): d.rounded_rectangle([a, b, c, e], r, fill=col)
    if th == 'hospital':
        rect(0, 900, W, FL, '#e0f2fe'); rect(0, FL - 20, W, H, '#94a3b8')
        rect(430, 960, 650, 1180, '#ffffff', 30); rect(520, 985, 560, 1155, '#ef4444'); rect(465, 1040, 615, 1100, '#ef4444')
        rect(80, 1250, 300, 1330, '#bae6fd', 20); rect(780, 1250, 1000, 1330, '#bae6fd', 20)
    elif th == 'transport':
        rect(0, 1000, W, FL - 70, '#334155'); rect(0, FL - 70, W, H, '#475569')
        for x in range(0, W, 180): rect(x, FL - 150, x + 90, FL - 135, '#facc15')
        rect(80, 880, 330, 1000, '#1e293b', 20); rect(380, 840, 700, 1000, '#0f172a', 20); rect(760, 900, 1020, 1000, '#1e293b', 20)
        for x in (110, 410, 790): rect(x, 900, x + 40, 930, '#fde047')
        rect(700, 1370, 1010, 1470, '#ef4444', 40); d.ellipse([730, 1440, 790, 1500], fill='#0f172a'); d.ellipse([920, 1440, 980, 1500], fill='#0f172a')
    elif th == 'market':
        rect(0, 900, W, FL, '#fef3c7'); rect(0, FL - 20, W, H, '#a16207')
        for i in range(8): rect(40 + i * 125, 880, 40 + i * 125 + 125, 980, '#ef4444' if i % 2 == 0 else '#ffffff')
        rect(60, 1230, 1020, 1300, '#92400e', 14)
        for i, c in enumerate(['#ef4444', '#f97316', '#84cc16', '#facc15', '#ef4444', '#f97316', '#84cc16']): d.ellipse([110 + i * 130, 1180, 190 + i * 130, 1260], fill=c)
    elif th == 'restaurant':
        rect(0, 900, W, FL, '#7c2d12'); rect(0, FL - 20, W, H, '#451a03')
        for x in (200, 540, 880): d.line([(x, 880), (x, 1000)], fill='#fde68a', width=6); d.ellipse([x - 60, 1000, x + 60, 1070], fill='#fde68a')
        rect(260, 1400, 820, 1440, '#d97706', 12); rect(300, 1440, 330, 1610, '#b45309'); rect(750, 1440, 780, 1610, '#b45309')
        d.ellipse([440, 1340, 640, 1400], fill='#ffffff'); d.ellipse([480, 1350, 600, 1385], fill='#f97316')
    elif th == 'school':
        rect(0, 900, W, FL, '#ccfbf1'); rect(0, FL - 20, W, H, '#a8a29e')
        rect(160, 940, 920, 1250, '#14532d', 16); rect(180, 960, 900, 1230, '#166534', 10)
        d.line([(260, 1030), (520, 1030)], fill='white', width=8); d.line([(260, 1100), (700, 1100)], fill='white', width=8); d.line([(260, 1170), (600, 1170)], fill='white', width=8)
        rect(60, 1380, 260, 1420, '#a16207'); rect(820, 1380, 1020, 1420, '#a16207')
    elif th == 'hotel':
        rect(0, 900, W, FL, '#ede9fe'); rect(0, FL - 20, W, H, '#7c3aed')
        rect(80, 960, 360, 1240, '#bfdbfe', 14); d.line([(220, 960), (220, 1240)], fill='white', width=8); d.line([(80, 1100), (360, 1100)], fill='white', width=8)
        rect(560, 1300, 1030, 1480, '#fda4af', 30); rect(560, 1250, 760, 1330, '#ffffff', 30)
    elif th == 'park':
        rect(0, 900, W, FL, '#bae6fd'); rect(0, FL - 120, W, H, '#16a34a')
        d.ellipse([820, 940, 960, 1080], fill='#fde047')
        for x in (120, 940): d.rectangle([x - 18, 1280, x + 18, FL - 100], fill='#92400e'); d.ellipse([x - 110, 1080, x + 110, 1320], fill='#15803d')
    elif th == 'street':
        rect(0, 900, W, FL - 70, '#cbd5e1'); rect(0, FL - 70, W, H, '#475569')
        for i, (x, h) in enumerate([(40, 380), (260, 300), (480, 440), (720, 330), (900, 400)]):
            rect(x, FL - 70 - h, x + 180, FL - 70, ['#64748b', '#94a3b8', '#475569', '#78716c', '#64748b'][i])
            for yy in range(FL - 70 - h + 30, FL - 120, 70): rect(x + 30, yy, x + 70, yy + 36, '#fde68a'); rect(x + 110, yy, x + 150, yy + 36, '#fde68a')
    else:  # home
        rect(0, 900, W, FL, '#fce7f3'); rect(0, FL - 20, W, H, '#92400e')
        rect(120, 960, 360, 1180, '#bfdbfe', 14); d.line([(240, 960), (240, 1180)], fill='white', width=8)
        rect(640, 1250, 1010, 1420, '#a78bfa', 36); rect(640, 1180, 1010, 1290, '#8b5cf6', 36)

def stick(d, cx, feet, who, speaking, t):
    col = '#f472b6' if who == 'A' else '#38bdf8'
    bob = (6 if t % 2 else 0) if speaking else 0
    top = feet - 330 - bob
    hy = top + 48
    lw = 15; ink = '#0f172a'
    # legs
    d.line([(cx, feet - 140), (cx - 45, feet)], fill=ink, width=lw); d.line([(cx, feet - 140), (cx + 45, feet)], fill=ink, width=lw)
    # body
    d.line([(cx, hy + 46), (cx, feet - 140)], fill=col, width=lw + 4)
    # arms
    sh = hy + 80
    d.line([(cx, sh), (cx - 60, sh + 90)], fill=col, width=lw)
    if speaking:
        up = -70 if t % 2 else -30
        d.line([(cx, sh), (cx + 70, sh + up)], fill=col, width=lw)
    else:
        d.line([(cx, sh), (cx + 60, sh + 90)], fill=col, width=lw)
    # head
    d.ellipse([cx - 48, hy - 48, cx + 48, hy + 48], fill='#fef3c7', outline=ink, width=6)
    d.ellipse([cx - 22, hy - 12, cx - 10, hy], fill=ink); d.ellipse([cx + 10, hy - 12, cx + 22, hy], fill=ink)
    if speaking and t % 2: d.ellipse([cx - 14, hy + 14, cx + 14, hy + 38], fill='#be123c')
    else: d.arc([cx - 20, hy + 8, cx + 20, hy + 34], 20, 160, fill=ink, width=5)
    if who == 'A':  # ponytail + bow
        d.ellipse([cx + 36, hy - 40, cx + 80, hy + 10], fill='#7c2d12'); d.pieslice([cx - 48, hy - 50, cx + 48, hy + 30], 180, 360, fill='#7c2d12')
        d.polygon([(cx, hy - 52), (cx - 24, hy - 72), (cx - 24, hy - 38)], fill='#f472b6'); d.polygon([(cx, hy - 52), (cx + 24, hy - 72), (cx + 24, hy - 38)], fill='#f472b6')
    else:  # cap
        d.pieslice([cx - 50, hy - 56, cx + 50, hy + 24], 180, 360, fill='#0369a1'); d.rectangle([cx - 52, hy - 22, cx + 70, hy - 14], fill='#0369a1')

def frame(sc, upto, path, t=0, th='home'):
    im, d = bg(); set_bg(d, th)
    center(d, 'КИНОНЫ ХАРИЛЦАЛАГА', 95, cfont(52), '#93c5fd')
    f = cfont(44); hk = f"HSK {sc['level']}"; w = d.textlength(hk, font=f)
    d.rounded_rectangle([(W - w) / 2 - 30, 170, (W + w) / 2 + 30, 240], 35, fill='#facc15'); d.text(((W - w) / 2, 177), hk, font=f, fill='#1e293b')
    center(d, sc['title_zh'], 275, font(76), 'white')
    center(d, sc['title_mn'], 375, cfont(42), '#fde68a')
    L = sc['lines']; cur = L[upto]
    # одоогийн мөр том, өмнөхүүд жижиг хэлбэрээр дээр нь
    y = 470
    prev = L[max(0, upto - 1):upto]
    for who, zh, mn in prev:
        fz = font(48); lines = wrap(d, zh, fz, W - 300); hh = len(lines) * 62 + 36
        x0, x1 = (70, W - 230) if who == 'A' else (230, W - 70)
        d.rounded_rectangle([x0, y, x1, y + hh], 36, fill='#334e8a')
        for i, l in enumerate(lines): d.text((x0 + 36, y + 18 + i * 62), l, font=fz, fill='#cbd5e1')
        y += hh + 24
    who, zh, mn = cur
    role = sc['role_a'] if who == 'A' else sc['role_b']
    y = max(y + 10, 590)
    d.text((90, y), role, font=cfont(44), fill=COL[who]); y += 70
    fz = font(78 if len(zh) <= 10 else 64); zl = wrap(d, zh, fz, W - 240)
    from pypinyin import pinyin, Style
    py = ' '.join(x[0] for x in pinyin(zh, style=Style.TONE) if x[0].isalpha())
    fp = cfont(40); pl = wrap(d, py, fp, W - 240)[:2]
    fm = cfont(48); ml = wrap(d, mn, fm, W - 240)[:4]
    hh = len(zl) * (104 if len(zh) <= 10 else 86) + len(pl) * 54 + len(ml) * 66 + 110
    d.rounded_rectangle([60, y, W - 60, y + hh], 50, fill='white', outline=COL[who], width=10)
    yy = y + 36
    for l in zl: d.text((120, yy), l, font=fz, fill='#0f172a'); yy += (104 if len(zh) <= 10 else 86)
    for l in pl: d.text((120, yy), l, font=fp, fill='#2563eb'); yy += 54
    yy += 16
    for l in ml: d.text((120, yy), l, font=fm, fill='#475569'); yy += 66
    # дүрүүд
    FEET = 1600; xs = {'A': 290, 'B': 790}
    for w2 in ('A', 'B'): stick(d, xs[w2], FEET, w2, w2 == who, t)
    if y + hh < 1230:
        cxs = xs[who]; d.polygon([(cxs - 30, y + hh - 4), (cxs + 30, y + hh - 4), (cxs, min(y + hh + 70, 1240))], fill='white')
    # ахиц
    n = len(L); bw = (W - 240) / n
    for i in range(n):
        d.rounded_rectangle([120 + i * bw, 1640, 120 + (i + 1) * bw - 8, 1656], 8, fill='#facc15' if i <= upto else '#475569')
    center(d, 'Дагаж, өдөр бүр хятад хэл сур', 1700, cfont(44), '#bfdbfe'); center(d, SITE, 1775, cfont(42), '#facc15')
    im.save(path)

def card(sc, kind, path):
    im, d = bg()
    if kind == 'hook':
        center(d, '🎬'.replace('🎬', 'КИНОНЫ ХАРИЛЦАЛАГА'), 330, cfont(56), '#93c5fd')
        center(d, f"HSK {sc['level']}", 440, cfont(60), '#facc15')
        for i, l in enumerate(wrap(d, sc['title_zh'], font(120), W - 160)[:2]): center(d, l, 640 + i * 150, font(120), 'white')
        for i, l in enumerate(wrap(d, sc['title_mn'], cfont(56), W - 200)[:2]): center(d, l, 1000 + i * 80, cfont(56), '#fde68a')
        center(d, 'Хэчнээн үгийг нь ойлгох вэ? 👀'.replace(' 👀', ''), 1350, cfont(52), '#bfdbfe')
    else:
        center(d, 'ДАХИН САНА', 200, cfont(64), '#93c5fd')
        y = 340
        for who, zh, mn in sc['lines'][:6]:
            col = COL[who]
            for l in wrap(d, zh, font(54), W - 160)[:1]: d.text((80, y), l, font=font(54), fill='white'); y += 70
            for l in wrap(d, mn, cfont(36), W - 160)[:2]: d.text((80, y), l, font=cfont(36), fill='#fde68a'); y += 50
            y += 22
        center(d, 'Ойлгосон бол комментд 1 гэж бич!', 1560, cfont(46), '#facc15')
        center(d, SITE, 1775, cfont(42), '#facc15')
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
    sc = S[num % len(S)]; th = theme_of(sc, num)
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        segs = []
        for kind in ('hook',):
            img = os.path.join(tmp, kind + '.png'); card(sc, kind, img); aud = os.path.join(tmp, kind + '.wav'); silence(aud, 2.2)
            mp4 = os.path.join(tmp, kind + '.mp4')
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', '30', '-i', img, '-i', aud, '-t', '2.2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '44100', '-shortest', mp4], check=True)
            segs.append(mp4)
        for i, (who, zh, mn) in enumerate(sc['lines']):
            w1 = say(zh, VOICE[who], '-5%', tmp, i, a.silent)
            pause = os.path.join(tmp, f'p{i}.wav'); silence(pause, 0.5)
            aud = os.path.join(tmp, f'a{i}.wav'); join([w1, pause], 0, aud)
            dur = probe(aud); nf = max(2, int(dur * 4))
            fd = os.path.join(tmp, f'fr{i}'); os.makedirs(fd)
            for t in range(nf): frame(sc, i, os.path.join(fd, f'f{t:03d}.png'), t, th)
            mp4 = os.path.join(tmp, f's{i}.mp4')
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '4', '-i', os.path.join(fd, 'f%03d.png'), '-i', aud, '-r', '30',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '44100', '-shortest', mp4], check=True)
            segs.append(mp4)
        img = os.path.join(tmp, 'end.png'); card(sc, 'end', img); aud = os.path.join(tmp, 'end.wav'); silence(aud, 5.0); mp4 = os.path.join(tmp, 'end.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', '30', '-i', img, '-i', aud, '-t', '5', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '44100', '-shortest', mp4], check=True)
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
