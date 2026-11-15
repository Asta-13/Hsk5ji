#!/usr/bin/env python3
"""Workflow-ийн эхэнд (хүнд суулгалт хийхээс өмнө) сүүлийн видеоноос хангалттай хугацаа өнгөрсөн эсэхийг шалгана.
Хэрэглээ: gap_check.py <series.json|state.json> <минут> [төрөл]
  төрөл өгвөл series.json-ийн last[төрөл]-ийг уншина (байхгүй бол хуучин state файлыг).
GITHUB_OUTPUT руу `skip=true|false` бичнэ. state файл байхгүй/эвдэрсэн бол skip=false (шинээр эхэлнэ)."""
import json, os, sys, time

def main():
    path, minutes = sys.argv[1], int(sys.argv[2]); kind = sys.argv[3] if len(sys.argv) > 3 else None
    last = 0.0
    try:
        d = json.load(open(path))
        last = float((d.get('last') or {}).get(kind, 0)) if kind else float(d.get('last', 0))
    except Exception:
        pass
    if kind and not last:                       # series.json хараахан байхгүй → хуучин state файл
        old = {'word': 'state.json', 'grammar': 'grammar-state.json', 'scene': 'scene-state.json', 'tone': 'tone-state.json', 'quiz': 'quiz-state.json'}.get(kind)
        try: last = float(json.load(open(os.path.join(os.path.dirname(path), old))).get('last', 0))
        except Exception: pass
    age = (time.time() - last) / 60
    skip = last > 0 and age < minutes
    print(f"Сүүлийн видеоноос {age:.0f} мин өнгөрсөн (босго {minutes} мин) → {'АЛГАСНА' if skip else 'ҮҮСГЭНЭ'}")
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a') as f:
            f.write(f"skip={'true' if skip else 'false'}\n")

if __name__ == '__main__':
    main()
