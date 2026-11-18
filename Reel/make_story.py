"""Богино (40-60 сек) анимэйшн түүх/боловсролын видео: stories/<id>.json → mp4 (+ цагтай хадмалын JSON).
HTML/JS анимэйшнийг Chromium-оор кадр кадраар авч ffmpeg-ээр кодлоно.
  python make_story.py stories/qin-unify.json --out OUT [--burn] [--tts] [--seconds N]
--burn : хадмалыг видеон дээр шатаана (урьдчилан харах). Апп дотор хадмал давхарга тусдаа тул үйлдвэрлэлд хэрэггүй.
--tts  : Microsoft дуу (edge-tts) нэмнэ; үгүй бол чимээгүй, урт нь тооцоолсон."""
import argparse, json, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FPS, W, H = 30, 1080, 1920
HAN = re.compile(r'[一-鿿]')

def pinyin(zh):
    from pypinyin import pinyin as pp, Style
    return ' '.join(x[0] for x in pp(''.join(c for c in zh if HAN.search(c)), style=Style.TONE))

def timeline(story, durs):
    t, lines, scenes = 0.6, [], []
    for i, ln in enumerate(story['lines']):
        d = durs[i]
        lines.append({'t': round(t, 2), 'e': round(t + d, 2), 'zh': ln['zh'], 'mn': ln['mn'], 'py': pinyin(ln['zh']), 'scene': ln['scene']})
        sc = scenes[-1] if scenes and scenes[-1]['id'] == ln['scene'] else None
        if sc: sc['end'] = t + d + 0.5
        else: scenes.append({'id': ln['scene'], 'start': t - 0.3 if scenes else 0.0, 'end': t + d + 0.5})
        t += d + 0.5
    for a, b in zip(scenes, scenes[1:]): a['end'] = b['start'] = (a['end'] + b['start']) / 2
    total = t
    if story.get('words'):
        scenes.append({'id': '__outro', 'start': scenes[-1]['end'], 'end': scenes[-1]['end'] + 5.5}); total = scenes[-1]['end'] + 0.3
    return {'lines': lines, 'scenes': scenes}, total

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('story'); ap.add_argument('--out', default='.'); ap.add_argument('--burn', action='store_true')
    ap.add_argument('--tts', action='store_true'); ap.add_argument('--seconds', type=float, default=0); ap.add_argument('--crf', default='17'); a = ap.parse_args()
    story = json.load(open(a.story, encoding='utf8')); os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='story_')
    durs, audio = [], None
    if a.tts:
        import make_reel as M
        wavs = [M.say(l['zh'], M.ZH_VOICE, '-8%', tmp, i, False) for i, l in enumerate(story['lines'])]
        if M.TTS_FAIL: sys.exit('Дуу үүсгэж чадсангүй: ' + ', '.join(M.TTS_FAIL))
        durs = [M.probe(w) + 0.15 for w in wavs]
    else:
        durs = [max(2.6, 0.30 * len(HAN.findall(l['zh'])) + 1.1) for l in story['lines']]
    tl, total = timeline(story, durs)
    if a.tts:                                    # дууг мөр бүрийн эхлэх цагт нь тавина
        import make_reel as M
        parts, cur = [], 0.0
        for i, w in enumerate(wavs):
            gap = tl['lines'][i]['t'] - cur
            g = os.path.join(tmp, f'g{i}.wav'); M.silence(g, max(0.01, gap)); parts += [g, w]; cur = tl['lines'][i]['t'] + M.probe(w)
        audio = os.path.join(tmp, 'voice.wav'); M.join(parts, 0, audio)
    html = open(os.path.join(HERE, 'stories', 'template.html'), encoding='utf8').read()
    html = html.replace('__STORY__', json.dumps(story, ensure_ascii=False)).replace('__BURN__', 'true' if a.burn else 'false')
    html = html.replace('__TIMELINE__', json.dumps(tl, ensure_ascii=False)).replace('__TOTAL__', f'{total:.2f}')
    hp = os.path.join(tmp, 'story.html'); open(hp, 'w', encoding='utf8').write(html)
    if a.seconds: total = min(total, a.seconds)
    n = int(total * FPS)
    out = os.path.join(a.out, story['id'] + ('-burn' if a.burn else '') + '.mp4'); part = out + '.part.mp4'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-']
    if audio: cmd += ['-i', audio]
    cmd += ['-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', a.crf, '-profile:v', 'high',
            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-r', str(FPS)]
    cmd += (['-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-shortest'] if audio else ['-an']) + ['-movflags', '+faststart', part]
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(viewport={'width': W, 'height': H}); pg.goto('file://' + hp); pg.wait_for_timeout(400)
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            pg.evaluate(f'render({i / FPS:.4f})')
            ff.stdin.write(pg.screenshot(type='jpeg', quality=93))
            if i % 150 == 0: print(f'  {i}/{n}', flush=True)
        ff.stdin.close(); rc = ff.wait(); br.close()
    if rc != 0: sys.exit('ffmpeg алдаа')
    os.replace(part, out)
    item = {'id': 'st_' + story['id'], 'kind': 'video', 'level': story['level'], 'title': story['title_mn'], 'titleZh': story['title_zh'], 'srcType': 'file',
            'src': 'video/' + story['id'] + '.mp4', 'story': 1, 'lines': [{'t': l['t'], 'e': l['e'], 'zh': l['zh'], 'mn': l['mn']} for l in tl['lines']]}
    json.dump(item, open(os.path.join(a.out, story['id'] + '.item.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('Бэлэн:', out, f'{total:.1f} сек')

if __name__ == '__main__':
    main()
