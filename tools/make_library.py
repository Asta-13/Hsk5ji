#!/usr/bin/env python3
"""HF dataset (Byambaa13/Library) доторх PDF-үүдээс data/books/library.json үүсгэнэ.

Хэрэглээ:
  python tools/make_library.py                  # HF API-аас жагсаалтыг татна (интернэт хэрэгтэй)
  python tools/make_library.py --from-list f.tsv   # "файлын нэр<TAB>MB" мөрүүдээс (офлайн)

Шинэ ном HF руу оруулсны дараа энийг дахин ажиллуулаад library.json-г commit хийнэ.
Файлын нэрийн хэлбэр:  "<дугаар>. <初级|中级|高级><综合|口语|听力|读写|阅读|写作> <1|2>_part<N>_<эхний хуудас>-<сүүлийн хуудас>.pdf"
"""
import json, re, sys, urllib.request, urllib.parse
from pathlib import Path

REPO = "Byambaa13/Library"
OUT = Path(__file__).resolve().parent.parent / "data" / "books" / "library.json"
RX = re.compile(r"^(\d+)\.\s*(初级|中级|高级)(综合|口语|听力|读写|阅读|写作)\s*(\d)(?:\(\d+\))?_part(\d+)_(\d+)-(\d+)\.pdf$")

def from_api():
    url = f"https://huggingface.co/api/datasets/{REPO}/tree/main"
    with urllib.request.urlopen(url, timeout=30) as r:
        items = json.load(r)
    return [(i["path"], i.get("size", 0) / 1e6) for i in items if i.get("type") == "file"]

def from_list(p):
    out = []
    for line in Path(p).read_text(encoding="utf-8").splitlines():
        if line.strip():
            n, mb = line.rsplit("\t", 1)
            out.append((n, float(mb)))
    return out

def main():
    files = from_list(sys.argv[sys.argv.index("--from-list") + 1]) if "--from-list" in sys.argv else from_api()
    books, skipped = {}, []
    for name, mb in files:
        m = RX.match(name)
        if not m:
            if name.lower().endswith(".pdf"): skipped.append(name)
            continue
        num, lv, sk, vol, part, a, b = m.groups()
        bk = books.setdefault(int(num), {"n": int(num), "title": f"{lv}{sk} {vol}", "level": lv, "skill": sk, "parts": []})
        bk["parts"].append({"p": int(part), "f": name, "a": int(a), "b": int(b), "mb": round(mb, 1)})
    for bk in books.values():
        bk["parts"].sort(key=lambda x: x["p"])
    data = {
        "base": f"https://huggingface.co/datasets/{REPO}/resolve/main/",
        "books": [books[k] for k in sorted(books)],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(data['books'])} ном, {sum(len(b['parts']) for b in data['books'])} хэсэг → {OUT}")
    for s in skipped: print("  алгасав:", s)

if __name__ == "__main__":
    main()
