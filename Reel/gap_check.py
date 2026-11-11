#!/usr/bin/env python3
"""Workflow-ийн эхэнд (хүнд суулгалт хийхээс өмнө) сүүлийн видеоноос хангалттай хугацаа өнгөрсөн эсэхийг шалгана.
Хэрэглээ: gap_check.py <state.json> <минут>
GITHUB_OUTPUT руу `skip=true|false` бичнэ. state файл байхгүй/эвдэрсэн бол skip=false (шинээр эхэлнэ)."""
import json, os, sys, time

def main():
    path, minutes = sys.argv[1], int(sys.argv[2])
    try:
        last = float(json.load(open(path)).get('last', 0))
    except Exception:
        last = 0.0
    age = (time.time() - last) / 60
    skip = last > 0 and age < minutes
    print(f"Сүүлийн видеоноос {age:.0f} мин өнгөрсөн (босго {minutes} мин) → {'АЛГАСНА' if skip else 'ҮҮСГЭНЭ'}")
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a') as f:
            f.write(f"skip={'true' if skip else 'false'}\n")

if __name__ == '__main__':
    main()
