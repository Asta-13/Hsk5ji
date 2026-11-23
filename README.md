# HSK 5жи — HSK шалгалтын бэлтгэлийн сайт

GitHub Pages + Supabase дээр ажилладаг PWA (vanilla JS).

## Бүтэц
| Зам | Юу вэ |
|---|---|
| `index.html`, `css/`, `js/` | Сайтын код (`js/app.js` үндсэн, `js/loader.js` өгөгдөл ачаалдаг) |
| `sw.js` | Service worker. Файл өөрчлөх бүртээ `VER`-ийг нэмэгдүүл |
| `data/hsk-words.json` | HSK 1-6 үгс; `hsk-mongolian.json`, `hsk-translations.json` орчуулга |
| `data/book-words.json` | Сурах бичгийн нэмэлт 1836 үг (初/中/高) — **гараар засахгүй**, доорх скриптээр үүснэ |
| `data/books/library.json` | PDF номын сан (Hugging Face `Byambaa13/Library`) |
| `tools/` | Туслах скриптүүд (сайтад ачаалагдахгүй) |
| `Reel/`, `media/`, `video/`, `.github/workflows/` | Instagram bot, медиа, автомат ажлууд |

## tools/
- `import_book_words.py` — ном (PDF)-оос OCR-ээр шинэ үг гаргана (laptop дээр; Tesseract хэрэгтэй).
- `book-data/` — гаргасан үгсийн эх сурвалж (ном/хэсэг бүрээр JSON). Орчуулга засах бол энд.
- `build_book_words.py` — `book-data/` → `data/book-words.json` (HSK-д байгааг давхарлахгүй).
  `python tools/build_book_words.py`
- `source-pdfs/` — OCR-д ашигласан эх PDF-үүд.
- `make_library.py`, `merge_examples.py` (+ `ex_batch*.txt`) — номын сан, жишээ өгүүлбэр нэгтгэх.

## Үг засах/нэмэх урсгал
1. `tools/book-data/<ном>/lesson-XX.json` засна
2. `python tools/build_book_words.py`
3. `sw.js` дахь `VER` нэмээд commit/push

## Хувилбар · Холбоо барих
Today доод талын «Холбоо барих · Хувилбар» карт. Админ нэвтэрсэн үед тэнд шууд имэйл, хувилбар, тайлбарыг засна (Supabase `site` хүснэгт, id=`about`).
Код дахь анхны утга: `APP_VER`, `CONTACT_MAIL` (app.js). Шинэчлэлт гаргахад `sw.js`-ийн `VER`-ийг нэмнэ.
> Баталгаажуулах захидлыг илгээгч (Supabase Auth) нь Supabase → Authentication → SMTP Settings дээр тохирно (код биш).

## Номын сан
PDF-үүд Hugging Face дээр. Сайт дотор `js/vendor/pdf.min.js` (PDF.js)-ээр хуудас хуудсаар нь унших; алдаа гарвал iframe руу буцна.
