#!/usr/bin/env python3
"""Сурах бичгүүдийн 综合注释 / 语言点 / 语法 хэсгийг OCR-оор түүж, дүрмийн жагсаалт гаргана.

import_book_words.py-тай ижил OCR кэш (tools/_ocr, tools/_pdfs)-ийг ашигладаг тул үг гаргасан номуудыг дахин OCR хийхгүй.
Гаралт: tools/book_grammar/ALL_grammar.txt  ← ЭНИЙГ Claude-д өгвөл data/grammar.json руу
(түвшин|хэв маяг|монгол утга|жишээ|жишээний орчуулга) хэлбэрээр цэвэрлэн нэмнэ.

Суулгах/тохиргоо нь import_book_words.py-тай ижил (Tesseract + chi_sim, pip install pymupdf pytesseract pypinyin).
  python tools/import_book_grammar.py --level 中级          # library.json-ийн 中级 бүх ном
  python tools/import_book_grammar.py --book 12             # нэг ном
  python tools/import_book_grammar.py --pdf "x.pdf" --name "中级综合 2"
"""
import argparse, json, os, re, sys, urllib.parse
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_book_words as ib  # OCR, татах, Tesseract тохируулгын туслахууд

OUT = ib.ROOT / "tools" / "book_grammar"
MARK = re.compile(r"综合注释|语言点|语法|注释")
RX_EX = re.compile(r"试\s*一\s*试|练习")


def pages_text(pdfs, workers):
    out = []  # (pdf нэр, хуудас, текст)
    for pdf in pdfs:
        n = len(ib._fitz().open(pdf))
        cdir = ib.OCRC / Path(pdf).stem
        jobs = [(str(pdf), i, str(cdir / ("%04d.txt" % i))) for i in range(n)]
        print("   OCR: %s (%d хуудас)" % (Path(pdf).name, n), flush=True)
        with Pool(workers, initializer=ib._init_worker, initargs=(ib._cfg["dpi"], ib._cfg.get("tess"))) as p:
            for r in p.imap(ib.ocr_page, jobs, chunksize=2):
                out.append((Path(pdf).stem, r[0] + 1, r[1]))
    return out


def grammar_blocks(pages):
    """Тэмдэгтэй хуудас + үргэлжлэл (жишээтэй) хуудсыг авч, дасгалын («试一试») хэсгийг хасна."""
    res, prev = [], False
    for stem, pno, t in pages:
        has = bool(MARK.search(t))
        if has or (prev and "例如" in t):
            i = MARK.search(t)
            body = t[i.start():] if i else t
            body = re.sub(r"\n.{0,3}试\s*一\s*试.*?(?=\n\s*\d{1,2}\s*[.．]|\Z)", "\n", body, flags=re.S)
            res.append("### %s · хуудас %d\n%s" % (stem, pno, ib.RX_CJKGAP.sub("", body).strip()))
        prev = has
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", choices=ib.LEVELS)
    ap.add_argument("--book", type=int)
    ap.add_argument("--pdf")
    ap.add_argument("--name", default="local")
    ap.add_argument("--dpi", type=int, default=170)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--tesseract")
    a = ap.parse_args()
    ib._cfg["dpi"], ib._cfg["tess"] = a.dpi, a.tesseract
    if not ib._setup_tess(a.tesseract):
        sys.exit("Tesseract олдсонгүй (--tesseract зам заа).")
    jobs = []
    if a.pdf:
        jobs.append((a.name, [p.strip() for p in a.pdf.split(",")]))
    else:
        lib = json.loads((ib.ROOT / "data" / "books" / "library.json").read_text(encoding="utf8"))
        for b in lib["books"]:
            if (a.book and b["n"] != a.book) or (a.level and b["level"] != a.level) or not b.get("parts"):
                continue
            paths = []
            for p in b["parts"]:
                dest = ib.PDFS / p["f"]
                print("[%s] %s — хэсэг %d" % (b["n"], b["title"], p["p"]))
                ib.download(lib["base"] + urllib.parse.quote(p["f"]), dest)
                paths.append(str(dest))
            jobs.append((b["title"], paths))
    if not jobs:
        sys.exit("Ном олдсонгүй (--level / --book / --pdf шалга).")
    OUT.mkdir(parents=True, exist_ok=True)
    allb = []
    for name, paths in jobs:
        blocks = grammar_blocks(pages_text(paths, a.workers))
        (OUT / (re.sub(r"\W+", "_", name) + ".txt")).write_text("\n\n".join(blocks), encoding="utf8")
        allb.append("######## %s ########\n%s" % (name, "\n\n".join(blocks)))
        print("   %s: %d хуудас" % (name, len(blocks)))
    (OUT / "ALL_grammar.txt").write_text("\n\n".join(allb), encoding="utf8")
    print("Бэлэн: %s — энэ файлыг Claude-д өг." % (OUT / "ALL_grammar.txt"))


if __name__ == "__main__":
    main()
