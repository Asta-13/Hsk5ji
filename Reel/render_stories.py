"""stories/*.json дундаас хараахан хийгдээгүй түүхийг (video/<id>.mp4 байхгүй) хамгийн ихдээ N ширхэг үүсгэж, data/stories.json-д бүртгэнэ.
  python Reel/render_stories.py --max 1 --tts
Өдөр бүр 1-ийг гаргавал апп дахь Лент өдөр бүр шинэжинэ."""
import argparse, glob, json, os, subprocess, sys, shutil, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ap = argparse.ArgumentParser(); ap.add_argument('--max', type=int, default=1); ap.add_argument('--tts', action='store_true'); ap.add_argument('--crf', default='22'); a = ap.parse_args()
os.makedirs(os.path.join(ROOT, 'video'), exist_ok=True)
reg_path = os.path.join(ROOT, 'data', 'stories.json')
reg = json.load(open(reg_path, encoding='utf8')) if os.path.exists(reg_path) else {'items': []}
done = {x['id'] for x in reg['items']}
files = sorted(glob.glob(os.path.join(ROOT, 'Reel', 'stories', '*.json')))
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
    print('Нэмлээ:', sid, flush=True)
json.dump(reg, open(reg_path, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('Шинэ түүх:', n)
