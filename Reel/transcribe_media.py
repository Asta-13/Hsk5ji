"""media/ дахь mp3/mp4 файлуудаас хятад хадмал (цагтай) автоматаар гаргана → data/media-auto.json.
Whisper (faster-whisper, CPU) ашиглана. Нэг удаа боловсруулсан файлыг дахин хийхгүй (нэр+хэмжээгээр таниж кэшлэнэ)."""
import json, os, re, sys, glob
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

def main():
    files = sorted(f for f in glob.glob(os.path.join(ROOT, 'media', '*')) if f.lower().endswith(EXT))
    old = {}
    if os.path.exists(OUT):
        for it in json.load(open(OUT, encoding='utf8')).get('items', []): old[it['id']] = it
    todo = []
    for f in files:
        rel = 'media/' + os.path.basename(f)
        fid = 'a_' + re.sub(r'\W+', '-', os.path.splitext(os.path.basename(f))[0]).strip('-').lower() + '_' + str(os.path.getsize(f))
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
        segs, info = model.transcribe(f, language='zh', vad_filter=True, beam_size=5, initial_prompt='以下是普通话的句子，使用简体中文。')
        lines = []
        for s in segs:
            z = t2s(s.text.strip())
            if z and re.search(r'[一-鿿]', z): lines.append({'t': int(s.start), 'zh': z})
        if not lines:
            print('  хоосон — алгаслаа'); continue
        title = os.path.splitext(os.path.basename(f))[0].replace('_', ' ').replace('-', ' ')
        items[fid] = {'id': fid, 'kind': 'song' if f.lower().endswith(('.mp3', '.m4a', '.wav', '.ogg')) else 'video',
                      'level': guess_level(lines, D), 'title': title, 'titleZh': '', 'srcType': 'file', 'src': rel, 'auto': 1, 'lines': lines}
        print('  %d мөр, HSK ~%d' % (len(lines), items[fid]['level']), flush=True)
    json.dump({'items': list(items.values())}, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
