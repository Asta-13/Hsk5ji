#!/usr/bin/env python3
"""tools/book-data/ доторх сурах бичгийн үгсээс data/book-words.json үүсгэнэ (HSK үгийн сан дотор 📖 тэмдэгтэй харагддаг).

Ажиллуулах:  python tools/build_book_words.py
- HSK 1-6-д байгаа үгийг оруулахгүй (давхардал үүсгэхгүй).
- Нэг үг хэд хэдэн ном дээр байвал эхний номд л тооцно.
- Шинэ үг нэмэх: tools/book-data/<ном>/lesson-XX.json-д нэмээд дахин ажиллуул.
  Хэсэг бүр: {"words":[{"zh","py","pos_mn","mn","en","note"}]}; ном бүрийн index.json-д lessons жагсаалт, tools/book-data/index.json-д {id,dir,title,title_mn,level} бичигдсэн байна.
"""
import json
from pathlib import Path
from pypinyin import lazy_pinyin, Style

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "book-data"
LV = {"初级": "初", "中级": "中", "高级": "高"}


def main():
    hsk = set()
    for s in json.loads((ROOT / "data" / "hsk-words.json").read_text(encoding="utf8")).values():
        hsk.update(it.split("|")[0].strip() for it in s.split(","))
    cat = json.loads((SRC / "index.json").read_text(encoding="utf8"))["books"]
    seen, out, skipped = set(hsk), [], 0
    for b in cat:
        idx = json.loads((SRC / b["dir"] / "index.json").read_text(encoding="utf8"))
        for l in idx["lessons"]:
            for w in json.loads((SRC / b["dir"] / l["file"]).read_text(encoding="utf8"))["words"]:
                z = w["zh"]
                if z in seen:
                    skipped += 1
                    continue
                seen.add(z)
                py = w["py"] if " " in w["py"] else " ".join(lazy_pinyin(z, style=Style.TONE))
                out.append([z, py, w.get("pos_mn", ""), w["mn"], w["en"], w.get("note", ""), b["title"], LV[b["level"]]])
    (ROOT / "data" / "book-words.json").write_text(json.dumps({"w": out}, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    print("data/book-words.json: %d үг (давхардсан %d алгассан)" % (len(out), skipped))


if __name__ == "__main__":
    main()
