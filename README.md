# Quiz Bot

Uzbek-language quiz administration and Telegram examination platform. Django and Aiogram call the same examination services; React uses the real session-authenticated Django API. No Docker or production mock data.

**Implementation is under validation, not certified production-ready.** See [implementation report and acceptance evidence](docs/IMPLEMENTATION_REPORT.md), [progress and outstanding checks](IMPLEMENTATION_PROGRESS.md), [functional specification](docs/MASTER_PROMPT.md) and [frontend specification](docs/FRONTEND_MASTER_PROMPT.md). A live human Telegram exam and an upstream build/test dependency advisory (picomatch ReDoS, no fixed published release at verification) remain outstanding; getMe/polling is not an end-to-end exam test.

## Architecture and stack

- Python 3.12+, Django 5.2 LTS, DRF 3.18, SQLite initially.
- React 19, TypeScript, Vite, Tailwind 4, shadcn-style components with Radix Dialog/Dropdown, TanStack Query, React Router, React Hook Form/Zod, Recharts, Lucide and Sonner.
- Aiogram 3, Redis FSM, Celery worker and Beat.
- openpyxl XLSX processing, Pillow 13 raster normalization.
- Pytest/Django, Vitest/Testing Library, Playwright Chromium and axe.

```text
backend/
  config/           settings, WSGI, Celery, bounded uploads, API errors
  apps/accounts/    User, StudentProfile, Group, AuditLog, RateLimitBucket
  apps/quizzes/     quiz lifecycle/access code services and API
  apps/questions/   question bank, safe images, staged spreadsheet imports
  apps/attempts/    SQL snapshots/answers/deadlines/scoring and reconciliation
  apps/reports/     scoped results/rankings/XLSX jobs and retention
  tests/
frontend/src/
  components/       UI primitives, forms, import flow, theme, notifications
  layouts/          responsive sidebar/header and protected shell
  pages/            authentication, dashboard, management and reporting
  services/         session/CSRF client, identity context and labels
bot/                main entry, handlers, keyboards, trusted Django services
scripts/            isolated browser-suite orchestration and opt-in fixtures
```

Roles are exactly SUPER_ADMIN, TEACHER and STUDENT. Telegram students have a separate unique Telegram-ID identity model; Telegram usernames are optional display data. A SUPER_ADMIN role string alone grants no Django superuser rights. Teachers' queries are scoped in SQL, including student summaries, nested questions, reports and protected images. Group membership never widens teacher permissions.

## Native macOS installation

```sh
brew install python@3.12 node redis
# Node 22.12+; Node 24 is suitable.
git clone https://github.com/yrustamjon/quiz_bot.git
cd quiz_bot
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.lock
cp .env.example .env
python -c 'import secrets; print(secrets.token_urlsafe(48))'
# Put the generated value into DJANGO_SECRET_KEY in .env.
python backend/manage.py migrate
python backend/manage.py createsuperuser
cd frontend
npm ci
cd ..
brew services start redis
```

Use an existing isolated checkout when one is already provided; do not create another Git repository or worktree for normal cloud tasks. Never overwrite an existing `.env`. Python requirements and npm lockfiles are committed; runtime databases, media, secrets and generated builds are ignored.

### Environment settings

`.env.example` contains names and safe defaults. Django rejects a missing or shorter-than-32-character secret. `DJANGO_DEBUG=false` is the default when unset; local development explicitly sets it true.

| Variable | Meaning |
|---|---|
| DJANGO_SECRET_KEY | Private random Django signing key |
| DJANGO_DEBUG | `true` only for local development |
| DJANGO_ALLOWED_HOSTS | Explicit comma-separated hostnames |
| DATABASE_URL | Unset: backend/db.sqlite3; PostgreSQL URL supported by config |
| REDIS_URL | Bot transient state; default redis://127.0.0.1:6379/0 |
| CELERY_BROKER_URL | Worker broker; defaults to REDIS_URL |
| CELERY_RESULT_BACKEND | Default redis://127.0.0.1:6379/1 |
| REDIS_CACHE_URL | Dashboard cache, default redis://127.0.0.1:6379/2; 20-second TTL, SQL fallback |
| CELERY_TASK_DEFAULT_QUEUE | Default celery; isolate queues for separate environments |
| TELEGRAM_BOT_TOKEN | Private BotFather token; existing TG_BOT cloud binding also supported |
| PUBLIC_BASE_URL | Frontend site URL |
| CSRF_TRUSTED_ORIGINS | Explicit full HTTPS origins in production |
| MEDIA_ROOT | Optional private storage directory override |

Never put tokens in source, screenshots, Git, logs or browser storage. Configure Telegram tokens securely in the environment, and allow HTTPS to api.telegram.org. HTTPS_PROXY is respected by the bot when present.

## Run every service

Use separate terminals, starting at the repository root unless stated otherwise.

```sh
# Redis (after Homebrew installation)
brew services start redis
redis-cli ping  # PONG
```

```sh
source .venv/bin/activate
python backend/manage.py runserver 127.0.0.1:8001
```

```sh
source .venv/bin/activate
PYTHONPATH=backend celery -A config worker --pool=solo --concurrency=1 --loglevel=INFO
```

```sh
source .venv/bin/activate
PYTHONPATH=backend celery -A config beat --schedule /tmp/quiz-bot-beat --loglevel=INFO
```

```sh
source .venv/bin/activate
python -m bot.main
```

```sh
cd frontend
npm run dev
```

Open the Vite URL printed by the command. Default port is 5173; `/api` proxies to Django on 8001. `BACKEND_URL` and `VITE_PORT` override these for isolated tests. Live processes must be restarted after restoration/publication; installed files alone do not preserve workers or polling.

## Teacher onboarding and authentication

1. Create a real Super Admin with `createsuperuser`.
2. Log in through the web panel and open O‘qituvchilar.
3. Create a teacher with full name, username, email and specialty.
4. Copy the generated temporary password from its one-time dialog and deliver it privately.
5. The teacher logs in and must replace it before panel APIs become accessible.

Temporary credentials expire after 24 hours. Super Admin can issue a replacement, or activate/deactivate the account. Passwords are Django-hashed; no plaintext password is retrievable after issuance. Password changes invalidate the old credential and rotate session authentication. Disabled accounts lose authenticated API access.

Browser authentication uses Django sessions and CSRF. The client bootstraps CSRF, includes it on mutations, clears other users' caches on logout and rechecks invalid sessions. No session secrets or passwords are placed in localStorage. Only theme preference is stored there. Authentication/code throttles use transactionally incremented, hashed SQL buckets, so a Redis outage cannot bypass them.

## Quiz and question workflow

A new quiz is a draft. The wizard has basic settings, questions and publishing stages, retains entered settings and prevents publication with unsaved changes. A data-router guard protects dirty forms on links and browser Back/Forward; tab close uses the browser confirmation. Questions can be created manually, selected from the owned bank, reordered, detached, duplicated or imported. Images can be replaced/removed. Teachers cannot attach another teacher's question to their quiz.

Lifecycle: draft → published → closed → archived; drafts may also be archived. Publishing validates settings, question count, options, correct answers, points and availability. Draft deletion is allowed only without attempts. Active quizzes/questions are edited through a new independent draft copy. Quiz duplication copies question content, not student attempts/results or access codes.

Private codes are cryptographically generated and regenerable. Available public quizzes are listed in Telegram; private quizzes require code validation. Codes and quiz windows both expire. Publishing a private quiz generates its code.

## XLSX template, ZIP and images

Download the real template in the import dialog or `/api/questions/import/template/`.

- Questions sheet columns: Question, Option A/B/C/D, Correct Answer, Points, Image File Name.
- Instructions!A1 identifies `QUIZ_BOT_TEMPLATE_V1`; mismatched templates are rejected.
- Four nonempty options, one correct A–D answer and positive points with at most two decimal places.
- At most 500 questions, 10 MB input, 40 MB aggregate expanded archive/staging and 1500 archive members.
- Raster images: PNG/JPEG/WebP, 5 MB before and after normalization, 16 million pixels. Stored as randomly named PNG files with metadata removed.
- ZIP contains exactly one XLSX plus relative referenced images, e.g. `images/question_001.png`. No paths are extracted to disk. Traversal, absolute paths, symlinks, duplicate/ambiguous paths, nested archives, unsupported entries and encrypted archives are rejected.
- Embedded images must be on the Questions sheet, one image anchored in column H on its exact question row. Unsupported/ambiguous anchors and unsupported image types produce errors. The pinned openpyxl private image-reading adapter is isolated and covered by regression tests because the library provides no public image-reading API.
- Formulas, external workbook links and external image references are rejected; formulas are never executed. Duplicate question rows within one upload are errors.

Upload → preview/errors/thumbnails → confirmation. Preview commits no questions and expires after 30 minutes. Confirmation is all-or-nothing and idempotent. Correct the file and upload again if any blocking errors exist. Images are private and served through authorized question endpoints, not public media URLs.

## Telegram examination and recovery

Commands: `/start`, `/menu`, `/help`, `/continue`, `/cancel`.

First `/start` asks for full name and binds it to Telegram's authenticated user ID. Main menu offers public quizzes, code entry, continue, results, ranking and profile. `/cancel` cancels only conversational state; it never silently cancels an exam or pauses its timer.

At start, SQL freezes the question text, scoring, answer mapping and order. Sequential mode saves one answer and advances; stale callbacks cannot alter a previous answer. Free mode permits navigation and replacement until completion. Callbacks verify identity, ownership, revision, question/option membership, state and server deadline. Duplicate starts reuse an active attempt; duplicate callbacks do not duplicate answers.

The deadline is `min(start + duration, configured closing time)`. It never pauses when Telegram, Redis or the bot restarts. `/continue` rebuilds state from SQL. Each answer/finish checks server time, independent of Celery timing. Beat reconciles missed expirations every 30 seconds. Early finish requires an explicit confirmation. Answered questions earn their configured points; incorrect and unanswered answers separately earn zero. Completion is idempotent.

Points use Decimal. Percentages are stored to six decimal places for ranking; displays round appropriately. Result fields are gated on the backend. Defaults show score/percentage/correct/incorrect counts and rank; detailed answer review is off. Release may be immediate, after quiz closure or manual. Hidden percentages cannot leak through Telegram overall rankings.

## Results, rankings and reporting

Teachers see only their quizzes' attempts and student history. Students shared by teachers do not expose cross-teacher private test names/results. Results include authorized per-question snapshot breakdowns and date/student/quiz filters.

Per-quiz ranking chooses each student's best final attempt, then orders by percentage descending, elapsed seconds ascending, and student ID ascending. Overall ranking averages best percentages per eligible quiz. Positions are sequential and may change as students finish. This average does not normalize quiz difficulty.

Telegram overall ranking includes only public, released, ranking-enabled quizzes with percentage visibility. Private per-quiz ranking requires a completed participation; percentage is omitted when hidden. Public display names are limited to first names.

Reports: results, student summaries, leaderboard and Super-Admin-only teacher activity. XLSX exports use the same authorized filters and escape formula-triggering user text. Up to 5000 attempt rows can export synchronously; larger jobs use Celery. Exports are bounded to 100000 input rows; use filters for larger datasets. The UI polls status and offers authenticated downloads only when ready. Jobs have bounded transient retries and failed status on permanent failure. Old exports are cleaned after seven days; staged imports expire after 30 minutes.

## API overview

All paths have `/api/` prefix; collections paginate at 25 rows.

| Area | Routes/actions |
|---|---|
| Auth | GET auth/csrf/, GET auth/me/, POST auth/login/, logout/, change-password/ |
| Profile | GET/PATCH profile/ (full name/email/specialty only) |
| Teachers | teachers/ GET/POST; detail GET/PATCH; reset-password/, activate/, deactivate/ POST |
| Students | students/ and detail GET, with scoped aggregates and latest 25 attempts |
| Groups | groups/ standard Super Admin CRUD including membership |
| Quizzes | quizzes/ standard CRUD; publish/, close/, archive/, duplicate/, regenerate-code/, release-results/ POST; questions/ GET/PUT ordered IDs |
| Questions | questions/ standard CRUD; duplicate/ POST; image/ authorized GET |
| Imports | questions/import/template/ GET; preview/ multipart POST (quiz + file); confirm/ POST (session id) |
| Results | results/ and detail GET; rankings/ GET; dashboard/summary/ GET |
| Reports | reports/summary/?type=students/teachers/leaderboard GET; reports/export/ POST; reports/exports/ GET; job detail/status and download/ GET |

Result/report filters include quiz, student, status, search, start/end (inclusive Toshkent calendar dates), min_score and max_score. Quiz filters include search/status/subject/access and whitelisted ordering. Dashboard accepts days 1/7/30/90 or a custom start/end range. Scheduling inputs/display dates use Asia/Tashkent; SQL stores aware UTC timestamps.

## Testing and verification

```sh
source .venv/bin/activate
pytest -q
ruff check backend bot scripts
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
cd frontend
npm test
npm run lint
npm run build
cd ..
python scripts/browser_suite.py
```

The browser suite starts separate Django/Vite ports and a dedicated native Celery worker/queue with a disposable SQLite database, media and random test credentials. It exercises actual API-backed web workflows and exports. Fixtures are explicit and opt-in; none are added during normal app startup. Test identities are deleted with the temporary directory. Screenshots/reports default to a sibling `artifacts/e2e` directory; `QUIZ_ARTIFACT_DIR` overrides it.

Install Chromium or set CHROMIUM_PATH to its binary (on macOS it can be `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`). The suite checks light/dark, widths 360/390/768/1024/1280/1440/1920, keyboard dialogs, and axe WCAG checks. Use `--scripts management-check.mjs` to rerun a specific workflow in a fresh environment. No passing compile is represented as functional validation. Explicit API/Bot API mocks occur only in unit tests, never in production pages.

Backend tests include account onboarding/CSRF, ownership, quiz lifecycle, shuffled snapshots, sequential/free answers, exact deadline, resume, duplicate finalization, simultaneous start/answer/finish using file-backed SQLite, imports/images/hostile archives, formula injection, report download ownership and Aiogram callback-to-real-domain-service flow. A live human Telegram run is a separate outstanding check.

Dependency audits are in the progress record. Full npm audit currently fails on GHSA-fc5q-39xc-vjpf (picomatch <=4.0.7; registry latest 4.0.7), affecting build/test tooling dependency chains. The production npm audit is clean. CI retains the full audit as a blocking gate; do not suppress it. Earlier DRF/Pillow advisories were resolved by upgrades and a clean re-audit; repeat audits before production deployment. TypeScript is strict; explicit any is prohibited and ESLint must report zero warnings.

## Deployment, concurrency and backups

Use a native Linux/macOS process manager and same-origin reverse proxy; Docker is not required. Serve Vite's `frontend/dist` with SPA fallback, proxy `/api` and `/admin` to the Django WSGI app, and serve collected static files. Never add a public alias for backend/media. Configure HTTPS, DEBUG=false, strong secrets, explicit hosts/CSRF origins and secure cookie flags. Do not blindly trust forwarded client-IP headers; configure proxy/client identity at the trusted deployment boundary.

```sh
cd frontend && npm run build && cd ..
python backend/manage.py migrate
python backend/manage.py collectstatic --noinput
python backend/manage.py check --deploy
# Run config.wsgi:application with a supported WSGI server and supervise
# Django, Redis, Celery worker, Beat and `python -m bot.main` independently.
```

SQLite uses IMMEDIATE write transactions, a 30-second busy timeout and uniqueness/check constraints. It is for modest concurrency, not arbitrarily high examination traffic. For PostgreSQL, install a supported psycopg driver, provision a private database, set DATABASE_URL, rehearse export/import into a separate database, apply migrations and rerun concurrency/constraint/ownership tests before switching. Do not delete the SQLite source to bypass a migration failure.

For a consistent SQLite backup:

```sh
sqlite3 backend/db.sqlite3 ".backup 'backup.sqlite3'"
# Back up backend/media separately, coordinating writes for a consistent pair.
```

Restore only with services stopped; preserve current data, restore the database and matching media, run migrations/checks and verify protected files and scoped results. Keep secret environment values in a separate secure backup, never in distributable archives. Check logs for rejected authentication, authorization denials, failed jobs, quiz transitions and attempt finalization; logs must not include passwords, tokens or uploaded content.

### Troubleshooting

- Missing secret: configure a generated DJANGO_SECRET_KEY; no fallback production key exists.
- CSRF failure: use the Vite proxy/same origin, correct trusted origins and fresh bootstrap token; never disable CSRF.
- Expired temporary password: Super Admin issues a new one-time credential.
- Redis unavailable: start native Redis and retry; examination state/deadlines remain in SQL. A missing Redis connection prevents bot startup.
- Telegram access denied: verify secure token binding and allowed api.telegram.org destination; do not paste tokens in chat or disable TLS verification.
- Unknown Celery task after code changes: restart the worker; installed files do not reload an existing process.
- Database locked: reduce write concurrency or migrate to PostgreSQL; do not remove constraints or reset user data.
- Import failure: follow row-specific errors, template version and image-anchor rules, then upload a corrected file. No partial import is silently accepted.
- Browser-suite failure: inspect saved artifacts, fix the real failure and rerun; it never uses the live database.
