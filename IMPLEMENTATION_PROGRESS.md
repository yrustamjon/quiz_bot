# Implementation progress

Specification: [MASTER_PROMPT](docs/MASTER_PROMPT.md). User-facing language: Uzbek.

## Completed
- Phase 0: audited clean existing repository (only LICENSE and Python .gitignore). No existing application or secrets modified.
- Saved complete master specification for recovery.

## Current
- Phase 1: Django foundation and secure account onboarding.
- Installing maintained Django 5.2 LTS, DRF, Aiogram 3, Celery, Redis client, openpyxl, Pillow and test tools in .venv.

## Remaining tasks / acceptance gates
1. Accounts/session/CSRF/password onboarding, migrations and negative security tests.
2. React/Vite/Tailwind/shadcn foundations, session client and protected routes.
3. Teacher administration and permission tests.
4. Quiz/question lifecycle, snapshots, bank and ownership.
5. XLSX template, bounded ZIP/embedded images, transactional preview/confirm.
6. Aiogram registration, discovery, private codes and persistent identity.
7. Transactional attempts, sequential/free navigation, callback validation.
8. Deadline/resume/confirmation/scoring and Celery reconciliation.
9. Scoped results, release policies and rankings.
10. Real dashboards, reports, filtered XLSX exports and protected downloads.
11. Integration/security/concurrency/UI tests, native macOS instructions, production hardening.

## Decisions
- No Docker. Existing checkout is used. SQLite initially; explicit write serialization and transaction safeguards required; PostgreSQL migration documented.
- Bot calls shared Django services directly. Exam state persists in SQL, transient registration in Redis.
- Sessions and CSRF remain authoritative. Private images/reports require authorization.
- No demo data in normal runtime. Live Telegram validation requires a securely configured bot token.

## Validation
- Initial git status clean. Python 3.12.14; Node 24.22.1; npm 11.9.0.

## Recovery / exact next steps
Read docs/MASTER_PROMPT.md and this file, run `git status --short`, inspect existing files before editing. Resume first unchecked task; do not regenerate working components. Check installation session then implement/test Phase 1. Never mark unverified acceptance gates complete.

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
