#!/usr/bin/env python3
"""Өдөр бүрийн HSK reel (9:16 mp4) үүсгэгч.
Үгийг ../index.html доторх өгөгдлөөс авна. Хятад хэлийг эхлээд ээлжлэн (удаан, хэвийн) уншина,
дараа нь монгол тайлбар, жишээ өгүүлбэр, давталт.
Хэрэглээ: python3 reel/make_reel.py [--level N] [--word 爱] [--silent]
Өдөрт 4 удаа ажиллана; HSK 1-ээс эхлэн үгсийг дарааллаар нь авна (reels/state.json дээр байр тэмдэглэнэ).
"""
import argparse, asyncio, datetime, json, os, re, subprocess, sys, wave, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get('REEL_OUT') or os.path.join(ROOT, 'reels')
HERE = os.path.dirname(os.path.abspath(__file__))
KEEP = 100
W, H = 1080, 1920
SITE = 'asta-13.github.io/Hsk5ji'
ZH_VOICE = os.environ.get('ZH_VOICE', 'zh-CN-XiaoxiaoNeural')   # өөр: zh-CN-XiaoyiNeural, zh-CN-YunxiNeural
MN_VOICE = os.environ.get('MN_VOICE') or 'mn-MN-YesuiNeural'      # эрэгтэй: mn-MN-BataaNeural
MN_RATE = os.environ.get('MN_RATE') or '-8%'      # монгол хоолойн хурд (жишээ -12%, +0%)
MN_PITCH = os.environ.get('MN_PITCH') or '+0Hz'   # өнгө (жишээ -3Hz, +3Hz)

FONT_CANDS = [
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc',
    '/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc',
]
def font(size):
    for p in FONT_CANDS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    sys.exit('Noto Sans CJK фонт олдсонгүй (sudo apt-get install fonts-noto-cjk)')

LATIN_CANDS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
]
def cfont(size):
    # Монгол кирилл (Ө, Ү) болон пиньиний аялгууны тэмдэгтэй фонт
    for p in LATIN_CANDS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return font(size)

# ---------- өгөгдөл ----------
def js_string(src, name):
    m = re.search(name + r'="((?:[^"\\]|\\.)*)"', src)
    return json.loads('"' + m.group(1) + '"')

def examples():
    try: return json.load(open(os.path.join(HERE, 'examples.json'), encoding='utf8'))
    except Exception: return {}

def sent_pinyin(z):
    try:
        from pypinyin import pinyin, Style
        return ' '.join(x[0] for x in pinyin(z, style=Style.TONE) if x[0].isalpha())
    except Exception: return ''

def load():
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf8').read()
    m = re.search(r'var HSKRAW=(\{.*?\});', src, re.S)
    raw = json.loads(m.group(1))
    mn = {}
    for it in js_string(src, 'HSKMN_RAW').split('|'):
        if '=' in it:
            k, v = it.split('=', 1); mn[k] = v
    gram = []
    for line in js_string(src, 'GRAM_RAW').split('\n'):
        a = line.split('|')
        if len(a) >= 5: gram.append((a[3], a[4]))
    words = {}
    for lv, s in raw.items():
        L = []
        for it in s.split(','):
            a = it.split('|')
            if len(a) >= 2 and a[0] in mn: L.append((a[0], a[1], mn[a[0]]))
        words[int(lv)] = L
    return words, gram

STATE = os.path.join(OUT, 'state.json')

def ordered(words):
    """HSK 1-ээс эхлээд түвшин түвшингээр дарааллаар (давхардлыг алгасана)."""
    seen, out = set(), []
    for lv in sorted(words):
        for w in words[lv]:
            if w[0] not in seen and len(w[0]) <= 6:
                seen.add(w[0]); out.append((lv, w))
    return out

def pick(words, level=None, word=None):
    """Буцаах: (түвшин, үг, дугаар|None). Дугаар нь дараалсан горимд л байна."""
    if word:
        for lv, L in words.items():
            for w in L:
                if w[0] == word: return lv, w, None
        sys.exit('Үг олдсонгүй: ' + word)
    seq = ordered(words)
    if level: seq = [x for x in seq if x[0] == level]
    try: n = json.load(open(STATE))['next']
    except Exception: n = 0
    if level: return seq[n % len(seq)][0], seq[n % len(seq)][1], None
    n %= len(seq)
    return seq[n][0], seq[n][1], n

# ---------- дуу ----------
def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True)
    return float(r.stdout.strip())

def to_wav(src, dst):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-ar', '24000', '-ac', '1', '-sample_fmt', 's16', dst], check=True)

def silence(path, sec):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
        w.writeframes(b'\x00\x00' * int(24000 * sec))

async def tts_async(text, voice, rate, path):
    import edge_tts
    pitch = MN_PITCH if voice.startswith('mn-') else '+0Hz'
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(path)

TTS_FAIL = []
def say(text, voice, rate, tmp, idx, silent):
    wav = os.path.join(tmp, f'c{idx}.wav')
    if not silent:
        mp3 = os.path.join(tmp, f'c{idx}.mp3')
        try:
            asyncio.run(tts_async(text, voice, rate, mp3)); to_wav(mp3, wav); return wav
        except Exception as e:
            print('TTS алдаа (' + text[:12] + '):', e); TTS_FAIL.append(text)
    silence(wav, max(1.2, len(text) * 0.25)); return wav

def join(wavs, gap, dst):
    gp = dst + '.gap.wav'; silence(gp, gap)
    with wave.open(dst, 'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(24000)
        for i, p in enumerate(wavs):
            for q in ([gp] if i else []) + [p]:
                with wave.open(q, 'rb') as r: out.writeframes(r.readframes(r.getnframes()))
    os.remove(gp)

# ---------- зураг ----------
def bg():
    im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(30 + 10 * t), int(58 - 25 * t), int(138 - 70 * t)))
    return im, d

def center(d, text, y, f, fill='white'):
    w = d.textlength(text, font=f); d.text(((W - w) / 2, y), text, font=f, fill=fill)

def wrap(d, text, f, maxw):
    lines, cur = [], ''
    for ch in text:
        if d.textlength(cur + ch, font=f) > maxw and cur:
            lines.append(cur); cur = ch
        else: cur += ch
    if cur: lines.append(cur)
    return lines

def header(d, lv):
    center(d, 'ӨДРИЙН ҮГ', 130, cfont(56), '#93c5fd')
    f = cfont(48); t = f'HSK {lv}'; w = d.textlength(t, font=f)
    d.rounded_rectangle([(W - w) / 2 - 36, 220, (W + w) / 2 + 36, 306], 43, fill='#facc15')
    d.text(((W - w) / 2, 228), t, font=f, fill='#1e293b')

def footer(d):
    center(d, 'Дагаж, өдөр бүр нэг үг сур', 1700, cfont(44), '#bfdbfe')
    center(d, SITE, 1775, cfont(42), '#facc15')

def hanzi_size(t): return 420 if len(t) == 1 else 300 if len(t) == 2 else 200 if len(t) == 3 else 150 if len(t) == 4 else 120

EX_PY = ''
def scene_img(kind, lv, w, ex, path):
    ex_py = EX_PY
    im, d = bg(); header(d, lv); han, py, mn = w
    hs = hanzi_size(han)
    if kind == 'word':
        center(d, han, 600, font(hs), 'white'); center(d, py, 600 + hs + 90, cfont(100), '#fde68a')
    elif kind == 'meaning':
        center(d, han, 420, font(min(hs, 300)), 'white'); center(d, py, 420 + min(hs, 300) + 70, cfont(80), '#fde68a')
        y = 1000
        d.rounded_rectangle([90, y, W - 90, y + 460], 50, fill='white')
        f = cfont(84 if len(mn) < 14 else 60); L = wrap(d, mn, f, W - 260)[:4]
        top = y + (460 - len(L) * (f.size + 20)) / 2
        for i, l in enumerate(L): center(d, l, top + i * (f.size + 20), f, '#1e3a8a')
    elif kind == 'example':
        center(d, 'ЖИШЭЭ', 440, cfont(58), '#93c5fd')
        d.rounded_rectangle([70, 540, W - 70, 1380], 50, fill='white')
        f = font(100); L = wrap(d, ex[0], f, W - 240)[:4]; y = 600
        for l in L:
            center(d, l, y, f, '#0f172a'); y += 135
        if ex_py:
            fp = cfont(40)
            for l in wrap(d, ex_py, fp, W - 240)[:2]:
                center(d, l, y + 10, fp, '#2563eb'); y += 56
        f2 = cfont(50); L2 = wrap(d, ex[1], f2, W - 240)[:4]; y = max(y + 60, 1050)
        for l in L2:
            center(d, l, y, f2, '#475569'); y += 90
    else:  # repeat
        center(d, 'ДАХИН ДАВТЪЯ', 440, cfont(62), '#93c5fd')
        center(d, han, 640, font(hs), 'white'); center(d, py, 640 + hs + 90, cfont(100), '#fde68a')
    footer(d); im.save(path)

def render(kind, lv, w, ex, wavs, gap, tmp, n):
    img = os.path.join(tmp, f's{n}.png'); aud = os.path.join(tmp, f's{n}.wav'); mp4 = os.path.join(tmp, f's{n}.mp4')
    scene_img(kind, lv, w, ex, img); join(wavs, gap, aud)
    dur = probe(aud) + 0.7
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', '30', '-i', img, '-i', aud, '-t', f'{dur:.2f}',
                    '-af', 'apad', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '44100', '-shortest', mp4], check=True)
    return mp4

HOOKS = [
    '🇨🇳 Энэ үгийг мэдэх үү?',
    '📚 Өнөөдөр нэг үг сурцгаая!',
    '🤔 Хятадаар хэрхэн хэлэх вэ?',
    '💡 Өдөр бүр 1 үг = жилд 365 үг!',
    '🔥 HSK шалгалтад заавал таардаг үг!',
    '👀 Үүнийг санаж аваарай!',
]
TAGS = ['#HSK', '#хятадхэл', '#хятадхэлсурах', '#хятад', '#mongolia', '#монгол', '#chinese', '#learnchinese', '#mandarin', '#中文', '#汉语']

def make_caption(han, py, mn, lv, ex, ex_py, num):
    k = (num if num is not None else datetime.date.today().toordinal()) % len(HOOKS)
    lines = [HOOKS[k], '', f'📌 {han}  [{py}]', f'🇲🇳 {mn}', f'🎓 HSK {lv}']
    if ex:
        lines += ['', '🗣 Жишээ:', ex[0]] + ([ex_py] if ex_py else []) + [ex[1]]
    lines += ['', '💾 Хадгалаад дараа давтаарай', '❤️ Таалагдвал like дарж, найздаа илгээгээрэй', '➕ Өдөр бүр шинэ үг — дагаж аваарай!', '',
              f'👉 Үнэгүй сурах сайт: {SITE}', '', f'{TAGS[0]} #HSK{lv} ' + ' '.join(TAGS[1:])]
    return '\n'.join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--level', type=int); ap.add_argument('--word'); ap.add_argument('--silent', action='store_true')
    a = ap.parse_args()
    global EX_PY
    words, gram = load(); lv, w, num = pick(words, a.level, a.word)
    han, py, mn = w; print('Үг:', han, py, mn, '(HSK', lv, ')', '#' + str(num + 1) if num is not None else '')
    exs = examples()
    ex = tuple(exs[han]) if han in exs else next(((z, t) for z, t in gram if han in z and z != han), None)
    ex_py = EX_PY = sent_pinyin(ex[0]) if ex else ''
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        c = lambda t, v, r, i: say(t, v, r, tmp, i, a.silent)
        zs, zn = c(han, ZH_VOICE, '-30%', 1), c(han, ZH_VOICE, '+0%', 2)
        scenes = [render('word', lv, w, ex, [zs, zn], 0.5, tmp, 0)]
        scenes.append(render('meaning', lv, w, ex, [c('Утга нь... ' + mn.replace(',', ', ').replace('(', ', ').replace(')', '').strip() + '.', MN_VOICE, MN_RATE, 3)], 0, tmp, 1))
        if ex: scenes.append(render('example', lv, w, ex, [c(ex[0], ZH_VOICE, '-25%', 4), c(ex[0], ZH_VOICE, '+0%', 5), c('Орчуулбал... ' + ex[1], MN_VOICE, MN_RATE, 6)], 0.5, tmp, 2))
        scenes.append(render('repeat', lv, w, ex, [zn, zs, zn], 0.6, tmp, 3))
        lst = os.path.join(tmp, 'list.txt')
        open(lst, 'w').write(''.join(f"file '{s}'\n" for s in scenes))
        tag = f'{num + 1:04d}' if num is not None else datetime.datetime.now().strftime('manual-%Y%m%d-%H%M%S')
        out = os.path.join(OUT, f'reel-{tag}.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out], check=True)
    cap = make_caption(han, py, mn, lv, ex, ex_py, num)
    open(out[:-4] + '.txt', 'w', encoding='utf8').write(cap)
    if num is not None and not a.silent:
        json.dump({'next': num + 1}, open(STATE, 'w'))
        keep = sorted(f[:-4] for f in os.listdir(OUT) if f.startswith('reel-') and f.endswith('.mp4'))[:-KEEP]
        for k in keep:
            for ext in ('.mp4', '.txt'):
                try: os.remove(os.path.join(OUT, k + ext))
                except OSError: pass
    print('Бэлэн:', out, round(probe(out), 1), 'сек')
    if TTS_FAIL:
        os.remove(out); os.remove(out[:-4] + '.txt'); sys.exit('Дуу үүсгэж чадсангүй: ' + ', '.join(TTS_FAIL))

if __name__ == '__main__': main()
