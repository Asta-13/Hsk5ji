"""stories/*.json дундаас хараахан хийгдээгүй түүхийг (video/<id>.mp4 байхгүй) хамгийн ихдээ N ширхэг үүсгэж, data/stories.json-д бүртгэнэ.
  python Reel/render_stories.py --max 1 --tts
Өдөр бүр 1-ийг гаргавал апп дахь Лент өдөр бүр шинэжинэ."""
import argparse, glob, json, os, subprocess, sys, shutil, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ap = argparse.ArgumentParser(); ap.add_argument('--max', type=int, default=1); ap.add_argument('--tts', action='store_true'); ap.add_argument('--crf', default='22'); ap.add_argument('--ig-out', default=''); a = ap.parse_args()
os.makedirs(os.path.join(ROOT, 'video'), exist_ok=True)
reg_path = os.path.join(ROOT, 'data', 'stories.json')
reg = json.load(open(reg_path, encoding='utf8')) if os.path.exists(reg_path) else {'items': []}
done = {x['id'] for x in reg['items']}
files = sorted(glob.glob(os.path.join(ROOT, 'Reel', 'stories', '*.json')), key=lambda f: (json.load(open(f, encoding='utf8')).get('order', 999), f))
n = 0
for f in files:
    sid = json.load(open(f, encoding='utf8'))['id']
    if 'st_' + sid in done and os.path.exists(os.path.join(ROOT, 'video', sid + '.mp4')): continue
    if n >= a.max: break
    tmp = tempfile.mkdtemp(prefix='stout_')
    cmd = [sys.executable, os.path.join(ROOT, 'Reel', 'make_story.py'), f, '--out', tmp, '--crf', a.crf] + (['--tts'] if a.tts else [])
    subprocess.run(cmd, check=True)
    shutil.copy(os.path.join(tmp, sid + '.mp4'), os.path.join(ROOT, 'video', sid + '.mp4'))
    item = json.load(open(os.path.join(tmp, sid + '.item.json'), encoding='utf8'))
    reg['items'] = [x for x in reg['items'] if x['id'] != item['id']] + [item]; n += 1
    if a.ig_out:                                 # Instagram-д нийтлэх хуулбар + тайлбар (post_instagram.py)
        st = json.load(open(f, encoding='utf8')); os.makedirs(a.ig_out, exist_ok=True)
        shutil.copy(os.path.join(tmp, sid + '.mp4'), os.path.join(a.ig_out, f'story-{sid}.mp4'))
        body = '\n'.join(f"{l['zh']}\n{l['mn']}" for l in item['lines'][:5])
        cap = (f"🎬 {st['title_mn']} — {st['title_zh']}\n🎓 HSK {st['level']}\n\n{body}\n\n💾 Хадгалаад дараа дахин үзээрэй ❤️ Найздаа илгээгээрэй\n"
               f"👉 Үнэгүй сурах сайт: asta-13.github.io/Hsk5ji\n\n#хятадхэл #HSK{st['level']} #түүх #learnchinese #монгол #中文 #hanzilaoshi")
        open(os.path.join(a.ig_out, f'story-{sid}.txt'), 'w', encoding='utf8').write(cap)
    print('Нэмлээ:', sid, flush=True)
json.dump(reg, open(reg_path, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('Шинэ түүх:', n)
