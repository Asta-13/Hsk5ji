# Түүх / боловсролын богино видео (40-60 сек)

Видео бүр нэг JSON: `Reel/stories/<id>.json`
- `lines`: хятад мөр + монгол орчуулга + аль `scene`-д хамаарах
- `scenes`: `merge` (нэгдэх блок), `title` (гарчиг), `icons` (4 карт), `timeline` (тоо + цагийн шугам)
- `words`: төгсгөлийн «Өнөөдөр сурсан үг» (5 үг)

Шинэ сэдэв нэмэх = шинэ JSON файл хийж main руу push хийх. `Daily story video` workflow өдөр бүр 1-ийг
дуутайгаар үүсгэж `video/` болон `data/stories.json`-д бүртгэнэ; апп-ын 🔥 Лент-д автоматаар гарна.

Гараар: `python Reel/render_stories.py --max 5 --tts`   (эсвэл Actions → Daily story video → Run workflow, max=5)
Туршилт: `python Reel/make_story.py Reel/stories/keju.json --out /tmp/o --burn` (дуугүй, хадмал шатаасан)
