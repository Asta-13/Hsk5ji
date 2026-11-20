#!/usr/bin/env python3
"""Өдөр бүрийн HSK reel (9:16 mp4) үүсгэгч.
Үгийг ../index.html доторх өгөгдлөөс авна. Хятад хэлийг эхлээд ээлжлэн (удаан, хэвийн) уншина,
дараа нь монгол тайлбар, жишээ өгүүлбэр, давталт.
Хэрэглээ: python3 reel/make_reel.py [--level N] [--word 爱] [--silent]
Өдөрт 4 удаа ажиллана; HSK 1-ээс эхлэн үгсийг дарааллаар нь авна (дугаар, заасан үгсийг reels/series.json дээр тэмдэглэнэ; Reel/series.py).
"""
import argparse, asyncio, datetime, faulthandler, json, os, re, subprocess, sys, time, wave, tempfile
from PIL import Image, ImageDraw, ImageFont

def start_watchdog(sec=None):
    """Ямар нэг юм гацвал (сүлжээ, ffmpeg) 15 минут чимээгүй хүлээхийн оронд N секундын дараа
    бүх thread-ийн байрлалыг лог руу хэвлэж, процессыг зогсооно → алдаа хаана гацсан нь Actions-ийн логоос харагдана."""
    sec = int(sec or os.environ.get('WATCHDOG_SEC') or 540)
    faulthandler.dump_traceback_later(sec, exit=True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get('REEL_OUT') or os.path.join(ROOT, 'reels')
HERE = os.path.dirname(os.path.abspath(__file__))
KEEP = 100
W, H = 1080, 1920
# Instagram Reels-ийн дээд (нэр, камер) ба доод (тайлбар, дуу, товчнууд) UI-ийн доор үсэг орвол халхлагдана.
# Бүх чухал зүйлийг SAFE_TOP..SAFE_BOTTOM завсарт, зүүн/баруун PAD-аас дотогш байрлуул.
PAD = 110
SAFE_TOP, SAFE_BOTTOM = 270, 1480
FOOT_Y = 1425
DITHER = float(os.environ.get('REEL_DITHER') or 0)      # дэвсгэрийн «үр» (banding арилгана, гэхдээ файл ~2-3 дахин том болно; жишээ нь 0.8)
CRF = os.environ.get('REEL_CRF') or '22'                 # эцсийн видеоны чанар: бага = чанартай/том (18-26)
SITE = 'asta-13.github.io/Hsk5ji'
import series as SR
BADGE = None   # (төрөл, дугаар): тохируулбал bg() бүрийн баруун дээд буланд «#35» тэмдэг зурна
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
    """Өгөгдлийг data/*.json-оос уншина (шинэ бүтэц); байхгүй бол хуучин index.html-ээс."""
    D = os.path.join(ROOT, 'data')
    if os.path.exists(os.path.join(D, 'hsk-words.json')):
        rd = lambda f: json.load(open(os.path.join(D, f), encoding='utf8'))
        raw, mn_raw, gram_raw = rd('hsk-words.json'), rd('hsk-mongolian.json'), rd('grammar.json')
    else:
        src = open(os.path.join(ROOT, 'index.html'), encoding='utf8').read()
        raw = json.loads(re.search(r'var HSKRAW=(\{.*?\});', src, re.S).group(1))
        mn_raw, gram_raw = js_string(src, 'HSKMN_RAW'), js_string(src, 'GRAM_RAW')
    mn = {}
    for it in mn_raw.split('|'):
        if '=' in it:
            k, v = it.split('=', 1); mn[k] = v
    gram = []
    for line in gram_raw.split('\n'):
        a = line.split('|')
        if len(a) >= 5: gram.append((a[3], a[4]))
    try: fix = json.load(open(os.path.join(HERE, 'word_overrides.json'), encoding='utf8')).get('pinyin_fix', {})
    except Exception: fix = {}
    def clean_py(h, p):
        # Эх өгөгдөлд нэг үсэгт үгийн пиньинь заримдаа буруу дуудлагатай эсвэл том үсгээр эхэлсэн байдаг.
        if h in fix: return fix[h]
        return p[:1].lower() + p[1:] if len(h) == 1 else p
    words = {}
    for lv, s in raw.items():
        L = []
        for it in s.split(','):
            a = it.split('|')
            if len(a) >= 2 and a[0] in mn: L.append((a[0], clean_py(a[0], a[1]), mn[a[0]]))
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

LOUDNORM = 'loudnorm=I=-15:TP=-1.5:LRA=9'   # Instagram/TikTok-д тохирсон дууны түвшин
TTS_TIMEOUT = 25      # нэг оролдлогын дээд хугацаа (сек). Богино өгүүлбэр ихэвчлэн 1-3 сек.
FEMALE = ('Xiaoxiao', 'Xiaoyi')

async def tts_async(text, voice, rate, path):
    import edge_tts
    pitch = MN_PITCH if voice.startswith('mn-') else '+0Hz'
    await asyncio.wait_for(edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(path), timeout=TTS_TIMEOUT)

def alt_voice(voice):
    """Сүүлийн оролдлогод ижил хүйсийн өөр хоолой хэрэглэнэ (нэг хоолой түр доголдож болдог)."""
    if voice.startswith('mn-'):
        return 'mn-MN-BataaNeural' if 'Yesui' in voice else 'mn-MN-YesuiNeural'
    fem = any(f in voice for f in FEMALE)
    base = 'zh-CN-XiaoxiaoNeural' if fem else 'zh-CN-YunxiNeural'
    if voice == base: base = 'zh-CN-XiaoyiNeural' if fem else 'zh-CN-YunjianNeural'
    return base

TTS_FAIL = []
TTS_DEAD = False      # нэг өгүүлбэр бүх оролдлогоор бүтэлгүйтвэл (сервис унасан) үлдсэнийг оролдохгүй, түргэн алдаатай дуусна
def say(text, voice, rate, tmp, idx, silent):
    global TTS_DEAD
    wav = os.path.join(tmp, f'c{idx}.wav')
    if not silent and not TTS_DEAD:
        mp3 = os.path.join(tmp, f'c{idx}.mp3')
        plan = [(voice, 0), (voice, 2), (alt_voice(voice), 4)]
        for n, (v, wait) in enumerate(plan, 1):
            time.sleep(wait)
            try:
                asyncio.run(tts_async(text, v, rate, mp3))
                if os.path.getsize(mp3) < 800: raise RuntimeError('аудио хэт жижиг')
                to_wav(mp3, wav)
                if probe(wav) < 0.25: raise RuntimeError('аудио хоосон')
                if n > 1: print(f'TTS {n}-р оролдлогоор бүтлээ ({v})', flush=True)
                return wav
            except Exception as e:
                print(f'TTS алдаа {n}/{len(plan)} [{v}] "{text[:12]}": {type(e).__name__}: {e}', flush=True)
        TTS_FAIL.append(text); TTS_DEAD = True
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
_BG = None
def badge(d, kind, n):
    """Баруун дээд булан (Instagram-ын дээд UI-ийн доор, баруун товчнуудын дээр): өнгөт «#35» + төрлийн нэр."""
    col = SR.KINDS[kind][2]; f = cfont(46); t = f'#{n}'; w = d.textlength(t, font=f); x1 = W - 40; x0 = x1 - w - 44
    d.rounded_rectangle([x0, 278, x1, 342], 32, fill=col); d.text((x0 + 22, 284), t, font=f, fill='#0f172a')
    lf = cfont(30); lab = SR.KINDS[kind][1].upper(); d.text((x1 - d.textlength(lab, font=lf), 350), lab, font=lf, fill=col)

TEACHER_MOOD = 'hi'      # hi · cheer · think — дүрийн сэтгэл (Reel/teacher/*.png)
TEACHER_SIZE = 170
IG_HANDLE = os.environ.get('IG_HANDLE') or 'hanzilaoshi'
_TCH = {}
def teacher(im):
    """Ханзи багш (汉字老师) — зүүн дээд буланд (Instagram-ын UI-д халхлагдахгүй, гарчгийн зүүн талд)."""
    m = TEACHER_MOOD
    if m not in _TCH:
        try: _TCH[m] = Image.open(os.path.join(HERE, 'teacher', m + '.png')).convert('RGBA').resize((TEACHER_SIZE, int(TEACHER_SIZE * 456 / 464)), Image.LANCZOS)
        except Exception: _TCH[m] = None
    t = _TCH[m]
    if t: im.paste(t, (16, 262), t)

def bg():
    """Градиент дэвсгэр. REEL_DITHER>0 үед маш бага тогтмол «үр» нэмж градиентын зэрэглэлийг (banding) зөөлрүүлнэ."""
    global _BG
    if _BG is None:
        from PIL import ImageChops
        g = Image.new('RGB', (W, H)); gd = ImageDraw.Draw(g)
        for y in range(H):
            t = y / H
            gd.line([(0, y), (W, y)], fill=(int(30 + 10 * t), int(58 - 25 * t), int(138 - 70 * t)))
        _BG = ImageChops.add(g, Image.effect_noise((W, H), DITHER).convert('RGB'), 1.0, -128) if DITHER > 0 else g
    im = _BG.copy(); d = ImageDraw.Draw(im)
    if BADGE: badge(d, *BADGE)
    teacher(im)
    return im, d

def center(d, text, y, f, fill='white'):
    w = d.textlength(text, font=f); d.text(((W - w) / 2, y), text, font=f, fill=fill)

def wrap(d, text, f, maxw):
    """Хятад үсгийг тэмдэгтээр, кирилл/латин үгийг үгийн зааг дээр таслана (үг дундаа тасрахгүй)."""
    lines, cur = [], ''
    toks = re.findall(r'[A-Za-z\u0400-\u04FF0-9\u0300-\u036F\u0101-\u017F\u00E0-\u00FC\'’\-.,!?:;()…“”"/%+=]+\s*|\s+|.', text)
    for tk in toks:
        if d.textlength((cur + tk).rstrip(), font=f) > maxw and cur:
            lines.append(cur.rstrip()); cur = tk.lstrip()
            while d.textlength(cur.rstrip(), font=f) > maxw and len(cur) > 1:   # маш урт үг
                k = len(cur) - 1
                while k > 1 and d.textlength(cur[:k], font=f) > maxw: k -= 1
                lines.append(cur[:k]); cur = cur[k:]
        else: cur += tk
    if cur.strip(): lines.append(cur.rstrip())
    return lines

def header(d, lv, label):
    """Дээд хэсэг: хөшүүрэг (hook) асуулт/гарчиг + HSK түвшин. Бүгд SAFE_TOP-оос доош."""
    center(d, label, 285, cfont(56), '#93c5fd')
    f = cfont(46); t = f'HSK {lv}'; w = d.textlength(t, font=f)
    d.rounded_rectangle([(W - w) / 2 - 32, 365, (W + w) / 2 + 32, 440], 38, fill='#facc15')
    d.text(((W - w) / 2, 372), t, font=f, fill='#1e293b')

def footer(d):
    center(d, f'@{IG_HANDLE} · {SITE}', FOOT_Y, cfont(36), '#facc15')

_FULL = {',': '，', '?': '？', '!': '！', ';': '；', ':': '：'}
def zh_punct(t):
    return re.sub(r'(?<=[\u4e00-\u9fff])[,?!;:]', lambda m: _FULL[m.group(0)], t)

def hanzi_size(t): return 420 if len(t) == 1 else 300 if len(t) == 2 else 200 if len(t) == 3 else 150 if len(t) == 4 else 120

def fit(d, text, mk, size, maxw, minsize=40):
    """Текст maxw-д багтах хүртэл фонтыг багасгана (урт пиньинь/монгол үг хажуу тийш халихгүй)."""
    while size > minsize and d.textlength(text, font=mk(size)) > maxw: size -= 4
    return mk(size)

def draw_hl(d, line, f, y, hl, off, color='#0f172a', hlc='#dc2626'):
    """Хятад мөрийг төвд зурж, hl=(эхлэл, төгсгөл) завсрын тэмдэгтүүдийг тодруулна (off = мөрийн эхний тэмдэгтийн дугаар)."""
    ws = [d.textlength(ch, font=f) for ch in line]
    x = (W - sum(ws)) / 2
    for i, ch in enumerate(line):
        d.text((x, y), ch, font=f, fill=hlc if hl and hl[0] <= off + i < hl[1] else color)
        x += ws[i]

LABELS = {'word': 'Энэ үгийг мэдэх үү?', 'meaning': 'Монгол утга', 'example': 'Жишээ өгүүлбэр', 'repeat': 'Дагаж хэлээрэй!'}

EX_PY = ''
def scene_img(kind, lv, w, ex, path, stage=2):
    """stage: жишээ дэлгэцэд 1 = хятад өгүүлбэр л, 2 = орчуулгатай нь (дуутай нь хамт аажим гарна)."""
    ex_py = EX_PY
    im, d = bg(); header(d, lv, LABELS[kind]); han, py, mn = w
    hs = hanzi_size(han); inner = W - 2 * PAD
    if kind in ('word', 'repeat'):
        blk = hs * 1.2 + 90 + 110
        y0 = 480 + (SAFE_BOTTOM - 60 - 480 - blk) / 2
        center(d, han, y0, font(hs), 'white')
        center(d, py, y0 + hs * 1.2 + 40, fit(d, py, cfont, 110, inner), '#fde68a')
        if kind == 'repeat':
            center(d, 'Хадгалаад өдөр бүр давтаарай', y0 + hs * 1.2 + 230, cfont(46), '#bfdbfe')
    elif kind == 'meaning':
        hz = min(hs, 260)
        center(d, han, 500, font(hz), 'white'); center(d, py, 500 + hz * 1.2 + 10, fit(d, py, cfont, 90, inner), '#fde68a')
        top, hgt = 960, 400
        d.rounded_rectangle([PAD - 20, top, W - PAD + 20, top + hgt], 50, fill='white')
        f = cfont(88 if len(mn) < 14 else 64); L = wrap(d, mn, f, inner - 40)[:4]
        y = top + (hgt - len(L) * (f.size + 20)) / 2
        for i, l in enumerate(L): center(d, l, y + i * (f.size + 20), f, '#1e3a8a')
    else:  # example
        iw = inner - 40; zh = zh_punct(ex[0])
        n = len(zh); fz = font(96 if n <= 12 else 80 if n <= 18 else 66)
        zl = wrap(d, zh, fz, iw)[:3]
        fp = cfont(46); pl = wrap(d, ex_py, fp, iw)[:3] if ex_py else []
        ft = cfont(58); tl = wrap(d, ex[1], ft, iw)[:4]
        lz, lp, lt = int(fz.size * 1.35), 62, 80
        hgt = 80 + len(zl) * lz + (30 + len(pl) * lp if pl else 0) + 60 + len(tl) * lt
        top = max(SAFE_TOP + 200, 470 + ((SAFE_BOTTOM - 60 - 470) - hgt) / 2)
        card_h = hgt if stage >= 2 else hgt - 60 - len(tl) * lt + 10   # 1-р шатанд орчуулгын зайг авахгүй; 2-р шатанд карт доош тэлнэ
        d.rounded_rectangle([PAD - 20, top, W - PAD + 20, top + card_h], 50, fill='white')
        y = top + 50; i = zh.find(w[0]); hl = (i, i + len(w[0])) if i >= 0 else None; cur = 0
        for l in zl:
            off = zh.find(l, cur); off = cur if off < 0 else off; cur = off + len(l)
            draw_hl(d, l, fz, y, hl, off); y += lz
        for l in pl: center(d, l, y + 20, fp, '#2563eb'); y += lp
        y += 40 if pl else 20
        if stage >= 2:
            d.line([(PAD + 60, y), (W - PAD - 60, y)], fill='#e2e8f0', width=4); y += 30
            for l in tl: center(d, l, y, ft, '#334155'); y += lt
    footer(d); im.save(path)

# Видеоны кодлолт: дундын (scene) файл бараг алдалтгүй, эцсийн файл CRF 22 (текст тод, хэмжээ жижиг).
# Өнгө: PNG (RGB) → YUV хөрвүүлэлтэд bt709 матриц + tag тавина (үгүй бол HD дээр өнгө бүдгэрч/хазайдаг).
BT709 = ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709']
CVF = 'scale=out_color_matrix=bt709:out_range=tv'
# Бүх скриптийн дундын сегментийн нэгдсэн чанар: CRF 16 (текст тод), аудио 256k (дахин кодлоход алдагдахгүй).
VQ = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-profile:v', 'high', '-pix_fmt', 'yuv420p'] + BT709
AQ = ['-c:a', 'aac', '-b:a', '256k', '-ar', '44100']
SCENE_V = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-r', '30'] + BT709
FADE = 'fade=t=in:st=0:d=0.2:color=0x1e3a8a' if os.environ.get('REEL_FADE', '1') != '0' else None   # дэвсгэрийн өнгөөс бүдэгээр гарч ирнэ

def render(kind, lv, w, ex, wavs, gap, tmp, n, stage=2, tail=0.7, fade=True):
    img = os.path.join(tmp, f's{n}.png'); aud = os.path.join(tmp, f's{n}.wav'); mp4 = os.path.join(tmp, f's{n}.mp4')
    scene_img(kind, lv, w, ex, img, stage); join(wavs, gap, aud)
    dur = probe(aud) + tail
    vf = ['-vf', ','.join(x for x in ((FADE if fade else None), CVF) if x)]
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', '30', '-i', img, '-i', aud, '-t', f'{dur:.2f}',
                    '-af', 'apad'] + vf + SCENE_V + ['-c:a', 'aac', '-ar', '44100', '-shortest', mp4], check=True)
    return mp4

def finalize(lst, total, out):
    """Сегментүүдийг нэгтгэж, дээд талд ахицын зурвас нэмээд нэг удаа CRF-ээр кодлоно. Дууг нэг түвшинд (loudnorm) болгоно."""
    bar_w = W - 2 * PAD
    fc = (f"[1:v]scale=w='max(2,2*trunc({bar_w}*t/{total:.2f}/2))':h=10:eval=frame[bar];"
          f"[0:v][bar]overlay=x={PAD}:y=LANE:eval=frame,{CVF},format=yuv420p[v]").replace('LANE', str(SAFE_TOP - 10))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-f', 'lavfi', '-i', f'color=c=0xfacc15:s={bar_w}x10:r=30:d={total + 1:.2f}',
                    '-filter_complex', fc, '-map', '[v]', '-map', '0:a', '-af', LOUDNORM,
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', CRF, '-profile:v', 'high', '-g', '300'] + BT709 + [
                    
                    '-x264-params', 'aq-mode=3', '-r', '30',
                    '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-movflags', '+faststart', '-shortest', out], check=True)

HOOKS = [
    'Энэ үгийг мэдэх үү? 🇨🇳',
    'Өнөөдрийн нэг үг 📚',
    'Хятадаар хэрхэн хэлэх вэ? 🤔',
    'Өдөр бүр 1 үг = жилд 365 үг 💡',
    'HSK шалгалтад таарна 🔥',
    'Үүнийг санаж аваарай 👀',
]
# Instagram одоо 3-5 hashtag-ийг зөвлөдөг; 12 hashtag нь спам шиг харагдаж хүртээмжийг бууруулдаг.
def segment(tmp, name, imgs, wav):
    """imgs: секунд тутамд нэг зураг. Видео = хамгийн багадаа аудиотой тэнцүү."""
    dur = probe(wav); fd = os.path.join(tmp, name); os.makedirs(fd)
    for i, im in enumerate(imgs): os.replace(im, os.path.join(fd, f'f{i:03d}.png'))
    mp4 = os.path.join(tmp, name + '.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '1', '-i', os.path.join(fd, 'f%03d.png'), '-i', wav, '-r', '30', '-t', f'{dur:.2f}',
                    '-vf', f'tpad=stop_mode=clone:stop_duration={dur + 2:.2f},{CVF}'] + VQ + AQ + [mp4], check=True)
    return mp4

TAGS = ['#хятадхэл', '#HSK', '#learnchinese', '#монгол', '#中文']

def make_caption(han, py, mn, lv, ex, ex_py, num, series=''):
    k = (num if num is not None else datetime.date.today().toordinal()) % len(HOOKS)
    lines = [HOOKS[k], '', f'{han}  [{py}]  —  {mn}', f'HSK {lv}' + (f' · Үг №{num}' if num else '')]
    if ex:
        lines += ['', zh_punct(ex[0])] + ([ex_py] if ex_py else []) + [ex[1]]
    lines += ['', '💾 Хадгалаад дараа давтаарай', '📩 Хятад хэл сурч буй найздаа илгээгээрэй', '➕ Өдөр бүр шинэ үг — дагаарай', '']
    if series: lines += [series, '']
    lines += ['🔗 Үнэгүй сурах сайт — профайлын линкээс (bio)', '', ' '.join(TAGS[:2] + [f'#HSK{lv}'] + TAGS[2:])]
    return '\n'.join(lines)

def find_word(words, han):
    for lv, L in words.items():
        for w in L:
            if w[0] == han: return lv, w
    sys.exit('Үг олдсонгүй: ' + han)

def main():
    global EX_PY, BADGE
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-gap', type=int, default=0, help='сүүлийн видеоноос N минут болоогүй бол алгасна')
    ap.add_argument('--level', type=int); ap.add_argument('--word'); ap.add_argument('--silent', action='store_true')
    a = ap.parse_args()
    start_watchdog()
    st = SR.load()
    if SR.too_soon(st, 'word', a.min_gap):
        print('Алгасав: сүүлийн видеоноос', round((time.time() - st['last'].get('word', 0)) / 60), 'минут болсон'); SR.skip_out(); return
    words, gram = load(); seq = ordered(words)
    # Хуучин систем (түвшин, дарааллаар) хэдийг гаргасан бол тэдгээрийг «заасан» гэж нэг удаа тэмдэглэнэ.
    SR.init(st, seq)
    if a.word: lv, w = find_word(words, a.word); num = None
    else:
        needed, _ = SR.split_words(seq, st)
        if a.level: needed = [x for x in needed if x[0] == a.level] or needed
        if not needed:                                      # бүх «хэрэгтэй үг» дууссан → эхнээс нь давтана
            st['done']['word'] = []; needed, _ = SR.split_words(seq, st)
        lv, w = needed[0]; num = SR.num(st, 'word')
    BADGE = ('word', num) if num else None
    han, py, mn = w; print('Үг:', han, py, mn, '(HSK', lv, ')', '#' + str(num) if num else '')
    exs = examples()
    ex = tuple(exs[han]) if han in exs else next(((z, t) for z, t in gram if han in z and z != han), None)
    ex_py = EX_PY = sent_pinyin(ex[0]) if ex else ''
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        c = lambda t, v, r, i: say(t, v, r, tmp, i, a.silent)
        # Эхлээд бүх дууг үүсгээд, алдаа гарвал зураг/видео зурахаас өмнө түргэн зогсоно.
        zs, zn = c(han, ZH_VOICE, '-30%', 1), c(han, ZH_VOICE, '+0%', 2)
        a_mean = c('Утга нь... ' + mn.replace(',', ', ').replace('(', ', ').replace(')', '').strip() + '.', MN_VOICE, MN_RATE, 3)
        a_ex = [c(ex[0], ZH_VOICE, '-25%', 4), c(ex[0], ZH_VOICE, '+0%', 5), c('Орчуулбал... ' + ex[1], MN_VOICE, MN_RATE, 6)] if ex else None
        if TTS_FAIL: sys.exit('Дуу үүсгэж чадсангүй: ' + ', '.join(TTS_FAIL))
        scenes = [render('word', lv, w, ex, [zs, zn], 0.5, tmp, 0)]
        scenes.append(render('meaning', lv, w, ex, [a_mean], 0, tmp, 1))
        if ex:
            # Эхлээд хятад өгүүлбэр (удаан → хэвийн), дараа нь орчуулга гарч ирнэ: дэлгэц дууны дагуу өөрчлөгдөнө.
            scenes.append(render('example', lv, w, ex, a_ex[:2], 0.5, tmp, 2, stage=1, tail=0.4))
            scenes.append(render('example', lv, w, ex, [a_ex[2]], 0, tmp, 4, stage=2, fade=False))
        scenes.append(render('repeat', lv, w, ex, [zn, zs, zn], 0.6, tmp, 3))
        lst = os.path.join(tmp, 'list.txt')
        open(lst, 'w').write(''.join(f"file '{s}'\n" for s in scenes))
        total = sum(probe(s) for s in scenes)
        out = os.path.join(OUT, SR.file_name('word', num) if num else datetime.datetime.now().strftime('reel-manual-%Y%m%d-%H%M%S.mp4'))
        finalize(lst, total, out)
    cap = make_caption(han, py, mn, lv, ex, ex_py, num, SR.series_line({**st, 'level': lv}, 'word', num) if num else '')
    open(out[:-4] + '.txt', 'w', encoding='utf8').write(cap)
    if num and not a.silent or (num and os.environ.get('REEL_TEST_STATE') == '1'):
        SR.finish(st, 'word', 'word', han, lv); SR.save(st)
        keep = sorted(f[:-4] for f in os.listdir(OUT) if f.startswith('reel-') and f.endswith('.mp4') and 'manual' not in f)[:-KEEP]
        for k in keep:
            for ext in ('.mp4', '.txt'):
                try: os.remove(os.path.join(OUT, k + ext))
                except OSError: pass
    print('Бэлэн:', out, round(probe(out), 1), 'сек')
    if TTS_FAIL:
        os.remove(out); os.remove(out[:-4] + '.txt'); sys.exit('Дуу үүсгэж чадсангүй: ' + ', '.join(TTS_FAIL))

if __name__ == '__main__': main()
