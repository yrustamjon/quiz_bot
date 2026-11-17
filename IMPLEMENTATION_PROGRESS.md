# Implementation progress

Specifications: [MASTER_PROMPT](docs/MASTER_PROMPT.md) and [FRONTEND_MASTER_PROMPT](docs/FRONTEND_MASTER_PROMPT.md). Communication/UI: Uzbek. Native services only; no Docker. Preserve existing data and Git changes. Direct pushes to main are authorized; environment publication is not.

## Current phase
Phase 11 — final hardening, acceptance evidence and runtime verification. Phases 0–10 have implemented components and passing automated workflows; live human Telegram acceptance is still outstanding. The chronological notes below are historical, not current TODO lists.

## Current verified evidence
- Backend: **77 passed**, including malformed authentication input, temporary-password reuse, private image ownership, scoring/ranking ties, imports and concurrency/security regressions.
- Frontend: **15 tests passed**, strict TypeScript production build and ESLint zero warnings, including StrictMode Back/link cancel/proceed guards.
- Full isolated real-browser suite passed, including actual SQL/API authentication/onboarding/import/publish, question/group management, private-code rotation, draft duplication/deletion, student/result detail, four XLSX kinds and a real Celery background export.
- Expanded browser actions passed: teacher edits/deactivation/reset, student activation, manual raster add/remove, question duplication/deletion, bank selection/reorder/detach.
- **50 route/dialog/state/theme axe combinations, zero violations**. Seven viewport widths checked: 360/390/768/1024/1280/1440/1920. Latest import-preview table and data-router/form guards passed integration, management and axe reruns.
- Python (54 pinned packages) and npm production dependency audits: zero known vulnerabilities. Earlier DRF/Pillow advisories were fixed by upgrades. **Full npm audit FAILED: picomatch <=4.0.7 ReDoS (GHSA-fc5q-39xc-vjpf / CVE-2026-112366), 14 high dependency-chain entries. Registry latest is 4.0.7, no fixed release listed. This is build/test tooling; no audit suppression or force upgrade used. Full audit is a blocking CI gate.**
- Django system/production checks and migration drift checks passed; pip check passed. Redis FSM write/reconnect/read and isolated-key cleanup passed.
- **22 screenshots confirmed delivered via Telegram**, credentials/destination outside Git.

## Current work
Latest user priority: Telegram bot was visually cluttered and slow in the user's local environment; requested partial @QuizBot UX inspiration while retaining agreed functions. Implemented compact native controls, one-message panels, 5-item pagination, paginated results, progress/selection feedback, concurrent callback acknowledgement, duplicate-tap coalescing and reusable Telegram photo IDs with stale-ID recovery. **Full backend: 77 passed.** Current frontend remains validated by 15 unit tests, production build/lint and the six-script real-browser suite (50 axe combinations, zero violations).

User clarified the screenshots came from a local installation. Cloud database differences are expected; do not migrate or overwrite either DB. Cloud changes do not automatically replace a running process on the user's Mac. After the authorized main push, local source must be pulled and the old bot process stopped/restarted. No fixed millisecond improvement is claimed without new local measurements; `Bot interaction kind=… render_ms=… total_ms=…` logs permit verification without logging payloads or secrets.

Current source after main 69d4e65 awaits final documentation/source scan and push. The open upstream picomatch advisory remains a security gate; its candidate PR was tested and still fails three bounded adversarial cases.

## Remaining acceptance gates / exact next steps
1. Screenshot delivery complete: **22 confirmed**. Finish the bot UX checkpoint source scan/commit/push and record delivery. Keep environment publication under user control.
2. Track upstream [picomatch PR 194](https://github.com/micromatch/picomatch/pull/194) and [GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf). Official advisory JSON was fetched from github/advisory-database (2026/10); affected versions introduced 0, last affected 4.0.7, no fixed event. `npm view picomatch dist-tags` returns latest 4.0.7. Once an audited fixed release is available, update the lockfile within supported ranges, rerun **full** npm audit, build/lint/Vitest/browser suite and push. Do not hide this audit failure or use `--force` to bypass it.
3. Apply main to the local installation (`git pull --ff-only origin main`, stop old polling process, activate .venv, `python -m bot.main`). User screenshots show local registration, public lists and invalid-code feedback; new layout, actual local latency and full exam completion still need local verification. Avoid two polling processes for the same bot token. Handler tests use real SQL with test transport; they do not substitute for a live local exam.
4. GitHub CI execution is unverified until observed remotely. Full npm audit is expected to remain red on the current upstream advisory. Production deployment and PostgreSQL load validation are outside current local evidence.

Runtime after latest source: Django 40137, bot 40138, worker 40139, Beat 40140 (verify current PIDs after environment restoration). Worker real queue roundtrip + captured startup source fingerprint passed. User data was preserved.

## Recovery / exact commands
Read both prompts and this file, inspect `git status --short` and current source before edits. Do not recreate completed components. Run:

```sh
.venv/bin/pytest -q
.venv/bin/ruff check backend bot scripts
.venv/bin/python backend/manage.py check
.venv/bin/python backend/manage.py makemigrations --check --dry-run
cd frontend
npm run build
npm run lint
npm test
cd ..
.venv/bin/python scripts/browser_suite.py
```

Browser tests use temporary DB/media/credentials and a unique Celery queue, not the user's DB. Artifacts are outside Git under `/workspace/artifacts/e2e`. Bot token is a runtime binding (`TG_BOT` alias supported); never print/copy it into tracked files. Last verified source checkpoint pushed to main: `308bec7` (100 files, 58 backend + 15 frontend tests). This final progress record is a documentation follow-up. Update this section before interruption or final handoff.

## Historical implementation journal

## Update — 2026-11-17, resumed after publication
- Preserved previous code and read both specifications. User authorized direct commits/pushes to main; no environment publication authorized.
- Phase 1 accounts backend completed at initial scope: 4 tests passed.
- Implemented quiz/question CRUD, ownership filtering, lifecycle validation, private codes, bank linkage and safe raster re-encoding/protected image access.
- Implemented internal SQL exam services: immutable snapshots, stable option shuffling, idempotent start, sequential/free answering with revisions, server deadlines, resume, explicit early finish, scoring and result field/release gates. These need broader concurrency/ranking tests before acceptance.
- Added migrations for quizzes/questions/attempts and ran them successfully.
- Backend validation: `pytest -q` **10 passed**. This is not the full required security matrix.
- Frontend initial foundation: React/Vite/TypeScript/Tailwind, shadcn-style Button/Radix Dialog primitives, theme, role-aware shell, CSRF/session client, auth, real dashboard, draft creation, directories/profile. `npm run build` passed.
- Chromium real rendering inspected for login and dashboard light/dark/mobile. Browser checks passed: login validation; seven widths (360/390/768/1024/1280/1440/1920); actual session login, API-backed draft create, refresh persistence, dashboard/directories/profile, mobile dialog Escape, logout.
- Sent initial login screenshots via Telegram (3 confirmed HTTP 200). Dashboard screenshots captured and delivery started. Token remains only in existing runtime binding TG_BOT, not repository source. Destination metadata is outside the repository.
- Full UI not complete. Results/rankings/reports navigation intentionally not displayed until working pages exist; mandatory requirements remain unchanged.
- A first dashboard file command used the wrong cwd and failed; rerun from repo root corrected it. TypeScript generic undefined return fixed before successful build.

## Current next tasks (do not reset completed code)
1. Commit/push this verified checkpoint to main, excluding local .env, DB, node_modules, artifacts and test credentials.
2. Finish question editing/quiz wizard and teacher management frontend; add form/permission tests.
3. Build bounded XLSX/ZIP/embedded-image parser with staged import preview/confirm and hostile input tests.
4. Build scoped results/ranking/report APIs and UIs; secure XLSX downloads and background cleanup.
5. Aiogram router/FSM integration with existing services; reconcile/Redis/Celery runtime; real Telegram end-to-end exam.
6. Expand race/CSRF/upload/authorization tests, Vitest/Playwright, accessibility and every-page visual verification; complete README and audit.

Known gaps: no full Excel/import/report system, no executable bot yet, no group UI, no full question editor/wizard, limited tests, no Redis server yet, no production readiness claim. Environment publication does not change these gaps.

## Update — continued implementation and recovery checkpoint
- Verified commit `56d9916` pushed to `origin/main` (initial foundation/UI). Later work below is currently uncommitted until checks finish.
- Excel v1 template, XLSX/ZIP/embedded-image parser, bounded archive safety, staged 30-minute preview and idempotent transactional confirmation implemented; questions migration 0002 applied. Image adapter explicitly documents tested openpyxl private APIs.
- Added scoped results, per-quiz/overall best-attempt ranking service, real formula-escaped XLSX export, ReportExport model/migration, protected owner-only download/status, Celery generation and 7-day cleanup. Browser handles queued exports instead of saving JSON as XLSX.
- Added question editor, import preview/confirm UI, quiz settings (three tabs), result visibility preview, teacher creation/activation/reset and one-time password dialog, results/ranking/report pages.
- Added Aiogram routers for registration/menu/public/private tests, resume, answer/navigation callbacks, early finish confirmation, results/profile/ranking. Uses SQL exam services and Redis FSM. Commands documented in bot/main.py. Full live student exam has NOT run yet.
- Native Redis 8.2.3 compiled from official Redis GitHub HTTPS source into `/workspace/tools/redis/redis-8.2.3`; two build jobs, libc allocator. System apt package metadata unavailable (safe local source build used instead). Redis running on localhost:6379; PONG verified.
- Celery solo worker started (session 61579, logs `/workspace/artifacts/celery.log`); real queued reconcile and cleanup tasks returned 0 successfully. Worker needs restart after later task edits. Aiogram proxy-aware real getMe passed; webhook false. Bot polling not yet started.
- Backend 19 tests passed including file-backed SQLite concurrent start/answer/finish and manipulated bot callback. Added two further snapshot/report ownership tests; current full run pending.
- Frontend Vitest: 5 passed. Fixed label lookup issue with explicit accessible login name.
- Real Chromium integration passed: admin login -> teacher creation -> one-time temporary login -> forced password change -> draft -> real XLSX preview/confirm -> publish -> report XLSX download. No page errors. Results/rankings/reports/profile/questions/students checked at seven widths. Export downloaded from browser opens with openpyxl.
- Browser caught an actual logout/auth cache race. Fixed AuthProvider to clear stale identity on errors, await session refetch, and clear non-identity caches on logout. Integration passed after fix.
- Screenshots viewed: login light, dashboard light/mobile-dark, import preview. Login/dashboard screenshots (7) confirmed sent via Telegram. Additional teacher/import/published screenshots delivery session 40892 pending confirmation. All secrets/test identities and screenshots are outside Git checkout or ignored; never include .env or /workspace/artifacts/ui-*.json in commits.
- Django dev server restarted on 8001 (session 26967), Vite on 5173 (session 75377).

### Exact next steps
1. Finish current pytest run, confirm screenshot delivery. Format/lint/typecheck/tests/build all current changes, then commit/push verified increment to main.
2. Add bank question CRUD UI, selection/reorder/remove; distinguish wizard steps correctly (currently 2/3 share questions/publication panel); unsaved-change guards and stronger forms.
3. Finish groups/settings/profile edits, result detail/date filters, report job feedback and report-specific analytics.
4. Add bot handler integration tests, real exam if user participates, error recovery; server deadline finish/expiry race tests, malformed input and all upload/ownership negative tests; improve logging and DB constraints.
5. Restart worker with updated tasks; exercise background exports through real queue; start Beat with schedule state outside repo. Check bot runtime safely, never claim complete live exam on getMe alone.
6. Expand all-page light/dark screenshots including 360px dialogs, accessibility audit, portable E2E setup, README update, final security scan and main push.

### Remaining definition-of-done gaps
No claim of completion: full bank workflow/group UI/settings/profile edits, complete date filters/results drilldown, all security/acceptance scenarios, full live Telegram exam, accessible all-page visual audit, full documentation and production audit remain. Existing old README feature list needs updating to reflect latest verified scope. Never treat this checkpoint or file existence as acceptance.

## Latest validation and continuing work
- Backend now **22 passed** including account/profile escalation negative test, concurrency, XLSX images, result/export ownership and callback tampering.
- Frontend **5 Vitest passed**, production build passed after bank/group/profile components. ESLint has no errors but explicit-any warnings remain to improve.
- Axe real browser audit **20 route/theme combinations, zero violations**. Initial runner error required an explicit BrowserContext; corrected and reran successfully. Newly added routes/dialogs require expansion.
- The initial concurrency run used Django's shared-memory SQLite and failed with table locking. Added isolated config.test_settings with a real file DB; reran simultaneous start/answer/finish successfully. No assertion disabled.
- Added questions 0003 migration for Decimal validator after migration check identified the needed state change; migration applied and no drift remains.
- Added minimal groups UI and safe profile PATCH; added bank selection/order/removal. Quiz duplication now clones question content so edits to a new draft can never mutate the original quiz.
- Bot polling running (session 32408), real pending updates handled. User still needs to participate for a real Telegram exam; do not claim that scenario passed.
- Worker restarted with current report tasks (86971), Beat running (37489), Redis active on localhost. Real background export test is next.
- Screenshots for teacher list/import preview/published quiz confirmed sent. **10 total screenshots sent**. No temporary password screenshot was captured.
- Next: push verified increment, restart Django after profile endpoints, test background export and new group/profile/bank actions; expand all-page dark/mobile/axe audit; close remaining accepted feature gaps (student/result details/date filters/teacher edits/group membership/full wizard navigation/error recovery/security hardening/portable tests/docs).

## Continuing hardening (post 399c3a7)
- Native full browser suite now available: `.venv/bin/python scripts/browser_suite.py` starts its own Django/Vite ports, fresh SQL DB/media, temporary accounts, and cleans up credentials/processes. Existing DB is not used. Full initial isolated suite passed (4 browser scripts including axe).
- Added report kinds (result/student summary/leaderboard/admin-only teacher activity) and matching real XLSX output; result detail and student detail scoping; result date/score filters; profile updates; teacher editing; bank reorder and quiz question cloning; unsaved-change guards.
- Added DB enum/score/attempt-limit constraints (new accounts/quizzes/attempts migrations), applied them. Added transactional hashed RateLimitBucket model for cross-process throttling; failed private start attempts now account outside the failed transaction (regression test added). Redis outage never bypasses throttling.
- Tightened normalized image-size and aggregate staging limits to prevent repeated JPEG/ZIP references inflating staging memory.
- Fixed expired start rollback: repeated start on a maxed expired attempt returns its finalized result instead of rolling back finalization.
- Added bot deleted-message acknowledgement recovery and generic update error handler; SQL snapshots remain authoritative.
- Backend 33 passed before latest throttle regression (current run pending); production npm audit reported 0 vulnerabilities. Ruff passed. Portable build needed explicit @types/node for Vite environment settings; installed and build passed.
- Remaining work before any completion claim: finish minimal group membership and account dropdown, dashboard required summaries/custom ranges, typed API cleanup, fresh runtime restarts and all-page/all-dialog/browser checks, audit dependencies, broaden release/ranking/race/upload tests, live Telegram student exam (currently only polling/getMe/handler tests verified), complete final docs and acceptance traceability. Current source changes after 399c3a7 not yet pushed.

## Current checkpoint — expanded implementation and dependency hardening
- Latest backend **38 passed** (includes a full Aiogram callback journey using real SQL services and mocked transport, plus hidden-percentage ranking regression). Live human Telegram exam is still unverified.
- Frontend **8 Vitest tests passed** (wizard retains edits, blocks unsaved publication, result preview toggles, invalid import cannot confirm, plus auth/theme/dialog/states). Several first test attempts exposed matcher/type issues; corrected selectors and reran without weakening feature assertions.
- Isolated full browser suite now includes group membership, persisted profile edits, manual questions, real student/result detail, four real XLSX report kinds, dropdown keyboard controls and expanded responsive light/dark pages. Latest completed suite passed; **24 route/theme axe checks, zero violations**. Later wizard/image changes need another complete run.
- Reviewed new group dark and result-detail screenshots. Corrected outline class collision with Tailwind, excessive percentage decimals, read-only dialog description, menu ordering and explicit Toshkent date display. Sent three more screenshots; total confirmed delivery pending session 31741 (expected total 13).
- Required UI now includes account dropdown, notifications, group membership/edit/delete, bank duplication/ordering/detach, quiz list subject/access/order filters, three distinct wizard stages with preserved settings and RHF/Zod validation, private code management, manual result release, report queue history/downloads.
- Added resource-bound upload middleware/handler, shared bounded raster normalization, image removal without breaking historical files, archive normalization/unsupported embedded-image guards, stronger publication validation and transactional quiz mutation checks.
- Identified dependency advisories (DRF 3.16.1 and Pillow 12.3.0). Upgraded to **DRF 3.18.3 / Pillow 13.0.0**, pip check passed, tests passed, pip-audit rerun found **0 known vulnerabilities**. npm production audit found **0 vulnerabilities**. Audit cache permission failure was fixed with an explicit writable cache path; no verification bypass used.
- Restarted owned runtime services after upgrades: Django 36862, bot polling 35296, worker 1452, Beat 49861. Further source edits require another restart before final live verification.
- README rewritten around actual implemented behavior and native macOS commands; historical pending lists above are superseded by this checkpoint. No production-readiness claim.

### Exact recovery / next tasks
1. Read both master prompts + progress and inspect git. Current changes since main commit 399c3a7 are uncommitted; do not recreate implemented components.
2. Finish current build/check sessions, run full isolated browser suite after newest wizard/image/toast/filter changes; fix any real failures. Extend axe to wizard/dialogs and verify read-only modal descriptions/date formats/mobile controls.
3. Complete remaining acceptance gaps: full race/release/ranking cases, code/ownership/upload negative coverage, accessible destructive confirmation UX, final typing/lint cleanup, meaningful production/deployment checks. Compare implementation to original acceptance matrix rather than file counts.
4. Refactor oversized bot callback handler into focused modules after keeping its tested service interface. Verify Celery failure/status and cleanup paths and restart current workers after task edits.
5. Run final audits/security checks, update current validation evidence and remaining limits, secret-scan staged source, commit/push to main (already authorized). User expects screenshots via Telegram; destination outside repo and TG_BOT runtime binding are working. No environment publication authorized.
6. A live human Telegram exam requires actual student participation; do not claim polling/getMe or mocked transport tests establish it. Continue all independent work before reporting a genuine external blocker.

## Continuing verification checkpoint
- Latest completed backend run: **40 passed**; added expired temporary-session regression (run in progress). Frontend **12 tests passed** including routing boundaries, wizard/state/preview/import rejection. TypeScript API responses now have explicit shared contracts; `api` defaults to unknown and explicit `any` is prohibited by ESLint. Full typecheck passed after fixing response narrowing and optional media fields.
- Added Uzbek Zod locale, localized DRF/CSRF error responses, server-side preview error cleanup, consistent mutation notifications and localized network errors.
- Added reusable keyboard-accessible Uzbek file picker/drop zone. Shared normalized image service is used by manual and XLSX uploads. Three-stage wizard now places publishing settings in the third stage, retains values, prevents unsaved publication and supports previous/next navigation.
- Added role/database-scoped 20-second Redis dashboard cache with SQL fallback; unit tests use isolated memory cache and never clear live Redis. Throttles remain transactional SQL. Added dashboard status distribution, recent attempts, most-active quizzes and custom date ranges.
- Refactored bot into registration/callback/presentation modules with preserved tested callback interface. Added private per-quiz ranking permission and hidden-percentage protection; Telegram overall board excludes private/unreleased/hidden-percent quizzes.
- Most recent completed isolated browser suite: all five scripts passed (real auth/teacher onboarding, drafts/import/publish, group membership, manual questions, profile persistence, details, four reports, responsive themes), **24 axe combinations: 0 violations**. Subsequent typed/file-picker/wizard/UI changes require another final run.
- Added native (no Docker) read-only GitHub CI configuration using official action commit SHAs verified from upstream v6 tags. CI has not yet run remotely; do not claim a remote CI result.
- Still no final completion claim: full last-run browser/security/acceptance matrix and a human Telegram exam remain to verify. The initial human check question was sent asynchronously; continue independent work while awaiting it.

## Final hardening evidence — 2026-11-17
- 58 backend + 15 frontend tests passed. Typecheck/build/lint, Django deploy/system/drift, pip check and source hygiene passed.
- Full browser run passed login/panel/onboarding/import/publish; the new Back test initially attempted cross-document `page.goto` history (native beforeunload), so its custom-modal expectation timed out. Corrected the test to create real SPA history with a client link; management plus 42 axe checks then passed. No product assertion was removed.
- Management now checks teacher edit/deactivate/reactivate/reset, student status, raster persistence/removal, question duplication/deletion, bank order/detach, private code rotation, draft duplicate/delete cancel/confirm, dirty link cancel and browser Back confirm, actual Celery report generation and authenticated download.
- Browser helper now terminates only its own process groups, cleaning npm/Vite children. Optional --scripts supports focused fresh-environment reruns.
- Added full dependency audit after production audit exposed no issues: actual full audit found upstream build/test picomatch ReDoS with no fixed published release. Functional pass is not a complete security acceptance. See remaining gate above and implementation report.

## Recovery checkpoint — 2026-11-18 (Asia/Tashkent)
- Working tree preserved after environment restart; no changes reapplied. Main remains 69d4e65; current follow-up is uncommitted.
- Backend **64 passed**; frontend **15 passed**, build/lint passed before the newest offline notice. Added SQL update/publication serialization and tests for publication race, resume/expiration race, real exported formula cells, source identity.
- Worker PID-only readiness was a false positive: old worker 11946 survived SIGTERM because its closed stdout caused BrokenPipeError; new 29694 had exited with a pidfile conflict. Verified idle state, shut down the old worker using Celery control, started 33362 with durable file output. New `scripts/check_worker.py` passed real queue roundtrip + startup-source fingerprint. After subsequent backend edit, it correctly failed stale-source verification. Restart the worker after final edits and rerun it.
- Official picomatch PR194 commit 7be3276fb8bd215a8c73fa066bcaf696c244ad88 was reviewed against installed4.0.7 in an isolated copy. Bounded child-process tests show both versions still time out for +(*)b, +(*a)b and *(*)b. No unverified patch applied. `npm run test:security` now reproduces this safely (1.5s per child), intentionally fails until fixed; full audit stays blocking.
- New real browser security flow confirmed stored question/quiz HTML is rendered as text. It then exposed an offline UX gap: TanStack pauses requests when navigator goes offline, leaving an unexplained loader. Added an explicit online/offline notice and real retry controls; next step is rerun `scripts/browser_suite.py --scripts security-check.mjs` after build/lint, then all six browser scripts.
- Browser security test uses real transport failure/latency via Chromium CDP (no fabricated API responses), then error/retry/empty/loading screenshots. CDP rule-based emulation is supported and leaves navigator online, unlike browser offline mode.

### New verification results / exact recovery
- `pytest -q`: **65 passed**. Includes a regression that first reproduced AttributeError/HTTP500 for a top-level JSON array, then passed 20 malformed payload cases across four custom endpoints after ObjectJSONParser was added. Multipart uploads remain supported; all parser/import tests passed.
- Frontend lint/build and **15 Vitest passed** after offline notice and styled retry controls.
- Real browser offline notice/reconnect, native request blocking + retry/empty, delayed real response/loading and stored XSS-as-text passed. A full-suite login failure was diagnosed as test ordering: management deliberately resets the shared teacher password. Security now runs before that terminal reset; no product checks weakened.
- New dynamic accessibility checks cover offline/error/empty/loading in Light/Dark; full suite final result and photo delivery await completion. Send screenshots only after suite copies its temporary artifacts into /workspace/artifacts/e2e.
- An intermediate restart was safely aborted when /proc/PID/cwd was unreadable; recovery verified the exact stored PID and command arguments, gracefully stopped the owned processes and restarted all four. No unrelated processes were killed and no data was reset.

## Active user steering — Telegram UX/performance, 2026-11-18
- User supplied real Telegram screenshots: each callback appended another large menu/list. Requested a lighter, cleaner bot and selected @QuizBot as partial UX/function reference while preserving agreed features.
- Current implementation in progress: one-message callback panel editing with safe missing-message fallback; per-panel async serialization; concurrent tap acknowledgement/render; 3-row/6-action home; 5-item numbered public pagination; one-result history pagination; bold Unicode-safe headings, answer progress and selected-answer markers. Existing SQL deadlines, ownership/revision and release flags remain authoritative.
- Initial transport tests needed explicit message.chat/message_id and edit_media assertions, since the expected operation changed from posting to editing. New regressions cover network call counts, noop/deleted/error cases, parallel acknowledgement and SQL-backed pagination.
- Important target mismatch found: configured token resolves to @ContactforClent2025bot and active DB contains 0 students / 1 published public quiz, while user's screenshot shows registration and ~20 quizzes. Asked asynchronously for the screenshot bot username to identify the correct runtime/data source. Do not overwrite credentials or delete/migrate data based on this discrepancy. Continue code/test work independently.
- Direct @QuizBot interaction/public reference fetch is unavailable here (no authenticated Telegram client tool, t.me/telegram.org network requests denied). Do not claim its private screens were inspected. UX is inspired by its compact quiz workflow and the user's screenshots.
- Before this Telegram redesign: all six isolated browser scripts passed; 42 route/dialog + 8 dynamic-state theme axe checks = 50 combinations, 0 violations; 65 backend / 15 frontend tests passed. Four additional screenshots delivered successfully (total **22**).
- Next: finish bot UI regressions/full backend tests; verify current bot handler transport with safe live Bot API reads and restart the owned bot/worker after source edits. Confirm target username/data before claiming user-visible latency improved. Then update report, source scan, push authorized main checkpoint.

## Telegram UX final verification — 2026-11-18
- Full backend **77 passed**, including compact menu/action preservation; one edit/no new message on pagination; repeated-tap coalescing; acknowledgement/render concurrency; result history without message bursts; safe deleted/old message fallback; media-ID reuse/caption editing; invalid cached-ID eviction and real raster reupload; UTF-16-safe headings/chunks; finish-preview counts/deadline/ownership.
- Native button styles use supported Aiogram fields: primary selection, success start and danger finish. Selected answers indicate the student's saved choice, never the correct answer before permitted release. No grading, timer, callback ownership/revision or visibility flag was relaxed.
- The user confirmed the supplied screenshots were local; no production data was moved or deleted. Reference @QuizBot private screens were unavailable, so no exact visual-copy claim is made.
- New frontend recovery screens and all six isolated browser scripts already passed; total 50 axe combinations (42 routes/dialogs + 8 dynamic state/theme), zero violations. Four extra screenshots confirmed delivered, **22 total**.
