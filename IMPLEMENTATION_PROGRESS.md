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
