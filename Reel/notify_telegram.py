#!/usr/bin/env python3
"""Шинээр үүссэн reel/scene видеог Telegram-аар (видео + хуулах caption) илгээнэ.
  notify_telegram.py <reels-out>
TELEGRAM_TOKEN, TELEGRAM_CHAT_ID (GitHub Secrets) байхгүй бол юу ч хийлгүй амжилттай дуусна.
Илгээж чадахгүй бол ч workflow-г унагахгүй (видео өөрөө репод хадгалагдана)."""
import json, os, re, sys, time, uuid, urllib.request, urllib.error

API = os.environ.get('TELEGRAM_API', 'https://api.telegram.org')
TOKEN, CHAT = os.environ.get('TELEGRAM_TOKEN', '').strip(), os.environ.get('TELEGRAM_CHAT_ID', '').strip()
PAT = re.compile(r'^(reel|scene|quiz)-.+\.mp4$')

def call(method, fields, file=None, tries=3):
    for n in range(tries):
        b = uuid.uuid4().hex; body = b''
        for k, v in fields.items():
            body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        if file:
            name, data = file
            body += (f'--{b}\r\nContent-Disposition: form-data; name="video"; filename="{name}"\r\n'
                     f'Content-Type: video/mp4\r\n\r\n').encode() + data + b'\r\n'
        body += f'--{b}--\r\n'.encode()
        req = urllib.request.Request(f'{API}/bot{TOKEN}/{method}', body, {'Content-Type': f'multipart/form-data; boundary={b}'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode('utf8', 'replace')[:200].replace(TOKEN, '***')
            print(f'Telegram {method} HTTP {e.code}: {msg}')
            if e.code in (400, 401, 403, 404): return None      # дахин оролдсон ч нэмэргүй
        except Exception as e:
            print(f'Telegram {method} алдаа: {type(e).__name__}')
        time.sleep(3 * (n + 1))
    return None

def main():
    if not TOKEN or not CHAT:
        print('TELEGRAM_TOKEN/TELEGRAM_CHAT_ID тохируулаагүй → алгасав'); return
    out = sys.argv[1]
    for f in sorted(x for x in os.listdir(out) if PAT.match(x)):
        path = os.path.join(out, f); txt = path[:-4] + '.txt'
        cap = open(txt, encoding='utf8').read().strip() if os.path.exists(txt) else f
        if os.path.getsize(path) > 49 * 1024 * 1024: print(f, 'хэт том (>50MB), алгасав'); continue
        r = call('sendVideo', {'chat_id': CHAT, 'caption': f[:-4] + '\n' + cap.split('\n')[0][:200], 'supports_streaming': 'true'},
                 (f, open(path, 'rb').read()))
        if r and r.get('ok'):
            call('sendMessage', {'chat_id': CHAT, 'text': cap[:4000]})
            print('Telegram руу илгээв:', f)
        else: print('Telegram руу илгээж чадсангүй:', f)

if __name__ == '__main__':
    try: main()
    except Exception as e: print('notify алдаа:', type(e).__name__)
