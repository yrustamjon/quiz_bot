# Quiz Bot — amalga oshirish va tekshiruv hisoboti

2026-11-18 (Asia/Tashkent). Telegram UX, runtime va input-hardening source checkpoint **465a5b2** main branchga push qilindi, remote SHA tasdiqlandi. 22 ta screenshot Telegram orqali yuborilgani tasdiqlandi.

Asos: [MASTER_PROMPT](MASTER_PROMPT.md) va [FRONTEND_MASTER_PROMPT](FRONTEND_MASTER_PROMPT.md). Qayta davom ettirish holati: [IMPLEMENTATION_PROGRESS](../IMPLEMENTATION_PROGRESS.md).

## A. Amalga oshirilgan funksiyalar

Django, React va Aiogram bir xil haqiqiy SQL ma’lumotlari va imtihon servislariga bog‘langan. Rollar, xavfsiz o‘qituvchi onboarding, test/savol boshqaruvi, uch bosqichli wizard, XLSX/ZIP/Excel ichidagi rasmlar importi, Telegram imtihonlari, muddat va tiklash, natijalar, reyting, guruhlar va to‘rt turdagi hisobotlar mavjud. Oddiy ishga tushirish sun’iy ma’lumot yaratmaydi.

## B. Fayllar

Asosiy kataloglar: `backend/apps/{accounts,quizzes,questions,attempts,reports}`, `backend/config`, `backend/tests`, `bot/{handlers,keyboards}`, `frontend/src/{pages,components,services,layouts}`, `scripts`, `.github/workflows`. Batafsil arxitektura va buyruqlar [README](../README.md)da. Amaldagi commit tarkibi Git orqali ko‘riladi; maxfiy `.env`, SQLite, media, screenshot va brauzer test parollari Gitga kiritilmaydi.

## C. Ma’lumotlar bazasi

Maxsus User, StudentProfile, Group, AuditLog, RateLimitBucket; Quiz/QuizAccessCode; Question/QuizQuestion/ImportSession; Attempt/AttemptQuestion/AttemptAnswer; ReportExport modellari mavjud. Migratsiyalar yangi ajratilgan bazada bajarildi va amaldagi bazaga qo‘llangan. Migratsiya tafovuti tekshiruvi toza.

SQL snapshot savollar, variant tartibi, to‘g‘ri javob, ball va rasm manzilini saqlaydi. Unique/check cheklovlar takroriy faol urinish va javoblarni himoyalaydi. SQLite IMMEDIATE tranzaksiyalari va 30 soniyali kutish ishlatiladi. PostgreSQL o‘tishi konfiguratsiya/dokumentatsiyada ko‘rsatilgan; PostgreSQLda tekshiruv hali o‘tkazilmagan.

## D. API

Session + CSRF bilan haqiqiy `/api/` endpointlar: auth/profile, teachers, students/groups, quizzes/lifecycle/access-code/questions, questions/images/import, results/rankings/dashboard, reports/export/jobs/download. Sahifalash 25 yozuv. Sana, ball, o‘qituvchi, test va o‘quvchi filtrlari mavjud. O‘qituvchi ma’lumotlari SQL darajasida egasi bilan cheklanadi. Barcha API javoblari private/no-store.

Endpoint va ishga tushirish tafsilotlari [README API jadvali](../README.md#api-overview)da.

## E. UI

Yangilangan navy/indigo dizayn, Light/Dark, dastlabki tizim mavzusi, 7 ekran kengligi, guruhlangan navigatsiya, mobil menyu, account dropdown, klaviatura bilan ishlaydigan Radix dialoglar, loading/empty/error holatlari, Uzbek validatsiya, haqiqiy import preview jadvali va rasmlar, hisobot navbati/yuklash mavjud.

Dashboard asosiy amallar, ixcham ko‘rsatkichlar, haqiqiy kunlik faollik va so‘nggi test/natijalarni ko‘rsatadi. Grafik alohida yuklanadi; holat kartalari test filtriga olib boradi. Mavzu almashganda tugma kontrasti saqlanadi. Testlar jadvalida bog‘liq ma’lumotlar birlashtirilgan, uch bosqichli wizard va natija sozlamalari aniqroq ko‘rinadi.

Wizard tahrirlarni bosqichlar orasida saqlaydi; saqlanmagan sozlama bilan nashr qilish bloklanadi. Muhim formalarda havola va brauzer Back/Forward navigatsiyasi tasdiqlash orqali boshqariladi, tabni yopish uchun brauzer himoyasi ishlaydi. O‘chirish/cheklash kabi amallar tasdiqlanadi. Rasm bilan savol yaratish bitta API so‘roviga birlashtirilgan, yaroqsiz rasm alohida bo‘sh savol yaratmaydi.

## F. Telegram

Ro‘yxatdan o‘tish, ochiq/yopiq testlar, kodni tekshirish, imtihon boshlash, ketma-ket/erkin javoblash, davom ettirish, erta yakunlash tasdig‘i, natijalar, profil va reyting implementatsiya qilingan. Qolgan vaqt serverdan olinadi va bot/Redis qayta ishga tushsa uzaymaydi. Callback shaxs, urinish, variant, revision va muddat bilan tekshiriladi.

Haqiqiy Telegram API ulanishi, polling va screenshot yuborish tekshirildi. Bot handler testlari haqiqiy SQL servislarini, test Telegram transportini ishlatadi. **Haqiqiy odam Telegramda ro‘yxatdan o‘tib imtihonni tugatgani hali tasdiqlanmagan.** Bot tokeni yoki chat identifikatori bu hisobotda yo‘q.

Telegram UX qayta tartiblandi: «Test tanlash» asosiy amal, barcha 6 bo‘lim saqlangan. Ro‘yxatda 4 tadan test, nomi yozilgan tanlash tugmalari, foydalanuvchining qolgan/ruxsat etilgan urinishlari va mavjudlik holati ko‘rsatiladi. Bitta xabar ichida sahifalash, bir natijali tarix, savol/javob progressi va native rangli boshqaruvlar ishlaydi. Matnlar tabiiy Uzbekcha sarlavhalar bilan qisqartirildi; kirish shartlari va yakunlash tasdig‘i ajratildi. To‘g‘ri koddan keyin input holati yopiladi, kod Start amali uchun saqlanadi. Xato kod faqat shu suhbatdagi bot promptini yangilaydi; boshqa suhbat yoki o‘quvchi xabari tahrirlanmaydi. /help amaliy yo‘riqnoma beradi. Bir xil tez bosishlar takroriy edit yubormaydi. Rasm file-ID orqali qayta ishlatiladi, eski ID rad etilsa asl rasm qayta yuklanadi. Eski/o‘chirilgan xabarda xavfsiz fallback bor. API cheklovi sabab juda uzun yoki photo-to-text holatlarida alohida davomiy xabar kerak bo‘lishi mumkin.

Foydalanuvchi rasmlar lokal muhitdan ekanini aniqlashtirdi. Bir token bilan ikki poller ishlamasligi uchun cloud sinov polleri xavfsiz to‘xtatildi; screenshot yuborish imkoniyati saqlanadi. Yangi kod lokalda pull/restart qilingach ko‘rinadi; lokal real javob tezligi hali o‘lchanmagan. @QuizBot ichki suhbat ekranlari bu muhitda tekshirilmagan.

## G. Xavfsizlik

Noto‘g‘ri top-level JSON (array/null/scalar) 500 o‘rniga 400 bilan rad etiladi. SQL savol tahriri/nashr va resume/expiration race sinovlari o‘tdi. Ishlayotgan worker joriy kodni yuklagani startup fingerprint va real task roundtrip orqali tekshiriladi.

CSRF, role/object ownership, vaqtinchalik parol muddati va qayta ishlatish cheklovi, Django parol hashlash, SQL throttling, private media va export, server muddati, stale/manipulated callback, Decimal hisoblash, formula-safe XLSX ishlatiladi.

Import traversal/absolute/symlink/nested/encrypted/ambiguous archive yo‘llari, ZIP hajmi, XML DTD/entity, formula/external content, noto‘g‘ri rasm/anchor va umumiy yuk hajmini tekshiradi. Rasmlar cheklangan raster sifatida qayta kodlanadi, metadata olib tashlanadi. React matnni JSX orqali chiqaradi, untrusted HTML render qilinmaydi.

DRF/Pillow audit topilmalari yangilash orqali bartaraf etildi. Pinned Python lock va npm production auditida hozircha 0 ma’lum zaiflik. **To‘liq npm auditi o‘tmadi:** picomatch <=4.0.7 ReDoS (CVE-2026-112366 / GHSA-fc5q-39xc-vjpf) build/test dependency zanjirida 14 high entry sifatida qayd etilgan. Registry latest 4.0.7; rasmiy advisory fixed release ko‘rsatmagan. To‘liq audit CI gate sifatida saqlandi; zaiflik yashirilmadi. Bu mustaqil penetration test o‘rnini bosmaydi.

## H. Tekshiruv va acceptance xaritasi

- Backend: **81 pytest passed**; concurrency, ruxsat, autentifikatsiya, parser/raster, muddat, callback, reyting va hisobot tekshiruvlari bilan.
- Frontend: **15 Vitest passed**; strict TypeScript build va ESLint zero warnings.
- Django `check`, `check --deploy`, `makemigrations --check --dry-run`: muammosiz. `pip check`: muammosiz.
- Haqiqiy Redis FSM write/reconnect/read/cleanup: o‘tdi; faqat ajratilgan kalitlar ishlatilgan.
- Alohida Celery worker + ajratilgan SQL/media bilan background XLSX navbati, tayyor statusi va authenticated download brauzerda tekshirildi.
- Yangi dizayndan keyingi kengaytirilgan axe tekshiruvi: **50 sahifa/oyna/holat/mavzu kombinatsiyasi, 0 violation**. Oxirgi router/form o‘zgarishidan keyingi integration/management/axe rerunlari ham o‘tdi.

| Ssenariy | Dalil va holat |
|---|---|
| A — Teacher onboarding | Real Chromium: admin yaratishi → bir martalik parol → majburiy almashtirish → panel, o‘tdi |
| B — Begona ma’lumot | API retrieval/edit/export/image/job ownership negative testlari, o‘tdi |
| C — Quiz yaratish | Real API/wizard/import/publish, o‘tdi; jonli Telegram tanlash hali kerak |
| D — XLSX | Template → preview → confirm → savollar, real brauzer/API, o‘tdi |
| E — ZIP rasm | Parser/real SQL/image handler testlari, o‘tdi; jonli Telegram rasmli exam hali kerak |
| F — Embedded rasm | Qator/anchor/content mapping va noto‘g‘ri anchor regressiyalari, o‘tdi |
| G — Public exam | Aiogram callback → real SQL → natija integratsiyasi, o‘tdi; inson bilan jonli bosqich kutilmoqda |
| H — Private quiz | Kod validation/expiry/rotation/ownership/handler testlari va kod oynasi brauzerda, o‘tdi |
| I — Sequential | Old callback va takroriy javob rad etilishi, o‘tdi |
| J — Free | Navigatsiya va javob almashtirish/revision testlari, o‘tdi |
| K — Uzilish/tiklash | SQL resume/snapshot va Redis reconnect, o‘tdi; real Telegram client/bot restart safari hali kerak |
| L — Timeout | Deadline chegarasi/kech javob/reconcile va parallel finish race, o‘tdi |
| M — Early finish | Confirm/cancel va idempotent finish integratsiyasi, o‘tdi |
| N — Natija maxfiyligi | Release/flags/detailed answers va reyting orqali hidden-percentage sizmasligi, o‘tdi |
| O — Rankings | Best attempt/average/time tie/student-ID tartibi va scope testlari, o‘tdi |
| P — XLSX report | To‘rt real hisobot, scope va background download, o‘tdi |
| Q — Security | Auth/CSRF/ID/callback/code/archive/raster/size negative tests, o‘tdi |
| R — UI quality | Yangi dizayn: Light/Dark, 7 width, klaviatura, CRUD/import/export va axe, o‘tdi; router Back/link tasdiqlash va bekor qilish ham tekshirildi |

Test dalillari `/workspace/artifacts` va `/workspace/artifacts/e2e`da; ular manba kodiga qo‘shilmagan. Screenshotlarda alohida test bazasi ma’lumotlari ishlatilgan.

## I. Cheklovlar va tashqi to‘siqlar

Dizaynning foydalanuvchiga yoqishi avtomatik test bilan tasdiqlanmaydi; yangi ko‘rinish rasmlari ko‘rib chiqish uchun yuborilgan. Lokal Telegram oynasiga bu muhitdan kirish imkoni yo‘q.

Jonli inson Telegram imtihoni yakunlanmaguncha barcha acceptance ssenariylari to‘liq yopilgan deb hisoblanmaydi. Bot foydalanuvchi tugmalarini inson nomidan bosa olmaydi.

Upstream picomatch xavfsiz relizi chiqmaguncha to‘liq npm audit qizil qoladi; bu yakuniy xavfsizlik acceptance uchun tashqi to‘siq.

Remote GitHub CI natijasi hali kuzatilmagan. macOS yo‘riqnomasi bor, amaldagi native tekshiruv Linux/Chromiumda o‘tdi. Yuqori trafik/PostgreSQL load testi va ishlab chiqarish infratuzilmasiga deployment bajarilmagan. SQLite katta trafik uchun cheksiz masshtablash kafolati emas.

openpyxl embedded image o‘qish adapteri hujjatlashtirilgan private APIga tayanadi; lock va regressiya testlari sabab dependency yangilanganda qayta tekshirish kerak. Export 100000 kirish qatori bilan cheklangan. Brauzerning tab-close matnini brauzerning o‘zi belgilaydi.

## J. Ishga tushirish

[README native macOS](../README.md#native-macos-installation) yo‘riqnomasi: Python virtualenv, lock install, maxfiy env, migrate, createsuperuser, native Redis, Django, Celery worker, Beat, Aiogram va Vite alohida jarayonlarda. Docker kerak emas. Ishlayotgan `.env`ni qayta yozmang.

Qayta tekshirish: `.venv/bin/pytest -q`, `npm run build`, `npm run lint`, `npm test`, `.venv/bin/python scripts/browser_suite.py`. Suite boshqa DB/media, random parol va unique queue ishlatadi; haqiqiy foydalanuvchi bazasi tozalanmaydi.

## K. Keyingi tavsiyalar

Avval picomatch rasmiy tuzatilgan relizini kuzatish va full npm auditni tozalash, haqiqiy Telegram foydalanuvchisi bilan public/private/image/resume safari va remote CI natijasini tasdiqlash. Ishlab chiqarishdan oldin HTTPS/reverse proxy, Redis himoyasi, process supervision va backup/restore mashqini o‘tkazish. Trafik oshganda alohida PostgreSQL bazasida constraint/concurrency/scoping testlarini qayta bajarib, nazoratli ko‘chirish.
