#!/usr/bin/env python3
"""Шинээр үүссэн видеог Instagram Reels руу автоматаар нийтэлнэ (Instagram Graph API, resumable upload).
  post_instagram.py <хавтас> [--dry-run]
Хавтас дахь words5-*.mp4 / grammar-*.mp4 / scene-*.mp4 / story-*.mp4 бүрийг, ижил нэртэй .txt-ийг тайлбар болгон нийтэлнэ.

GitHub Secrets (Settings → Secrets and variables → Actions):
  IG_ACCESS_TOKEN  — Instagram access token (instagram_business_content_publish эрхтэй)
  IG_USER_ID       — Instagram professional account-ийн ID
Аль нэг нь байхгүй бол юу ч хийлгүй амжилттай дуусна. Нийтэлсэн файлыг <хавтас>/ig-posted.json-д тэмдэглэж, дахин нийтлэхгүй.
Token нь `IG…`-ээр эхэлбэл graph.instagram.com, бусад (`EAA…`) бол graph.facebook.com ашиглана (IG_GRAPH_HOST-оор дарж болно)."""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

TOKEN = os.environ.get('IG_ACCESS_TOKEN', '').strip()
USER = os.environ.get('IG_USER_ID', '').strip()
VER = os.environ.get('IG_API_VERSION', 'v21.0')
HOST = os.environ.get('IG_GRAPH_HOST') or ('graph.instagram.com' if TOKEN.startswith('IG') else 'graph.facebook.com')
PAT = re.compile(r'^(words5|grammar|scene|story)-.+\.mp4$')
MAX_CAPTION, MAX_TAGS = 2200, 30


def req(method, url, data=None, headers=None, tries=3, timeout=300):
    """JSON буцаана. 5xx/сүлжээний алдаанд дахин оролдоно; 4xx бол алдааны текстийг (token нууцлан) шууд шиднэ."""
    last = None
    for n in range(tries):
        r = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(r, timeout=timeout) as resp: return json.load(resp)
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf8', 'replace').replace(TOKEN, '***')[:600]
            last = f'HTTP {e.code}: {body}'
            if e.code < 500: raise RuntimeError(last)
        except Exception as e:
            last = f'{type(e).__name__}: {str(e).replace(TOKEN, "***")[:200]}'
        time.sleep(5 * (n + 1))
    raise RuntimeError(last)


def form(**kw): return urllib.parse.urlencode(kw).encode()


def clean_caption(text):
    text = text.strip()
    tags = re.findall(r'#\w+', text)
    if len(tags) > MAX_TAGS:                       # Instagram 30-аас олон hashtag-д алдаа өгдөг
        keep = set(tags[:MAX_TAGS]); seen = 0
        def sub(m):
            nonlocal seen
            if m.group(0) in keep and seen < MAX_TAGS: seen += 1; return m.group(0)
            return ''
        text = re.sub(r'#\w+', sub, text)
    return text[:MAX_CAPTION]


def post(path, caption):
    base = f'https://{HOST}/{VER}'
    size = os.path.getsize(path)
    c = req('POST', f'{base}/{USER}/media', form(media_type='REELS', upload_type='resumable', caption=caption, share_to_feed='true', access_token=TOKEN))
    cid, uri = c['id'], c['uri']
    with open(path, 'rb') as f: blob = f.read()
    u = req('POST', uri, blob, {'Authorization': f'OAuth {TOKEN}', 'offset': '0', 'file_size': str(size), 'Content-Type': 'application/octet-stream'})
    if not u.get('success', True): raise RuntimeError(f'upload амжилтгүй: {u}')
    for _ in range(60):                            # ~10 минут хүртэл Instagram видеог боловсруулахыг хүлээнэ
        s = req('GET', f'{base}/{cid}?' + urllib.parse.urlencode({'fields': 'status_code,status', 'access_token': TOKEN}))
        code = s.get('status_code')
        if code == 'FINISHED': break
        if code in ('ERROR', 'EXPIRED'): raise RuntimeError(f'Instagram боловсруулалтын алдаа: {s}')
        time.sleep(10)
    else:
        raise RuntimeError('Instagram боловсруулалт хугацаандаа дууссангүй')
    m = req('POST', f'{base}/{USER}/media_publish', form(creation_id=cid, access_token=TOKEN))
    return m['id']


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    if not args: sys.exit(__doc__)
    out = args[0]
    if not dry and (not TOKEN or not USER):
        print('IG_ACCESS_TOKEN/IG_USER_ID тохируулаагүй → Instagram руу нийтлэхийг алгасав'); return
    logp = os.path.join(out, 'ig-posted.json')
    try: log = json.load(open(logp, encoding='utf8'))
    except Exception: log = {}
    bad = 0
    for f in sorted(x for x in os.listdir(out) if PAT.match(x)):
        if f in log: print(f, '— аль хэдийн нийтэлсэн, алгасав'); continue
        path = os.path.join(out, f); txt = path[:-4] + '.txt'
        cap = clean_caption(open(txt, encoding='utf8').read() if os.path.exists(txt) else f[:-4])
        if dry: print(f'[dry-run] {f} ({os.path.getsize(path) // 1024} KB), caption {len(cap)} тэмдэгт'); continue
        try:
            mid = post(path, cap); log[f] = {'id': mid, 't': int(time.time())}
            json.dump(log, open(logp, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
            print('Instagram руу нийтэллээ:', f, '→', mid)
        except Exception as e:
            bad += 1; print(f'::error::Instagram руу нийтэлж чадсангүй ({f}): {e}')
    if bad: sys.exit(1)


if __name__ == '__main__': main()
