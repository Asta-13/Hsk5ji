"""media/ дахь mp3/mp4 файлуудаас хятад хадмал (цагтай) автоматаар гаргана → data/media-auto.json.
Whisper (faster-whisper, CPU) ашиглана. Нэг удаа боловсруулсан файлыг дахин хийхгүй (нэр+хэмжээгээр таниж кэшлэнэ)."""
import json, os, re, sys, glob, hashlib, difflib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXT = ('.mp4', '.mp3', '.m4a', '.wav', '.ogg', '.webm')
OUT = os.path.join(ROOT, 'data', 'media-auto.json')
MODEL = os.environ.get('WHISPER_MODEL', 'small')

def hsk_dict():
    raw = json.load(open(os.path.join(ROOT, 'data', 'hsk-words.json'), encoding='utf8'))
    d = {}
    for lv, s in raw.items():
        for it in s.split(','):
            w = it.split('|')[0]
            d.setdefault(w, int(lv))
    return d

def segment(text, D):
    out, i = [], 0
    while i < len(text):
        for n in range(min(6, len(text) - i), 0, -1):
            if text[i:i + n] in D:
                out.append(text[i:i + n]); i += n; break
        else:
            i += 1
    return out

def guess_level(lines, D):
    lv = sorted(D[w] for ln in lines for w in segment(ln['zh'], D))
    return lv[int(len(lv) * 0.85)] if lv else 3

HAN = re.compile(r'[^\u4e00-\u9fff]')

def read_lyrics(txt):
    """media/<нэр>.txt: мөр бүр `中文` эсвэл `中文 | монгол`. Хоосон мөр, # тайлбар алгасна."""
    rows = []
    for r in open(txt, encoding='utf8').read().splitlines():
        r = r.strip()
        if not r or r.startswith('#'): continue
        p = [x.strip() for x in r.split('|', 1)]
        if HAN.sub('', p[0]): rows.append({'zh': p[0], 'mn': p[1] if len(p) > 1 else ''})
    return rows

def align(lyrics, chars):
    """lyrics: [{'zh',..}], chars: [(char, start_sec)] (Whisper-ийн таньсан текст). Дууны үгийн мөр бүрт эхлэх цаг ононо."""
    A, owner = [], []
    for i, ln in enumerate(lyrics):
        for c in HAN.sub('', ln['zh']): A.append(c); owner.append(i)
    B = [c for c, _ in chars]
    first = {}
    if A and B:
        for blk in difflib.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks():
            for k in range(blk.size):
                first.setdefault(owner[blk.a + k], chars[blk.b + k][1])
    ts = [first.get(i) for i in range(len(lyrics))]
    for i, t in enumerate(ts):                       # олдоогүй мөрийг хөрш мөрүүдийн хооронд тэгшилнэ
        if t is None:
            lo = next((j for j in range(i - 1, -1, -1) if ts[j] is not None), None)
            hi = next((j for j in range(i + 1, len(ts)) if ts[j] is not None), None)
            if lo is not None and hi is not None: ts[i] = ts[lo] + (ts[hi] - ts[lo]) * (i - lo) / (hi - lo)
            elif lo is not None: ts[i] = ts[lo] + 3
            elif hi is not None: ts[i] = max(0, ts[hi] - 3 * (hi - i))
            else: ts[i] = 0
    for i in range(1, len(ts)): ts[i] = max(ts[i], ts[i - 1])   # цаг буурахгүй
    return [dict(ln, t=round(t, 1)) for ln, t in zip(lyrics, ts)]

def split_seg(text, t0, t1):
    """Урт өгүүлбэрийг цэг таслалаар богино хадмал болгож, цагийг үсгийн тоогоор хуваана (TikTok маягийн богино хадмал)."""
    parts = [p for p in re.split(r'(?<=[。，！？；,.!?;])', text) if HAN.sub('', p)]
    tot = sum(len(HAN.sub('', p)) for p in parts) or 1
    out, t = [], t0
    for p in parts:
        d = (t1 - t0) * len(HAN.sub('', p)) / tot
        out.append({'t': round(t, 1), 'e': round(t + d, 1), 'zh': p.strip('，, ')}); t += d
    return out

def main():
    files = sorted(f for f in glob.glob(os.path.join(ROOT, 'media', '*')) if f.lower().endswith(EXT))
    old = {}
    if os.path.exists(OUT):
        for it in json.load(open(OUT, encoding='utf8')).get('items', []): old[it['id']] = it
    todo = []
    for f in files:
        rel = 'media/' + os.path.basename(f)
        txt = os.path.splitext(f)[0] + '.txt'
        sig = str(os.path.getsize(f)) + ('_' + hashlib.sha1(open(txt, 'rb').read()).hexdigest()[:6] if os.path.exists(txt) else '')
        fid = 'a_' + re.sub(r'\W+', '-', os.path.splitext(os.path.basename(f))[0]).strip('-').lower() + '_' + sig
        todo.append((f, rel, fid))
    keep = {fid for _, _, fid in todo}
    items = {k: v for k, v in old.items() if k in keep}      # устгасан файлын хадмал автоматаар арилна
    need = [t for t in todo if t[2] not in items]
    if not need:
        print('Шинэ файл алга.'); json.dump({'items': list(items.values())}, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=1); return
    from faster_whisper import WhisperModel
    try:
        from opencc import OpenCC; t2s = OpenCC('t2s').convert
    except Exception:
        t2s = lambda s: s
    D = hsk_dict()
    model = WhisperModel(MODEL, device='cpu', compute_type='int8')
    for f, rel, fid in need:
        print('Хадмал:', rel, flush=True)
        txt = os.path.splitext(f)[0] + '.txt'
        lyr = read_lyrics(txt) if os.path.exists(txt) else None
        def run(vad):
            segs, _ = model.transcribe(f, language='zh', vad_filter=vad, beam_size=5, word_timestamps=bool(lyr),
                                       condition_on_previous_text=False,
                                       initial_prompt='以下是普通话的句子，使用简体中文。')
            lines, chars = [], []
            for s_ in segs:
                z = t2s(s_.text.strip())
                if z and re.search(r'[\u4e00-\u9fff]', z): lines += split_seg(z, s_.start, s_.end)
                for w in (s_.words or []):
                    cs = HAN.sub('', t2s(w.word))
                    for k, c in enumerate(cs): chars.append((c, w.start + (w.end - w.start) * k / max(1, len(cs))))
            return lines, chars
        lines, chars = run(not lyr)
        if not lines and not lyr:
            # Дуу/хөгжимтэй файлд VAD бүх дууг «чимээ» гэж тасалдаг → VAD-гүйгээр дахин оролдоно
            print('  хоосон гарлаа — VAD-гүйгээр дахин оролдож байна', flush=True)
            lines, chars = run(False)
        if lyr:
            lines = align(lyr, chars)
            print('  дууны үгийг цагт тааруулав: %d мөр' % len(lines), flush=True)
        auto = 0 if lyr else 1
        if not lines:
            # Урьд нь энд `continue` хийж файлыг сайтаас бүр алгасдаг байсан. Одоо хадмалгүй ч тоглуулагчтай нэмнэ.
            print('  хадмал олдсонгүй — хадмалгүй (зөвхөн тоглуулагч) нэмлээ. Дууны үгийг media/<нэр>.txt-д бичвэл цагт тааруулна.', flush=True)
            auto = 2
        title = os.path.splitext(os.path.basename(f))[0].replace('_', ' ').replace('-', ' ')
        items[fid] = {'id': fid, 'kind': 'song' if f.lower().endswith(('.mp3', '.m4a', '.wav', '.ogg')) else 'video',
                      'level': guess_level(lines, D), 'title': title, 'titleZh': '', 'srcType': 'file', 'src': rel, 'auto': auto, 'lines': lines}
        print('  %d мөр, HSK ~%d' % (len(lines), items[fid]['level']), flush=True)
    json.dump({'items': list(items.values())}, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
