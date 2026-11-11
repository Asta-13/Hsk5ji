# Reel бот

GitHub Actions өдөрт олон удаа HSK видео (reel) үүсгэж `reels` салбарт хадгална.

- **Daily reel** — HSK үг тус бүрийн видео (удаан → хэвийн дуудлага → монгол тайлбар → жишээ → давталт).
- **Daily scene** — 40 богино харилцан яриа (амьд ярианы хэв маяг, дүрүүд ярихад ам нь дуутай хамт хөдөлнө).

## Файлууд хаана байх вэ
`reels` салбар → `days/ӨӨӨӨ-СС-ӨӨ/` (Улаанбаатарын өдөр) дотор тухайн өдрийн бүх видео + `.txt` тайлбар,
мөн `days/ӨӨӨӨ-СС-ӨӨ.zip` нэг дор татахад зориулсан. Сүүлийн 3 өдрийг үлдээнэ. Хуучин файлууд `days/legacy/` дотор.

## Найдвартай ажиллуулах (schedule)
GitHub-ийн `schedule` үргэлж ажилладаггүй (ихэнхийг алгасдаг). Тогтвортой болгохын тулд cron-job.org-оор гаднаас дуудна:
1. GitHub → Settings → Developer settings → Fine-grained token: зөвхөн энэ репо, **Actions: Read and write**.
2. cron-job.org → шинэ job, 15 минут тутамд, `POST https://api.github.com/repos/Asta-13/Hsk5ji/actions/workflows/daily-reel.yml/dispatches`
   Header: `Authorization: Bearer <TOKEN>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`
   Body: `{"ref":"main","inputs":{"auto":"true"}}`
3. Scene-д мөн адил `daily-scene.yml`-ээр өөр job (3 цаг тутам).
`auto=true` үед хоорондын хугацаа (reel 50 мин, scene 230 мин) хүрээгүй бол ажил өөрөө алгасна.

## Алдаа гарвал
Actions → улаан run → улаан алхамын лог. Дуу үүсгэх алхам 3 удаа дахин оролддог; гацвал 10 минутын дараа
хаана гацсаныг лог руу хэвлээд зогсоно.
