#!/usr/bin/env python3
"""Нүүр хуудасны PDF номуудаас 生词 (шинэ үг) гаргаж, давхардлыг хасан 初级/中级/高级 гэж ангилна.

Ном нь скан (зураг) тул OCR ашиглана. Гаралт нь Claude-д илгээж Монгол орчуулга + OCR алдаа засуулах
TSV файл. Pinyin-г OCR-аас биш хятад үгнээс pypinyin-ээр шинээр гаргана (OCR-ын pinyin алдаатай).

=== Нэг удаа суулгах (laptop) ===
  1) Python 3.9+      https://www.python.org
  2) Tesseract OCR    Windows: https://github.com/UB-Mannheim/tesseract/wiki  (суулгахдаа
                      "Additional language data" → Chinese (Simplified) + English-ийг тэмдэглэ)
                      macOS:  brew install tesseract tesseract-lang
                      Linux:  sudo apt install tesseract-ocr tesseract-ocr-chi-sim
  3) pip install pymupdf pytesseract pypinyin
     (Windows дээр Tesseract PATH-д байхгүй бол: --tesseract "C:\\Program Files\\Tesseract-OCR\\tesseract.exe")

=== Ажиллуулах (repo-гийн хавтаснаас) ===
  python tools/import_book_words.py --level 初级            # library.json-ийн 初级 бүх ном
  python tools/import_book_words.py --book 1                # зөвхөн 1-р ном (初级综合 1)
  python tools/import_book_words.py --pdf "x.pdf" --name "中级综合 2" --level 中级   # дотоод PDF
  python tools/import_book_words.py --merge-only            # зөвхөн нэгтгэл дахин хийх

Гаралт (tools/book_words/):
  <дугаар>-<ном>.tsv   ном тус бүрийн бүх үг (давхардал тэмдэглэгдсэн)
  ALL_new.tsv          ШИНЭ, давхардалгүй үгс (初级→中级→高级 дарааллаар). ЭНИЙГ Claude-д өг.
  summary.txt          тоо
Хэсэг хэсгээр ажиллуулж болно: OCR/татсан PDF кэшлэгддэг (tools/_pdfs, tools/_ocr), тасарвал үргэлжлүүлнэ.
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDFS = ROOT / "tools" / "_pdfs"
OCRC = ROOT / "tools" / "_ocr"
OUT = ROOT / "tools" / "book_words"
LEVELS = ["初级", "中级", "高级"]
POS = "名动形副助介连代量数叹拟象"
RX_ENTRY = re.compile(r"^\s*(\d{1,3})\s*[.,，。、:：]*\s*([\u4e00-\u9fff]{1,6})\s+(.*)$")
RX_POS = re.compile(r"(?:^|\s)([%s])(?:\s|$)" % POS)
RX_LATIN = re.compile(r"^[A-Za-z0-9\s'’,.;:()/\-–\u00c0-\u024f]+$")
_cfg = {"dpi": 170}


def _pix(pdf, pno, dpi):
    import fitz, io
    from PIL import Image
    doc = fitz.open(pdf)
    pix = doc[pno].get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    return Image.open(io.BytesIO(pix.tobytes("png")))


def ocr_page(args):
    """1-р давхар: chi_sim (хятад үг + POS). Хуудас үгийн хүснэгт шиг бол 2-р давхар: eng (англи тайлбар)."""
    pdf, pno, cache = args
    cf = Path(cache)
    ef = cf.with_suffix(".eng.txt")
    import pytesseract
    img = None
    if cf.exists():
        chi = cf.read_text(encoding="utf8")
    else:
        img = _pix(pdf, pno, _cfg["dpi"])
        chi = pytesseract.image_to_string(img, lang="chi_sim", config="--psm 6")
        cf.parent.mkdir(parents=True, exist_ok=True)
        cf.write_text(chi, encoding="utf8")
    eng = ""
    if ef.exists():
        eng = ef.read_text(encoding="utf8")
    elif sum(1 for ln in chi.splitlines() if RX_ENTRY.match(ln)) >= 3:
        img = img or _pix(pdf, pno, _cfg["dpi"])
        eng = pytesseract.image_to_string(img, lang="eng", config="--psm 6")
        ef.write_text(eng, encoding="utf8")
    return pno, chi, eng


def download(url, dest):
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
            got += len(b)
            if total:
                print("\r   татаж байна %d/%d MB" % (got >> 20, total >> 20), end="", flush=True)
    print()
    tmp.rename(dest)


RX_NUM = re.compile(r"^\s*(\d{1,3})\s*[.,，。、:：]*\s*(.*)$")


def _strip_tone(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if c.isalpha() and ord(c) < 128)


def eng_map(eng):
    """eng-давхрын мөрүүдээс {n: [токенууд]} (хятад үг латин хогоор солигдсон байдаг)."""
    mp, last = {}, None
    for line in eng.splitlines():
        m = RX_NUM.match(line)
        toks = m.group(2).split() if m else []
        if m and len(toks) >= 3 and int(m.group(1)) not in mp:
            mp[int(m.group(1))] = toks
            last = int(m.group(1))
        elif last and RX_LATIN.match(line.strip()) and 0 < len(line.strip()) < 60:
            mp[last] = mp[last] + line.split()  # ээлжлэн дараагийн мөрөнд шилжсэн англи тайлбар
        else:
            last = None
    return mp


def eng_from(toks, zh):
    """Pinyin-тай хамгийн ойр токеныг олж, түүний (POS-ийн) дараах хэсгийг англи тайлбар болгоно."""
    import difflib
    from pypinyin import lazy_pinyin
    want = "".join(lazy_pinyin(zh))
    best, bi = 0.0, -1
    for i, t in enumerate(toks[:4]):
        r = difflib.SequenceMatcher(None, want, _strip_tone(t)).ratio()
        if r > best:
            best, bi = r, i
    if bi < 0 or best < 0.45:
        bi = 1 if len(toks) > 2 else 0
    rest = toks[bi + 1:]
    if rest and len(rest[0]) <= 2 and len(rest) > 1:  # POS багана (хятад тэмдэгт латин хог болсон)
        rest = rest[1:]
    return " ".join(rest).strip()


def parse_pages(texts):
    """texts: [(page_no, chi, eng)] → [{lesson,n,zh,pos,en,page,raw}]"""
    rows, last_n, lesson = [], 0, 0
    for pno, chi, eng in texts:
        em = eng_map(eng) if eng else {}
        page_rows = []
        for line in chi.splitlines():
            m = RX_ENTRY.match(line.rstrip())
            if not m:
                continue
            n, zh, rest = int(m.group(1)), m.group(2), m.group(3).strip()
            parts = re.split(r"\s{2,}", rest)
            if len(parts) < 3 and not RX_POS.search(" " + rest + " "):
                continue
            if not (n == 1 or last_n < n <= last_n + 8):
                continue
            pos = ""
            for t in parts[1:3]:
                t = t.strip()
                if len(t) == 1 and t in POS:
                    pos = t
            if n == 1:
                lesson += 1
            last_n = n
            page_rows.append({"lesson": lesson, "n": n, "zh": zh, "pos": pos,
                              "en": eng_from(em[n], zh) if n in em else "", "page": pno + 1, "raw": rest})
        # хуудас хоорондын сүүлийн мөр: eng хуудсанд n давхцаагүй бол хоосон үлдээнэ
        rows.extend(page_rows)
    return rows


def process_pdfs(pdfs, workers):
    """Нэг номын бүх хэсгийг (PDF жагсаалт) OCR хийж, мөрүүдийг нэгтгэн буцаана."""
    texts = []
    for pdf in pdfs:
        import fitz
        n = len(fitz.open(pdf))
        cdir = OCRC / Path(pdf).stem
        jobs = [(str(pdf), i, str(cdir / ("%04d.txt" % i))) for i in range(n)]
        print("   OCR: %s (%d хуудас)" % (Path(pdf).name, n), flush=True)
        with Pool(workers) as p:
            done = 0
            res = []
            for r in p.imap(ocr_page, jobs, chunksize=2):
                res.append(r)
                done += 1
                if done % 20 == 0:
                    print("\r   %d/%d" % (done, n), end="", flush=True)
        print()
        texts.extend(sorted(res, key=lambda r: r[0]))
    return parse_pages(texts)


def load_known():
    """Давхардлыг тооцох: HSK 1-6 болон repo-д орчуулагдсан номын үгс."""
    known = {}
    p = ROOT / "data" / "hsk-words.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf8"))
        for lv, s in d.items():
            for it in s.split(","):
                w = it.split("|")[0].strip()
                if w:
                    known.setdefault(w, "HSK" + str(lv))
    for f in (ROOT / "data" / "books").glob("*/lesson-*.json"):
        try:
            for w in json.loads(f.read_text(encoding="utf8")).get("words", []):
                known.setdefault(w["zh"], "book:" + f.parent.name)
        except Exception:
            pass
    return known


def write_book_tsv(name, level, bno, rows, known):
    from pypinyin import pinyin, Style
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / ("%s-%s.tsv" % (str(bno).zfill(2), re.sub(r"\s+", "", name)))
    seen = set()
    with open(f, "w", encoding="utf8") as o:
        o.write("level\tbook\tlesson\tn\tzh\tpy\tpos\ten\tpage\tstatus\traw_ocr\n")
        for r in rows:
            py = " ".join(x[0] for x in pinyin(r["zh"], style=Style.TONE))
            if r["zh"] in known:
                st = "dup:" + known[r["zh"]]
            elif r["zh"] in seen:
                st = "dup:same-book"
            else:
                st = "new"
            seen.add(r["zh"])
            o.write("\t".join([level, name, str(r["lesson"]), str(r["n"]), r["zh"], py, r["pos"],
                               r["en"].replace("\t", " "), str(r["page"]), st, r["raw"].replace("\t", " ")]) + "\n")
    return f


def merge_all():
    """Бүх ном-TSV → ALL_new.tsv (初级→中级→高级, ном бүрээр, давхардалгүй)."""
    files = sorted(OUT.glob("[0-9]*.tsv"))
    recs = []
    for f in files:
        lines = f.read_text(encoding="utf8").splitlines()[1:]
        for ln in lines:
            c = ln.split("\t")
            if len(c) >= 10:
                recs.append(c)
    recs.sort(key=lambda c: (LEVELS.index(c[0]) if c[0] in LEVELS else 9, c[1], int(c[2] or 0), int(c[3] or 0)))
    seen, out, dup = {}, [], 0
    for c in recs:
        if not c[9] == "new":  # HSK/өмнөх ном/ижил номд давхцсан
            dup += 1
            continue
        if c[4] in seen:
            dup += 1
            seen[c[4]][2] += "; " + c[1]
            continue
        c = c[:]
        seen[c[4]] = [c, None, c[1]]
        out.append(c)
    with open(OUT / "ALL_new.tsv", "w", encoding="utf8") as o:
        o.write("level\tbook\tlesson\tn\tzh\tpy\tpos\ten\tpage\talso_in\n")
        for c in out:
            o.write("\t".join(c[:9] + [seen[c[4]][2].replace(c[1], "", 1).strip("; ")]) + "\n")
    by = {}
    for c in out:
        by[c[0]] = by.get(c[0], 0) + 1
    s = "Нийт мөр: %d | давхардсан/хасагдсан: %d | ШИНЭ: %d\n%s\n" % (
        len(recs), dup, len(out), "\n".join("%s: %d" % (k, by.get(k, 0)) for k in LEVELS))
    (OUT / "summary.txt").write_text(s, encoding="utf8")
    print(s)
    print("→", OUT / "ALL_new.tsv", "(энийг Claude-д өг)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", choices=LEVELS)
    ap.add_argument("--book", type=int, help="library.json дахь ном n")
    ap.add_argument("--pdf", help="дотоод PDF (таслалтай олныг зааж болно)")
    ap.add_argument("--name", default="local")
    ap.add_argument("--dpi", type=int, default=170)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--tesseract")
    ap.add_argument("--merge-only", action="store_true")
    a = ap.parse_args()
    _cfg["dpi"] = a.dpi
    if a.tesseract:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = a.tesseract
    if a.merge_only:
        merge_all()
        return
    known = load_known()
    jobs = []  # (level, name, bno, [pdf paths])
    if a.pdf:
        jobs.append((a.level or "中级", a.name, 0, [p.strip() for p in a.pdf.split(",")]))
    else:
        lib = json.loads((ROOT / "data" / "books" / "library.json").read_text(encoding="utf8"))
        for b in lib["books"]:
            if a.book and b["n"] != a.book:
                continue
            if a.level and b["level"] != a.level:
                continue
            paths = []
            for p in b["parts"]:
                dest = PDFS / p["f"]
                print("[%s] %s — хэсэг %d" % (b["n"], b["title"], p["p"]))
                download(lib["base"] + urllib.parse.quote(p["f"]), dest)
                paths.append(str(dest))
            jobs.append((b["level"], b["title"], b["n"], paths))
    if not jobs:
        sys.exit("Ном олдсонгүй (--level / --book / --pdf шалга).")
    for level, name, bno, paths in jobs:
        print("=== %s %s ===" % (level, name))
        rows = process_pdfs(paths, a.workers)
        f = write_book_tsv(name, level, bno, rows, known)
        print("   %d үг → %s" % (len(rows), f.name))
    merge_all()


if __name__ == "__main__":
    main()
