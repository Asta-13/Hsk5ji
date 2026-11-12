#!/usr/bin/env python3
"""`reels` салбарын файлуудыг өдөр өдрөөр нь хавтаслана.

  organize.py legacy <reels-out>
      Үндсэн хавтаст байгаа хуучин reel-*/scene-* файлуудыг days/legacy/ руу зөөнө (нэг удаа; дараа нь юу ч үлдэхгүй).
  organize.py daily <reels-out> [--keep-days 3]
      Шинээр үүссэн reel-*/scene-* файлуудыг days/YYYY-MM-DD/ (Улаанбаатарын өдөр) руу зөөж,
      тэр өдрийн days/YYYY-MM-DD.zip-ийг шинээр үүсгэнэ. keep-days-аас хуучин өдрийн хавтас+zip-ийг устгана.
"""
import argparse, datetime, os, re, shutil, sys, zipfile
from zoneinfo import ZoneInfo

PAT = re.compile(r'^(reel|scene)-.+\.(mp4|txt)$')
DAY = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def root_files(out):
    return sorted(f for f in os.listdir(out) if PAT.match(f) and os.path.isfile(os.path.join(out, f)))

def move_all(out, dest):
    fs = root_files(out)
    if fs: os.makedirs(dest, exist_ok=True)
    for f in fs: shutil.move(os.path.join(out, f), os.path.join(dest, f))
    return len(fs)

def make_zip(day_dir):
    zp = day_dir + '.zip'
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_STORED) as z:     # mp4 аль хэдийн шахагдсан тул STORED
        for f in sorted(os.listdir(day_dir)):
            z.write(os.path.join(day_dir, f), os.path.join(os.path.basename(day_dir), f))
    return zp

def prune(days, today, keep):
    oldest = today - datetime.timedelta(days=keep - 1)
    gone = []
    for name in os.listdir(days):
        stem = name[:-4] if name.endswith('.zip') else name
        if not DAY.match(stem): continue                        # legacy/ болон бусдыг хөндөхгүй
        if datetime.date.fromisoformat(stem) < oldest:
            p = os.path.join(days, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
            gone.append(name)
    return gone

def write_index(out):
    """reels салбарын үндсэн хуудсанд харагдах README.md: хамгийн шинэ видеог дээр нь, холбоостой жагсаана
    (утаснаас GitHub нээгээд шууд дарж үзэх/татахад зориулав)."""
    days = os.path.join(out, 'days')
    if not os.path.isdir(days): return
    L = ['# Reels', '', 'Видеог дарж үзээд, **Download** (↓) хийж хадгална. Доорх caption-ыг нээж хуулна.', '']
    for day in sorted((x for x in os.listdir(days) if DAY.match(x) and os.path.isdir(os.path.join(days, x))), reverse=True):
        dd = os.path.join(days, day)
        vids = sorted((f for f in os.listdir(dd) if f.endswith('.mp4')), key=lambda f: os.path.getmtime(os.path.join(dd, f)), reverse=True)
        L += [f'## {day}', '']
        if os.path.exists(dd + '.zip'): L += [f'📦 [Өдрийн бүх видео (zip)](days/{day}.zip)', '']
        for f in vids:
            txt = os.path.join(dd, f[:-4] + '.txt'); first = ''
            if os.path.exists(txt): first = open(txt, encoding='utf8').read().strip().split('\n')[0][:90]
            L.append(f'- 🎬 [{f}](days/{day}/{f}) — {first}' + (f' · [caption](days/{day}/{f[:-4]}.txt)' if os.path.exists(txt) else ''))
        L.append('')
    open(os.path.join(out, 'README.md'), 'w', encoding='utf8').write('\n'.join(L) + '\n')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['legacy', 'daily']); ap.add_argument('out')
    ap.add_argument('--keep-days', type=int, default=3)
    a = ap.parse_args()
    days = os.path.join(a.out, 'days')
    if a.mode == 'legacy':
        print('legacy руу зөөсөн:', move_all(a.out, os.path.join(days, 'legacy')))
        return
    today = datetime.datetime.now(ZoneInfo('Asia/Ulaanbaatar')).date()
    d = os.path.join(days, today.isoformat())
    n = move_all(a.out, d)
    if os.path.isdir(d):
        print(f'{today}: +{n} файл → {make_zip(d)}')
    print('устгасан хуучин өдөр:', prune(days, today, a.keep_days) if os.path.isdir(days) else [])
    write_index(a.out)

if __name__ == '__main__':
    main()
