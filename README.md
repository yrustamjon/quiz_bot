# Quiz Bot

Uzbek educational assessment platform, under active implementation. **Not yet complete or production-ready.** Full requirements: [master specification](docs/MASTER_PROMPT.md), [frontend requirements](docs/FRONTEND_MASTER_PROMPT.md). Recovery: [implementation progress](IMPLEMENTATION_PROGRESS.md).

Implemented: Django session/CSRF authentication, custom roles, 24-hour temporary teacher credentials and forced password replacement, scoped quiz/question CRUD, publishing/closure/duplication, public/private codes, SQL-backed examination services with frozen question/option snapshots, deadline checks, sequential/free navigation, scoring and result release policies. React connects to the real Django API: authentication, dashboard, quiz draft creation/list/details, question/student directories and profile. There is no mock production data.

Still pending: full quiz wizard and question editor; teacher management UI; XLSX/images import; Aiogram handlers; reports/rankings; complete security/concurrency/accessibility testing. Existing tests do **not** establish all acceptance scenarios.

## Native macOS setup (no Docker)

Requires Python 3.12+, Node 22.12+ and Redis (later bot/background workflows).

```sh
brew install python@3.12 node redis
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.lock
cp .env.example .env
# Set DJANGO_SECRET_KEY in .env to a generated random secret, never commit .env.
python backend/manage.py migrate
python backend/manage.py createcachetable
python backend/manage.py createsuperuser
cd frontend
npm ci
cd ..
```

`createsuperuser` creates a real Django Super Admin; a role string alone grants no superuser privileges. Only Super Admin may create teachers at `/api/teachers/`. Temporary passwords are returned once, expire after 24 hours, are hashed in SQL, and must be replaced before other panel APIs are accessible. No public teacher registration exists.

Run in separate terminals:

```sh
source .venv/bin/activate
python backend/manage.py runserver 127.0.0.1:8001
```

```sh
cd frontend
npm run dev
```

Vite proxies `/api` to Django on port 8001; session cookies and CSRF stay same-origin. Redis: `brew services start redis`. Celery task modules and bot startup are not yet complete; do not treat their configuration as verified startup instructions.

## Validation

```sh
source .venv/bin/activate
pytest -q
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
cd frontend
npm run build
node browser-check.mjs
```

`browser-check.mjs` currently requires `/usr/bin/chromium` and saves screenshots outside the repository at `/workspace/artifacts`. `panel-check.mjs` additionally requires an isolated test identity JSON there; never commit that file. These browser scripts are development checks, not yet a portable full E2E suite.

## Current API

- `/api/auth/{csrf,login,logout,me,change-password}/`
- `/api/teachers/`, teacher detail/PATCH, `reset-password/`, `activate/`, `deactivate/`
- `/api/students/`, student detail; `/api/groups/` Super Admin CRUD
- `/api/quizzes/`, detail/PATCH/DELETE (unused drafts only)
- quiz detail actions: `publish/`, `close/`, `archive/`, `duplicate/`, `regenerate-code/`, `release-results/`, `questions/` GET/PUT
- `/api/questions/` CRUD, protected `/{id}/image/`
- `/api/dashboard/summary/?days=1|7|30|90`

Collections paginate at 25 rows. Teachers' querysets are filtered by ownership. Attempt services are internal Python functions, not public student-control endpoints.

## Examination policy

Server time controls deadlines, including when the application is closed; closing time caps individual duration. Question/options/scoring snapshots stay stable. Sequential mode advances once and refuses stale callbacks. Free mode permits answer replacement with the current revision until completion. Early finish requires confirmation. Unanswered questions score zero, separately from wrong answers. Results obey per-quiz field visibility and release mode. Timestamps store UTC; dashboard dates display in Asia/Tashkent.

SQLite uses IMMEDIATE transactions and a 30-second busy timeout, plus uniqueness constraints. It is suitable only for modest concurrency. PostgreSQL migration requires a supported driver, a new DATABASE_URL, migrations and a rehearsed data migration/constraint validation; re-run concurrency tests on PostgreSQL. This is not a claim of unlimited parallel exam support.

## Deployment and data protection

Use HTTPS, `DJANGO_DEBUG=false`, a strong private key, explicit allowed hosts/CSRF origins, secure cookies and a same-origin reverse proxy. Run `manage.py check --deploy`, configure static serving with `collectstatic`, keep media behind authenticated endpoints, protect Redis on localhost and manage services with launchd/systemd. Full production review remains pending.

Back up SQLite consistently using `sqlite3 backend/db.sqlite3 ".backup 'backup.sqlite3'"` while coordinating writes; separately back up `backend/media`. Restore to a stopped instance, run migrations and verify ownership and file access. Preserve secret environment configuration securely outside distributable backups. Never commit databases, tokens, generated exports or .env files.

## Implemented increment: Excel, reporting and Telegram

The current increment also implements teacher onboarding UI, manual question editor, bank selection/order/removal, quiz settings/result preview, XLSX import dialog, scoped results/rankings, synchronous/queued exports, minimal group creation/deletion, profile updates and Aiogram chat handlers. Detailed coverage and remaining limitations are recorded in IMPLEMENTATION_PROGRESS.md; the earlier pending list describes the initial checkpoint and is superseded here.

### Excel convention and limits

`GET /api/questions/import/template/` returns template version `QUIZ_BOT_TEMPLATE_V1`, with Questions and Instructions sheets. Columns are Question, Option A/B/C/D, Correct Answer (A–D), Points, Image File Name. At most 500 questions, upload 10 MB, total uncompressed archive 40 MB, 1500 members, each image 5 MB / 16 million pixels. Supported raster input: PNG, JPEG, WebP; stored as re-encoded PNG. ZIP contains one XLSX plus relative referenced images. Embedded images must have their top-left anchor in column H on the exact question row, one per row. The pinned openpyxl image-reading adapter necessarily uses private APIs; regression tests cover embedded and ZIP import. Unsupported/ambiguous placement is rejected, never silently omitted. Formulas/external links, traversal, symlinks and duplicate archive names are rejected. Duplicate question rows within one upload are errors. Preview lasts 30 minutes; confirm is atomic and idempotent. Private images require the authenticated question endpoint.

### Additional API

- `PATCH /api/profile/` allows only full name, email, specialty.
- `/api/questions/import/{template,preview,confirm}/`
- `/api/results/`, result detail; `/api/rankings/?quiz=<id>`
- `POST /api/reports/export/` generates XLSX; more than 5000 rows (or `background:true`) queues a job.
- `/api/reports/exports/`, job detail and `/{id}/download/` are owner-scoped. Artifacts expire after seven days.

Rankings choose each student's best final attempt per quiz, order by average percentage descending, elapsed time ascending and student ID ascending, using sequential positions. Telegram rankings omit unreleased/ranking-hidden quizzes and use first names. This average does not normalize difficulty between subjects.

### Redis, worker, scheduler and bot

```sh
brew services start redis
source .venv/bin/activate
PYTHONPATH=backend celery -A config worker --pool=solo --concurrency=1 --loglevel=INFO
# Another terminal:
PYTHONPATH=backend celery -A config beat --schedule /tmp/quiz-bot-beat --loglevel=INFO
# Another terminal, project root:
python -m bot.main
```

Set TELEGRAM_BOT_TOKEN securely before starting the bot. TG_BOT is supported as an existing cloud binding alias. Never place tokens in URLs printed to logs or in Git. The bot respects HTTPS_PROXY when provided; local macOS typically needs no proxy. Redis stores transient registration/code state; SQL stores exam-critical state and deadline. Reconciliation runs every 30 seconds, but synchronous services independently reject late answers.

Bot commands: `/start`, `/menu`, `/help`, `/continue`, `/cancel`. `/cancel` resets only conversational state; active exams and deadlines remain intact. Inline menus support public quizzes, private codes, resume, results, rankings and profile. A real Aiogram getMe and polling startup were verified; **a complete live student exam has not yet been verified**.

### Browser validation

Vitest: `cd frontend && npm test`. Build: `npm run build`. ESLint: `npm exec eslint -- src`. Current lint reports explicit-any typing warnings; no errors at the last completed check. `accessibility-check.mjs` audits real pages with axe; 20 initial route/theme combinations passed with zero automated violations. Newly added groups/settings/quiz dialogs still need expanded audit. Browser integration currently uses isolated runtime accounts in `/workspace/artifacts`; that machinery must be made portable before considering the E2E suite complete. Native cloud Redis was compiled outside the checkout; macOS uses Homebrew.
