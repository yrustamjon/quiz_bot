# MASTER IMPLEMENTATION PROMPT — QUIZ BOT

## ROLE AND MISSION

You are a principal full-stack engineer, senior Python/Django architect, React UI/UX engineer, Telegram Bot engineer, database engineer, application security engineer, and QA automation specialist.

Your task is to **design, implement, integrate, test, and document a complete production-oriented Quiz Bot platform** inside an existing Git repository named `quiz_bot`.

This is a real software engineering assignment, not a prototype exercise.

The system consists of:

1. A responsive web administration platform for Super Admins and Teachers.
2. A Django REST Framework backend.
3. A Telegram quiz bot using Aiogram 3.
4. A shared persistent database and domain logic.
5. Excel import/export with question images.
6. A secure examination engine, timer, scoring, leaderboard, and reporting system.
7. Redis and Celery for caching, bot state, and background jobs.

**The most important requirement: build a genuinely functional, integrated system.**

Do not substitute static mockups, fake dashboards, hardcoded statistics, placeholder API calls, simulated authentication, or incomplete CRUD operations for actual functionality.

The application must be usable end-to-end.

All code must be maintainable, secure, tested, and documented.

---

# PART 1 — NON-NEGOTIABLE PROJECT REQUIREMENTS

## 1.1 Existing repository

The project already has an existing Git repository:

`quiz_bot/`

You MUST work inside this repository.

Before making changes:

1. Inspect the current directory.
2. Inspect the existing Git status.
3. Inspect tracked and untracked files.
4. Inspect existing code and configuration.
5. Identify any useful existing implementation.
6. Identify potential conflicts with this specification.
7. Preserve existing user work.
8. Never delete unrelated files without necessity and clear justification.
9. Never execute destructive Git commands such as `git reset --hard`, `git clean -fd`, or force-push.
10. Never overwrite existing secrets or environment configurations.

If existing code is functional, integrate or improve it rather than automatically replacing it.

Do not initialize a new repository if `.git` already exists.

## 1.2 Mandatory technology stack

Frontend:

- React
- Vite
- JavaScript or TypeScript, with TypeScript strongly preferred
- Tailwind CSS
- Shadcn/ui
- React Router
- TanStack Query
- React Hook Form
- Zod
- Recharts
- Lucide React

Backend:

- Python
- Django
- Django REST Framework
- Django session authentication
- CSRF protection
- Django ORM
- Django migrations
- Django permissions and explicit role-based access controls

Telegram:

- Aiogram 3
- Telegram Bot API
- Inline keyboards
- Callback query handling
- FSM or equivalent persistent conversation state

Database:

- SQLite for the initial MVP
- Database architecture that allows migration to PostgreSQL

Background services:

- Redis
- Celery
- Redis-backed bot state when appropriate

Excel:

- openpyxl for XLSX generation and parsing
- ZIP processing for image archives

Additional libraries may be installed only when they provide a concrete benefit.

Use compatible, maintained versions and verify their current official documentation before implementation.

Avoid unnecessary framework proliferation.

## 1.3 Absolutely no Docker

DO NOT introduce:

- Dockerfiles
- docker-compose.yml
- Docker-based development assumptions
- Kubernetes dependencies
- Container-specific setup requirements

The target development environment is macOS.

Use native Python virtual environments, Node.js, Redis, and local processes.

Provide explicit commands for installing and running all services on macOS.

## 1.4 Required directory structure

Preserve the following top-level architecture:

```text
quiz_bot/
├── backend/
│   ├── config/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── quizzes/
│   │   ├── questions/
│   │   ├── attempts/
│   │   └── reports/
│   ├── manage.py
│   └── db.sqlite3
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   └── layouts/
│   └── package.json
│
├── bot/
│   ├── handlers/
│   ├── keyboards/
│   ├── middlewares/
│   └── main.py
│
├── .env.example
├── .gitignore
└── README.md
```

You may add files and appropriate subdirectories within this architecture.

Do not reorganize the agreed structure without a compelling technical reason.

Keep code modular.

Do not put all business logic in `views.py`, all frontend components in one file, or all Telegram handlers in `main.py`.

## 1.5 Language requirements

The user-facing application must use Uzbek as the default language.

Examples:

- Boshqaruv paneli
- Testlarim
- Yangi test
- Savollar
- O‘quvchilar
- Natijalar
- Reyting
- Hisobotlar
- Sozlamalar
- Testni boshlash
- Testni yakunlash
- Davom ettirish
- Parolni almashtirish

Use consistent Uzbek terminology throughout the application.

Avoid mixing Uzbek, Russian, and English in user-facing interface text unless an English term is a recognized technical term.

Structure frontend UI text so that future localization is possible.

Internal code identifiers, API paths, documentation for developers, and commit messages may use English.

---

# PART 2 — SOFTWARE ARCHITECTURE

## 2.1 Layered architecture

Implement distinct layers:

### Presentation layer

- React web interface
- Telegram chat interface

### API layer

- Django REST Framework
- Authentication and authorization
- Serializers
- Request validation
- Response formatting

### Service layer

Contains application business logic:

- Quiz publishing
- Access-code validation
- Attempt creation
- Answer submission
- Question navigation
- Time expiration
- Attempt completion
- Result calculation
- Ranking calculation
- Excel import
- Excel export

### Persistence layer

- Django ORM
- SQLite
- Database migrations
- Transaction handling

### Background processing

- Celery tasks
- Redis broker
- Idempotent scheduled operations

Business logic MUST NOT be duplicated between Telegram handlers and DRF views.

Telegram handlers and API views must call the same service functions where appropriate.

## 2.2 Django configuration

Organize settings clearly:

- Installed apps
- Database
- Static files
- Media files
- Session configuration
- CSRF
- CORS if genuinely needed
- Redis
- Celery
- Logging
- Telegram configuration
- Security configuration
- Development and production behavior

Use environment variables for secrets and environment-specific values.

Validate required environment variables at startup.

Do not hardcode tokens, passwords, secret keys, or production URLs.

Provide a comprehensive `.env.example` without real secrets.

## 2.3 Architecture decisions

Keep the application deployable with SQLite initially.

However, avoid assumptions that only one process will ever access the database.

Implement appropriate database transactions, constraints, and safeguards against duplicate answers.

Recognize that SQLite has limited write concurrency.

Do not claim SQLite is appropriate for arbitrarily high simultaneous examination traffic.

Document a realistic PostgreSQL migration strategy.

---

# PART 3 — AUTHENTICATION, USERS AND AUTHORIZATION

## 3.1 Roles

There are exactly three main platform roles:

1. `SUPER_ADMIN`
2. `TEACHER`
3. `STUDENT`

Super Admin and Teacher primarily use the web panel.

Student primarily uses Telegram.

A Student does not require web administrator access.

## 3.2 Custom User model

Create a custom Django User model before initial application migrations, if no existing model must be preserved.

Suggested fields:

- id
- username
- email
- first_name
- last_name
- role
- is_active
- is_staff
- is_superuser
- must_change_password
- last_login
- created_at
- updated_at

Use Django's password hashing framework.

Do not store plaintext passwords.

Do not rely on the `role` field alone for Django's superuser privileges.

Ensure the real Super Admin has appropriate Django permissions.

## 3.3 Student profile

Student-specific data:

- User reference or clearly defined identity model
- Telegram user ID
- Full name
- Telegram username, if available
- Registration date
- Account status

Telegram user ID must be unique for active student identity mapping.

Telegram usernames are optional and changeable.

Never use Telegram username as a secure primary identity.

Use Telegram's authenticated user ID from updates.

## 3.4 Teacher creation

Only Super Admin can create Teacher accounts.

The public application MUST NOT expose open Teacher registration.

Teacher creation fields:

- Full name
- Username
- Email
- Subject or specialty
- Account status

The UI must validate required fields and uniqueness.

The backend must independently validate everything.

## 3.5 Temporary password onboarding

When Super Admin creates a Teacher:

1. Generate a cryptographically secure temporary password.
2. Store only its secure password hash.
3. Set `must_change_password = true`.
4. Display the temporary password once in the admin UI.
5. Provide a copy button.
6. Never expose the temporary password again.
7. Never print the password in logs.
8. Never store it in localStorage or analytics.
9. Require the Teacher to change it during the first login.
10. Invalidate the temporary credential after password replacement.

Set an expiration policy for temporary credentials.

When temporary credentials expire, Super Admin must be able to issue a replacement.

## 3.6 First-login experience

Teacher visits `/login`.

After successful authentication:

- If `must_change_password` is true, redirect to `/change-password`.
- Do not allow access to the normal dashboard until the password is changed.
- Require a valid new password.
- Require confirmation.
- Use Django password validators.
- Reject weak passwords.
- Rotate the authenticated session appropriately after changing the password.

Never allow frontend-only enforcement of the password change requirement.

## 3.7 Login page

The login page must be beautifully designed and fully functional.

UI requirements:

- Logo and product name
- Welcome heading
- Login/email field
- Password field
- Show/hide password button
- Submit button
- Loading indicator
- Inline validation errors
- Authentication error message
- Keyboard accessibility
- Responsive layout
- Light/Dark support

Do not add a public Teacher sign-up form.

Display:

"Hisobingiz yo‘qmi? Administrator bilan bog‘laning."

## 3.8 Session authentication

Use Django session authentication and CSRF protection for web clients.

Implement:

- Login
- Logout
- Current-user endpoint
- CSRF bootstrap
- Session validation
- Password change
- Permission checks

Never disable CSRF globally.

Do not use `csrf_exempt` as a shortcut for the browser-facing authentication flow.

Prefer a same-origin production setup where Vite's compiled frontend is served behind the same site or reverse proxy as the API.

For local development, use a properly configured Vite proxy.

Avoid storing session secrets in JavaScript-accessible storage.

Configure secure cookie flags appropriately for HTTPS production.

## 3.9 Role-based access

Implement both role-based and object-level authorization.

Teacher may:

- Create quizzes.
- Edit their own quizzes.
- Add questions to their own quizzes.
- Import questions into their own quizzes.
- Publish their own quizzes.
- Close their own quizzes.
- Generate access codes for their own quizzes.
- See participants of their own quizzes.
- See results of their own quizzes.
- Export reports for their own quizzes.

Teacher may NOT:

- Manage other Teachers.
- View another Teacher's private quizzes.
- Modify another Teacher's quizzes.
- Access another Teacher's results.
- Export another Teacher's student results.
- Access global administration settings.

Super Admin may manage all platform records.

## 3.10 Critical object-level security

For every endpoint that accepts a quiz ID, question ID, attempt ID, report ID, or student ID:

1. Authenticate the user.
2. Check the user's role.
3. Check ownership or permitted scope.
4. Filter querysets at the database level where appropriate.
5. Return an appropriate denial when access is unauthorized.
6. Prevent unauthorized access through nested object references.

Example:

A Teacher must not retrieve another Teacher's quiz simply by changing `/api/quizzes/12/` to `/api/quizzes/13/`.

The same restriction applies to:

- Results
- Students
- Excel exports
- Generated report files
- Uploaded images where private visibility matters
- Quiz codes
- Question details

Add automated security tests for these cases.

---

# PART 4 — DESIGN SYSTEM AND UI/UX

## 4.1 Design direction

The approved design style is:

**Minimal SaaS Dashboard using Shadcn/ui.**

The application must feel polished, modern, consistent, and professional.

Do not produce a generic Bootstrap admin template.

Do not create a chaotic collection of unrelated components.

Design characteristics:

- Clean layout
- Minimal visual noise
- Comfortable spacing
- Clear typography
- Subtle borders
- Soft shadows
- Consistent iconography
- Neutral surfaces
- Carefully chosen accent color
- Strong content hierarchy
- Clear interactive states

## 4.2 Theme system

Support:

- Light mode
- Dark mode
- System preference detection

A ThemeToggle must be available in the header.

Persist the selected preference locally.

Avoid a flash of the wrong theme during initial rendering.

All components, charts, dialogs, tables, and notifications must support both themes.

Do not hardcode light-only colors.

Use design tokens and CSS variables.

## 4.3 Suggested visual tokens

Use a consistent token system rather than arbitrary values.

Suggested defaults:

- Primary accent: professional blue
- Background: neutral light/dark
- Cards: slightly elevated surface
- Border radius: approximately 10–16 px
- Sidebar width: approximately 248 px
- Header height: approximately 64 px
- Content max width: suitable for wide desktop dashboards
- Spacing: consistent 4/8/12/16/24/32 scale

Use semantic colors:

- Success: green
- Warning: amber
- Error: red
- Informational: blue

Colors must remain readable in both themes.

Do not use color alone to communicate status.

## 4.4 Typography

Use a modern, readable font that supports Uzbek Latin characters.

Ensure consistent:

- Heading scale
- Body text
- Table labels
- Form labels
- Helper text
- Error text
- Numeric statistics

Avoid excessively small text.

Use tabular numerals where appropriate for scores and statistics.

## 4.5 Primary layout

Approved layout:

**Sidebar + Header**

Desktop:

- Fixed or collapsible left sidebar
- Top header
- Main content region
- Breadcrumbs where appropriate
- Page actions on the right
- Content padding
- Consistent responsive grid

Mobile:

- Sidebar becomes a drawer
- Header contains menu trigger
- Touch-friendly controls
- Cards stack vertically
- Data tables use horizontal scrolling or responsive row presentations

## 4.6 Sidebar navigation

Super Admin:

- Dashboard
- O‘qituvchilar
- Testlar
- Savollar
- O‘quvchilar
- Guruhlar
- Natijalar
- Reyting
- Hisobotlar
- Sozlamalar

Teacher:

- Dashboard
- Testlarim
- Savollar
- O‘quvchilarim
- Natijalar
- Reyting
- Hisobotlar
- Profil

Show the current active navigation item clearly.

Use Lucide icons consistently.

Do not show unauthorized navigation items.

Backend authorization must still be enforced even when items are hidden.

## 4.7 Header

The header should include:

- Current page title or breadcrumb
- Theme toggle
- User avatar
- User dropdown
- Profile link
- Change password
- Logout

Do not add notification features unless there is a genuine implemented notification system.

Avoid decorative buttons with no working actions.

## 4.8 Shared component library

Build reusable components such as:

- AppShell
- Sidebar
- Header
- PageHeader
- ThemeToggle
- StatCard
- DataTable
- SearchInput
- FilterBar
- StatusBadge
- ConfirmDialog
- FormDialog
- EmptyState
- ErrorState
- LoadingSkeleton
- Pagination
- DateRangeFilter
- FileUpload
- ImagePreview
- QuestionEditor
- ResultSummary
- LeaderboardTable
- PasswordInput
- ProtectedRoute

Use Shadcn/ui foundations where appropriate.

Maintain a consistent component API.

## 4.9 Every page must implement UI states

Each data-driven page needs:

1. Initial loading state.
2. Successful data state.
3. Empty state.
4. No search results state.
5. API/network error state.
6. Permission denied state where relevant.
7. Action in progress state.
8. Successful action feedback.
9. Failed action feedback.

Do not leave empty white spaces during loading.

Use skeletons rather than distracting full-screen spinners when practical.

## 4.10 Forms

All forms must have:

- Associated labels
- Clear descriptions
- Validation
- Required-field indication
- Accessible focus states
- Disabled and loading states
- Submission feedback
- Server-side error mapping
- Unsaved changes protection where appropriate

Use React Hook Form + Zod.

Backend validation remains authoritative.

Do not submit forms twice when the button is clicked repeatedly.

## 4.11 Accessibility

Target WCAG 2.2 AA practices where feasible.

Ensure:

- Proper keyboard navigation
- Visible focus indicators
- Meaningful labels
- Semantic markup
- Accessible dialog focus management
- Appropriate contrast
- Screen-reader-friendly error text
- Accessible tables
- Touch targets large enough for mobile use
- Reduced-motion preferences respected

Do not implement clickable `div` elements where real buttons should be used.

## 4.12 Responsive testing

Validate at representative sizes:

- 360 px
- 390 px
- 768 px
- 1024 px
- 1280 px
- 1440 px

Check that:

- Text is readable.
- Controls do not overlap.
- Dialogs fit mobile screens.
- Tables remain usable.
- Header and sidebar do not cause layout overflow.
- Dark mode is visually complete.

---

# PART 5 — ADMIN AND TEACHER DASHBOARDS

## 5.1 Super Admin dashboard

Display real backend statistics:

- Total Teachers
- Active Teachers
- Registered Students
- Total Quizzes
- Active Quizzes
- Total Attempts
- Completed Attempts
- Recent Activity
- Average Performance

Include:

- KPI cards
- Activity line chart
- Recent quizzes table
- Recent attempts table
- Test status distribution
- Time period selector

Every statistic must use real data.

Empty database must display meaningful zero/empty states.

Do not use hardcoded example values in production.

## 5.2 Teacher dashboard

Display only data belonging to the authenticated Teacher.

KPIs:

- My Total Quizzes
- My Published Quizzes
- My Participants
- My Completed Attempts
- My Average Score

Include:

- Recent tests
- Recent student attempts
- Performance trends
- Most active quizzes
- Quick action: Create Quiz
- Quick action: Import Excel

## 5.3 Date filters

Support useful periods:

- Today
- Last 7 days
- Last 30 days
- Custom range

All date-based API filtering must respect a documented timezone strategy.

Prefer timezone-aware storage and explicitly defined display timezone.

---

# PART 6 — QUIZ MANAGEMENT

## 6.1 Quiz list page

Implement a functional quiz list.

Columns:

- Quiz title
- Subject
- Owner, for Super Admin
- Question count
- Duration
- Access type
- Status
- Participants
- Created date
- Actions

Actions:

- View
- Edit
- Duplicate
- Publish
- Close
- Archive
- View results
- Manage access code
- Delete, when allowed

Include:

- Search by name
- Filter by status
- Filter by subject
- Sort by date
- Pagination
- Loading and empty states

## 6.2 Quiz lifecycle

Statuses:

- Draft
- Published
- Closed
- Archived

Define valid status transitions.

Do not let invalid transitions occur.

Publishing must perform complete validation.

A quiz must not be published when:

- Required fields are missing.
- No questions exist.
- The specified number of questions exceeds available questions.
- A question has missing answer options.
- A question has no correct answer.
- The duration is invalid.
- The configured time window is invalid.

## 6.3 Quiz creation wizard

Use a three-step wizard:

**Step 1: Basic Settings**

Fields:

- Title
- Description
- Subject
- Duration
- Number of questions
- Passing score
- Maximum attempts
- Shuffle questions
- Shuffle answer options
- Navigation mode

**Step 2: Questions**

Options:

- Add manually
- Select from question bank
- Import Excel
- Reorder questions
- Remove questions
- Preview questions

**Step 3: Publishing**

Fields:

- Public/private access
- Access code settings
- Availability dates
- Result visibility
- Result publication timing
- Final preview
- Publish action

Provide an easy way to save a draft.

Preserve entered values when navigating between steps.

## 6.4 Quiz edit safety

Editing an active quiz must not silently change the meaning of existing attempts.

Implement an explicit strategy for quiz versioning or immutable attempt snapshots.

Recommended:

- Preserve question text, choices, correct answers, and scoring information used by each attempt.
- Existing attempts retain their original grading context.
- Changes apply to new attempts.

Clearly communicate this behavior in the UI.

Avoid deleting historical result data when a quiz is archived.

## 6.5 Quiz duplication

Duplicating a quiz should:

- Create a new draft.
- Copy its editable configuration.
- Copy or appropriately reference question content.
- Give it a distinct identity.
- Not copy students' attempts.
- Not copy result records.
- Not reuse access codes.

---

# PART 7 — QUESTIONS AND IMAGE MANAGEMENT

## 7.1 Question structure

Each standard question contains:

- Unique ID
- Text
- Optional image
- Four answer options
- Exactly one correct answer
- Score value
- Owner
- Creation and update timestamps

The first version focuses on single-correct-answer questions with A/B/C/D options.

Do not silently introduce multi-answer or essay question behavior.

## 7.2 Manual question editor

Provide:

- Question text area
- Optional image upload
- Image preview
- Remove image action
- A/B/C/D option fields
- Correct answer radio selection
- Point value
- Save
- Cancel
- Validation

The editor must work on mobile and desktop.

## 7.3 Question bank

Teachers can:

- View their own questions.
- Search by text.
- Filter by subject.
- Create questions.
- Edit their questions.
- Duplicate questions.
- Select questions for a quiz.
- Import questions.

Super Admin may view all questions.

A Teacher cannot modify questions owned by another Teacher.

## 7.4 Images

Support common safe raster formats such as:

- PNG
- JPEG
- WebP, if fully supported by the processing stack

Define maximum file size and pixel dimensions.

Validate the actual file content, not only the filename extension.

Reject corrupted, unsupported, or suspicious files.

Use randomized server-side file names.

Never trust a user-provided file path.

Do not allow uploaded files to become executable server content.

Store images in Django-managed media storage.

Handle missing image files gracefully.

## 7.5 Telegram image presentation

When a question includes an image:

- Send the image with the question caption when it fits Telegram limits.
- Otherwise send the image and question text in appropriately linked messages.
- Display A/B/C/D inline buttons.
- Preserve the association between the image, question, and current attempt.
- Handle image delivery failures without corrupting attempt state.

Do not reveal the correct answer in captions, file names, or callback data.

---

# PART 8 — EXCEL TEMPLATE AND IMPORT

## 8.1 Critical product requirement

The website MUST provide its own downloadable Excel question template.

The client downloads the template, fills it in, and uploads it back to the platform.

The importer must not assume the client already possesses a third-party template.

## 8.2 Template generation

Generate a real `.xlsx` file using openpyxl.

Suggested columns:

- Question
- Option A
- Option B
- Option C
- Option D
- Correct Answer
- Points
- Image File Name

Include:

- Clear header styling
- Example questions
- Instructions sheet
- Correct-answer validation where practical
- Column descriptions
- Supported image formats
- Maximum image size guidance

Define a version identifier for the template.

Document how incompatible templates are handled.

## 8.3 ZIP image import

Support a ZIP upload containing:

- One XLSX file
- Image files referenced by the XLSX

Example:

```text
questions.zip
├── questions.xlsx
└── images/
    ├── question_001.png
    ├── question_002.jpg
    └── question_003.png
```

The Excel file should reference the images by a documented relative name.

Do not trust ZIP file paths.

Prevent:

- Zip Slip path traversal
- Absolute path extraction
- Symlink abuse
- Excessive decompressed size
- Excessive file count
- Duplicate ambiguous filenames
- Unsupported extensions
- Unexpected nested archives

Use bounded extraction and validation.

## 8.4 Embedded Excel images

Also support images embedded directly in XLSX files.

Define a precise supported convention:

- Each embedded image must be anchored to an identifiable question row.
- Images must not be ambiguously placed across multiple questions.
- Supported formats must be documented.
- The importer must detect unsupported or ambiguous placements.

Do not depend on undocumented private library internals without justification and tests.

If an embedded image cannot be parsed reliably, return a row-specific validation error.

Do not silently drop images.

## 8.5 Import UI

Use an import dialog or dedicated import flow with three steps:

1. Upload
2. Preview and validation
3. Confirmation

Include:

- Download template button
- Upload XLSX button
- Upload ZIP button
- Drag-and-drop area
- File size information
- Validation progress
- Preview table
- Question count
- Image thumbnails
- Error list
- Row numbers
- Confirm import
- Cancel

## 8.6 Validation

Validate:

- File extension and signature
- XLSX validity
- Sheet name and columns
- Template version
- Question text
- Required options
- Correct answer value
- Point value
- Image references
- Embedded images
- Duplicate entries according to documented policy
- Maximum rows
- Maximum total file size

Do not execute Excel formulas or external content.

Treat spreadsheet content as untrusted input.

Avoid formula injection when later exporting user-controlled values.

## 8.7 Preview and confirm

Preview MUST NOT directly commit the entire import.

Recommended workflow:

- Parse and validate.
- Create a short-lived import session or safely staged data.
- Return preview and validation errors.
- Allow the user to confirm.
- Perform the final import atomically where practical.
- Prevent duplicate confirmation from creating duplicate records.
- Provide an import summary.

For initial MVP, all-or-nothing import is preferred.

If any blocking errors exist, do not import partial data silently.

## 8.8 Import ownership

An imported question must belong to the current Teacher.

A Teacher cannot import questions directly into another Teacher's quiz.

The backend must enforce this independent of frontend behavior.

---

# PART 9 — TELEGRAM BOT EXPERIENCE

## 9.1 Core principle

Students solve quizzes entirely inside normal Telegram chat.

Do NOT replace the quiz experience with:

- A Telegram Web App
- A separate website
- A browser-based examination page
- A Mini App

Telegram messages and inline keyboards are the primary student interface.

## 9.2 Main commands

Implement suitable commands:

- `/start`
- `/help`
- `/menu`
- `/continue`
- `/cancel`, only where appropriate

The exact available commands must be documented.

Do not let `/cancel` silently discard an active attempt.

## 9.3 Registration

On first `/start`:

1. Read Telegram authenticated user ID.
2. Check whether the Student already exists.
3. If not registered, request full name.
4. Validate the input.
5. Create Student identity.
6. Show success.
7. Display main menu.

On subsequent `/start`:

- Do not create a duplicate.
- Refresh non-sensitive Telegram profile fields if appropriate.
- Display main menu or a relevant active-test prompt.

Do not ask for phone number or unnecessary personal information.

## 9.4 Main menu

Provide:

- Ochiq testlar
- Test kodini kiritish
- Testni davom ettirish
- Natijalarim
- Reyting
- Profilim

Use Telegram inline or reply keyboards appropriately.

Keep navigation understandable.

## 9.5 Open quizzes

Display available public quizzes.

Each quiz should show:

- Title
- Duration
- Number of questions
- Attempts allowed or remaining
- Availability status

Support pagination if necessary.

Do not list unpublished or private quizzes.

## 9.6 Private quiz codes

A Student chooses "Test kodini kiritish".

Bot asks for the code.

Backend validates:

- Code format
- Code existence
- Active status
- Quiz status
- Start/end availability
- Attempt limits
- Any additional access restrictions

Return generic but useful error messages.

Avoid leaking whether guessed private quiz identifiers exist when not appropriate.

Apply rate limiting.

## 9.7 Quiz introduction

Before beginning, show:

- Quiz title
- Subject
- Question count
- Duration
- Navigation mode
- Attempt limit
- Important rules

Explain clearly:

- The timer continues if Telegram is closed.
- Answers are saved.
- The test ends when time expires.
- Early completion requires confirmation.
- Unanswered questions receive zero points.
- In sequential mode, previous answers cannot be changed.

Provide "Testni boshlash" and "Orqaga" actions.

---

# PART 10 — ATTEMPT ENGINE

## 10.1 Domain state machine

Use explicit attempt statuses such as:

- `in_progress`
- `completed`
- `timed_out`
- `cancelled` only if a genuine administrative cancellation flow exists

Define all valid transitions.

Prevent an attempt from being completed twice.

Do not allow a timed-out attempt to accept new answers.

## 10.2 Starting an attempt

When the Student confirms start:

1. Authenticate the Student via Telegram identity.
2. Validate quiz access.
3. Validate availability window.
4. Validate attempt limit.
5. Detect existing active attempt.
6. Create or return the appropriate active attempt.
7. Freeze the question set for that attempt.
8. Freeze question ordering.
9. Freeze answer option mappings.
10. Set `started_at`.
11. Calculate `deadline`.
12. Persist the attempt transactionally.
13. Send the first question.

Do not create multiple attempts because Telegram retries a callback.

Use idempotent start handling.

## 10.3 Sequential mode

This mode is selected by the Teacher when configuring a quiz.

Behavior:

- Show one question at a time.
- Show A/B/C/D buttons.
- Student selects one option.
- Save the answer.
- Advance automatically.
- Previous question cannot be reopened for modification.
- The old question's answer buttons become invalid.
- Repeated callbacks must not create multiple answers.

Do not reveal correctness after each question by default.

## 10.4 Free navigation mode

Also supported as a Teacher-configurable option.

Behavior:

- Show one question at a time.
- Show A/B/C/D buttons.
- Allow previous and next navigation.
- Preserve selected answers.
- Allow answer changes until attempt completion or deadline.
- Display progress.
- Allow unanswered questions.

Use a stable per-attempt mapping for shuffled options.

Never compare user-visible choice labels against a separately reshuffled answer key.

## 10.5 Telegram callback security

Callback payloads must not be blindly trusted.

Validate:

- Telegram user ID
- Attempt ownership
- Attempt status
- Question belongs to attempt
- Option belongs to question
- Deadline has not passed
- Navigation rules
- Callback freshness or version
- Idempotency

Use compact opaque identifiers or signed/validated payloads where appropriate.

Never expose correct answers in callback data.

## 10.6 Duplicate requests

Handle:

- Double button presses
- Telegram retries
- Slow network
- Callback arriving after next question
- Multiple devices belonging to the same Telegram account
- Concurrent answer attempts

Use database uniqueness constraints and transactional service logic.

For sequential mode, only one accepted answer should advance the cursor.

For free mode, define and enforce a consistent update policy until the deadline.

---

# PART 11 — TIMER AND RESUMABILITY

## 11.1 Server authority

The server is the sole authority for examination deadlines.

Do not trust:

- Client browser time
- Telegram message timestamp as the only authority
- Redis TTL as the only deadline source
- A countdown displayed in chat

Store deadline in the database.

Use timezone-aware timestamps.

## 11.2 Timer creation

At attempt start:

`deadline = started_at + duration`

If the quiz has a global closing time, define a consistent rule such as using the earlier of the individual deadline and the quiz closing time.

Document and test this rule.

## 11.3 Time checks

Before accepting an answer:

- Read attempt status.
- Compare authoritative server time with deadline.
- Reject answers submitted after deadline.
- Finalize the attempt when expired.
- Prevent double finalization.

## 11.4 Remaining time display

Display remaining time when:

- Test starts
- A question is sent
- The Student resumes
- Relevant navigation occurs

Do not edit Telegram messages every second.

Avoid excessive Telegram API calls.

Optional periodic warnings must be rate-limited and avoid duplicate messages.

## 11.5 Resume behavior

This behavior is APPROVED:

**Students resume where they left off; the timer never pauses.**

When `/continue` is invoked:

1. Identify the Student.
2. Find their active attempt.
3. Check the deadline.
4. If expired, finalize and show the permitted result.
5. Otherwise restore the current question.
6. Restore saved answers.
7. Restore question ordering.
8. Restore navigation state.
9. Display current remaining time.

The attempt must remain recoverable after:

- Bot restart
- Redis restart
- Telegram client restart
- Network disconnection

Redis is not the sole source of truth.

## 11.6 Time expiration behavior

This behavior is APPROVED:

**Grade answered questions; unanswered questions receive zero points.**

Example:

- Total questions: 20
- Correct: 12
- Incorrect: 3
- Unanswered: 5
- Equal weight per question
- Result: 12/20 = 60%

Store correct, incorrect, and unanswered counts separately.

Do not classify unanswered questions as incorrect in stored reporting, even though both earn zero points.

## 11.7 Celery expiration

Use Celery to process expired attempts.

Tasks must be:

- Idempotent
- Retry-safe
- Observably logged
- Safe when the attempt is already completed
- Safe when the deadline changes under an explicitly supported policy

Do not depend on a Celery task firing at the exact deadline to enforce timing.

The synchronous answer service must independently reject expired answers.

Use a periodic reconciliation mechanism to finalize missed expirations.

## 11.8 Early completion

This behavior is APPROVED:

**The Student may finish early, but confirmation is mandatory.**

Telegram flow:

Student presses "Testni yakunlash".

Bot displays:

"Testni yakunlamoqchimisiz? Javob berilmagan savollar uchun 0 ball beriladi. Yakunlangandan keyin testga qayta olmaysiz."

Buttons:

- Ha, yakunlash
- Yo‘q, davom etish

If confirmed:

- Finalize once.
- Preserve answered questions.
- Score unanswered as zero.
- Set completion status.
- Save finish timestamp.
- Calculate result.
- Return permitted result.

If cancelled:

- Resume current question.
- Do not reset timer.
- Do not alter existing answers.

In sequential mode, provide the early-completion action without enabling back navigation.

---

# PART 12 — RESULT CALCULATION

## 12.1 Scoring

For each attempt, store:

- Total questions
- Correct answers
- Incorrect answers
- Unanswered questions
- Earned points
- Maximum points
- Percentage
- Time spent
- Status
- Started timestamp
- Finished timestamp

Use precise numerical types for point calculations.

Avoid inconsistent floating-point calculations.

## 12.2 Percentage

Calculate:

`percentage = earned_points / maximum_points * 100`

When maximum points are zero, the quiz must not be publishable.

Define consistent rounding for display and ranking.

Store sufficient precision to rank accurately.

## 12.3 Approved default visibility

Every new quiz must default to:

```text
show_score = true
show_percentage = true
show_correct_count = true
show_incorrect_count = true
show_detailed_answers = false
show_ranking = true
result_release_mode = instant
```

Teachers may override these values per quiz.

## 12.4 Result release modes

Support:

- Instant: after attempt completion
- After quiz closes
- Manual Teacher release

Result release must be checked on the backend.

A Student must not access hidden result data by manipulating bot callbacks or API requests.

Teachers may see the detailed results for their own quizzes.

## 12.5 Telegram result message

Default result:

```text
✅ Test yakunlandi!

📘 Matematika — 1-variant

🎯 Ball: 18 / 20
📊 Natija: 90%

✅ To‘g‘ri: 18 ta
❌ Noto‘g‘ri: 2 ta
➖ Javobsiz: 0 ta

🏆 Reyting: 3-o‘rin

[Reytingni ko‘rish]
[Bosh menyu]
```

Display only fields allowed by that quiz's result settings.

Do not display a detailed answer-review button when detailed answers are disabled.

If result publication is delayed, show:

"Natijangiz saqlandi. Natijalar keyinroq e’lon qilinadi."

Do not leak hidden statistics through alternate commands.

## 12.6 Rank freshness

Explain that ranking positions can change when more Students finish.

Do not present a preliminary rank as permanently fixed.

---

# PART 13 — RANKING SYSTEM

## 13.1 Approved ranking types

Support both:

1. Per-quiz leaderboard
2. Overall leaderboard

## 13.2 Per-quiz leaderboard

Recommended rules:

- Consider completed and timed-out attempts that qualify as final results.
- Use the best eligible attempt per Student.
- Sort by percentage descending.
- Break ties by lower elapsed time.
- Use a deterministic final tie-breaker.

Clarify whether tied scores share displayed rank or use sequential positions; implement one policy consistently.

## 13.3 Overall leaderboard

For the initial implementation, use a documented MVP policy:

- Calculate each Student's best eligible attempt percentage per quiz.
- Average those percentages across eligible quizzes.
- Show the number of quizzes included.
- Keep the overall leaderboard distinct from an individual quiz leaderboard.

Teacher overall leaderboards must be scoped to that Teacher's quizzes.

Super Admin may view platform-wide leaderboards.

## 13.4 Comparability caveat

Do not claim that simple average percentage perfectly represents ability across quizzes of different difficulty.

Design the calculation as an isolated service so the policy can be changed later.

Document it transparently in the UI.

If minimum participation criteria are introduced, display them clearly and cover them with tests.

## 13.5 Ranking UI

Web leaderboard:

- Position
- Student
- Score/percentage
- Number of eligible quizzes
- Time spent where relevant
- Quiz filter
- Date filter
- Search
- Pagination
- Export

Telegram leaderboard:

- Compact top list
- Student's own position
- Student's own score
- Back button

Avoid exposing unnecessary personal information to other Students.

Where appropriate, use limited display names rather than full identity details in public rankings.

---

# PART 14 — STUDENT MANAGEMENT

## 14.1 Student list

Super Admin can view all Students.

Teacher can view only Students who participated in that Teacher's quizzes.

Fields:

- Full name
- Telegram username when available
- Participation count within permitted scope
- Average result within permitted scope
- Registration or first-participation date

Include search, filters, and pagination.

## 14.2 Student detail

Teacher profile view must display only the Teacher's own quiz-related attempts.

Do not include another Teacher's private test names or results.

Super Admin may view the whole student's history.

## 14.3 Groups

Provide group management compatible with the role model.

For the first version:

- Super Admin may create and manage groups.
- Teachers must not gain cross-owner visibility merely because a Student belongs to a group.
- Group membership does not override quiz ownership permissions.

If the existing project does not yet define full group enrollment behavior, implement a minimal, clearly documented group module without inventing automatic Teacher access.

Do not let an unfinished group feature compromise authorization boundaries.

---

# PART 15 — REPORTING AND EXCEL EXPORT

## 15.1 Report pages

Provide:

- Result listing
- Per-quiz report
- Student performance summary
- Leaderboard report
- Teacher activity report for Super Admin

## 15.2 Filters

Support:

- Quiz
- Date range
- Student
- Teacher for Super Admin
- Attempt status
- Minimum/maximum score where useful

## 15.3 Export format

Generate real `.xlsx` files using openpyxl.

Suggested columns:

- Student name
- Quiz title
- Teacher
- Attempt number
- Start time
- Finish time
- Duration
- Correct count
- Incorrect count
- Unanswered count
- Earned points
- Maximum points
- Percentage
- Rank
- Attempt status

Style exported workbooks professionally.

Include clear headings, appropriate number formatting, and column widths.

## 15.4 Export security

The export queryset MUST be scoped to the authenticated user's permissions.

Do not trust a frontend-supplied teacher ID to define authorization.

A Teacher must not export another Teacher's results.

Protect generated report files.

Do not create permanently public URLs for private report downloads.

## 15.5 Spreadsheet injection

When exporting user-controlled values, protect against spreadsheet formula injection.

Treat data beginning with spreadsheet formula trigger characters as potentially unsafe.

Use a consistent escaping policy.

## 15.6 Background exports

Small exports may be generated synchronously if safe.

Large exports should use Celery.

Provide:

- Job status
- Progress or status feedback
- Error handling
- Secure download
- Cleanup policy for old files

Do not make UI buttons appear successful before an export exists.

---

# PART 16 — REST API DESIGN

## 16.1 API conventions

Use:

`/api/`

Prefer consistent REST conventions.

Use appropriate HTTP methods and status codes.

Provide structured validation errors.

Use pagination on large collections.

Implement filtering and ordering consistently.

## 16.2 Authentication routes

Suggested endpoints:

```text
GET    /api/auth/csrf/
POST   /api/auth/login/
POST   /api/auth/logout/
GET    /api/auth/me/
POST   /api/auth/change-password/
```

## 16.3 Teacher routes

```text
GET    /api/teachers/
POST   /api/teachers/
GET    /api/teachers/{id}/
PATCH  /api/teachers/{id}/
POST   /api/teachers/{id}/reset-password/
POST   /api/teachers/{id}/deactivate/
POST   /api/teachers/{id}/activate/
```

Super Admin only.

## 16.4 Quiz routes

```text
GET    /api/quizzes/
POST   /api/quizzes/
GET    /api/quizzes/{id}/
PATCH  /api/quizzes/{id}/
POST   /api/quizzes/{id}/publish/
POST   /api/quizzes/{id}/close/
POST   /api/quizzes/{id}/duplicate/
POST   /api/quizzes/{id}/regenerate-code/
```

## 16.5 Question routes

```text
GET    /api/questions/
POST   /api/questions/
GET    /api/questions/{id}/
PATCH  /api/questions/{id}/
DELETE /api/questions/{id}/

GET    /api/questions/import/template/
POST   /api/questions/import/preview/
POST   /api/questions/import/confirm/
```

## 16.6 Student and result routes

```text
GET    /api/students/
GET    /api/students/{id}/
GET    /api/results/
GET    /api/results/{id}/
GET    /api/rankings/
GET    /api/dashboard/summary/
```

## 16.7 Reports

```text
POST   /api/reports/export/
GET    /api/reports/exports/
GET    /api/reports/exports/{id}/
GET    /api/reports/exports/{id}/download/
```

The final endpoint names may be refined to match Django REST Framework conventions, but document every change.

## 16.8 Bot integration

The Telegram Bot must invoke trusted backend service operations.

Prefer direct service integration when running inside the same trusted application environment rather than exposing unnecessary public bot-control endpoints.

If a separate internal HTTP interface is necessary, authenticate it robustly and restrict network exposure.

Never trust a client-supplied Student ID without independently validating the Telegram identity context.

---

# PART 17 — DATA MODEL DESIGN

Implement normalized, maintainable models.

## 17.1 accounts

- User
- StudentProfile
- TeacherProfile, if needed
- AuditLog, if placed here

## 17.2 quizzes

- Quiz
- QuizAccessCode
- QuizSettings
- Subject, if a separate model is justified

## 17.3 questions

- Question
- Choice
- QuizQuestion
- QuestionImage or appropriate media field, if needed

## 17.4 attempts

- Attempt
- AttemptQuestion
- AttemptAnswer

## 17.5 reports

- ReportExport

## 17.6 Database constraints

Enforce meaningful constraints such as:

- Unique Telegram identity
- Unique active code identity where appropriate
- Valid choice relationships
- One answer per attempt-question record
- Valid point values
- Valid attempt statuses
- Valid quiz statuses

Use database constraints in addition to serializer validation.

## 17.7 Referential integrity

Avoid accidental cascades that destroy historical exam data.

Define deletion behavior carefully.

Use archival or soft-deletion semantics where appropriate.

Do not silently delete completed attempt history when an associated quiz is removed from the visible UI.

## 17.8 Migration safety

Create proper Django migrations.

Do not edit migrations casually once applied.

Run migration checks.

Document how to initialize a clean database.

Keep `db.sqlite3` out of Git.

---

# PART 18 — SECURITY REQUIREMENTS

Security is a core deliverable, not an optional enhancement.

## 18.1 Threat model

Consider at least:

- Unauthorized Teacher access
- Broken object-level authorization
- Student impersonation
- Quiz-code guessing
- Session hijacking
- CSRF
- XSS
- File-upload abuse
- ZIP traversal
- Spreadsheet formula injection
- Data leakage through reports
- Answer leakage before completion
- Replay of Telegram callbacks
- Duplicate submissions
- Race conditions
- Timing manipulation
- Excessive login attempts
- Exposure of Redis
- Secrets in Git
- Sensitive data in logs

## 18.2 Password security

Use Django's standard secure password hashing.

Do not invent custom password hashing.

Do not expose plaintext passwords after initial one-time issuance.

Use Django password validation.

Rate-limit authentication.

## 18.3 CSRF and sessions

Use session cookies with secure production settings.

Protect state-changing browser requests with CSRF.

Set appropriate SameSite behavior.

Rotate sessions after sensitive authentication events.

Invalidate sessions for disabled accounts.

## 18.4 Authorization testing

Create automated tests proving:

- Teacher A cannot read Teacher B's quiz.
- Teacher A cannot edit Teacher B's question.
- Teacher A cannot export Teacher B's results.
- Teacher A cannot access Teacher B's report file.
- Student cannot access admin APIs.
- Unauthenticated requests are denied.
- Disabled Teacher access is denied.
- Frontend route protection is not the only security boundary.

## 18.5 Input handling

Validate input with serializers, Django forms where appropriate, and service-level rules.

Never trust:

- Query parameters
- JSON payloads
- Telegram callback data
- File names
- ZIP paths
- Excel content
- User-selected answer IDs
- Client-side timestamps

## 18.6 XSS prevention

Use React's default escaping.

Do not render arbitrary HTML from question text.

Avoid `dangerouslySetInnerHTML`.

If rich content is added, use strict sanitization and a deliberately limited format.

## 18.7 Secure media handling

Ensure:

- Media storage paths are safe.
- Private files are access-controlled.
- Images are validated.
- Filenames are randomized.
- Upload size is limited.
- Unsupported content is rejected.
- Uploaded files cannot execute on the server.

## 18.8 Telegram bot token

Store Telegram token in environment configuration.

Never print the token.

Never commit the token.

Do not expose it through frontend builds or browser API responses.

## 18.9 Redis security

Redis must not be publicly exposed.

Configure local binding and appropriate credentials where required.

Do not store unnecessary long-lived sensitive data in Redis.

Do not treat Redis state as authoritative for exam results.

## 18.10 Logging

Use structured, useful logs.

Never log:

- Passwords
- Temporary passwords
- Session cookies
- Bot tokens
- Raw authorization secrets

Avoid logging complete private quiz answer keys unnecessarily.

## 18.11 Rate limits

Rate-limit:

- Login
- Temporary password resets
- Quiz-code validation
- Telegram command spam
- Expensive report generation
- Import requests

Keep limits configurable.

## 18.12 Security headers

Configure suitable production headers including:

- HTTPS enforcement
- Secure cookies
- Content type protections
- Frame restrictions where appropriate
- Referrer policy
- Content Security Policy compatible with actual assets

Do not blindly copy a CSP that breaks the application.

Test the final configuration.

## 18.13 Dependency security

Avoid abandoned libraries.

Pin compatible dependency versions.

Use dependency auditing where available.

Document critical vulnerabilities discovered and how they were addressed.

## 18.14 Security acceptance

A feature is not complete until its authorization and input-validation boundaries are tested.

Do not mark the project production-ready while known high-severity vulnerabilities remain unresolved.

---

# PART 19 — FRONTEND ENGINEERING

## 19.1 React architecture

Organize code by feature.

Within `frontend/src`, include appropriate modules for:

- Authentication
- Dashboard
- Teachers
- Quizzes
- Questions
- Students
- Results
- Rankings
- Reports
- Settings

Preserve the agreed top-level frontend directories.

## 19.2 Routing

Use React Router with authenticated and role-restricted routes.

Suggested paths:

```text
/login
/change-password
/dashboard
/teachers
/teachers/new
/quizzes
/quizzes/new
/quizzes/:id
/quizzes/:id/edit
/questions
/students
/students/:id
/results
/results/:id
/rankings
/reports
/settings
/profile
```

Hide unauthorized routes from navigation and reject direct navigation appropriately.

The backend remains authoritative.

## 19.3 API client

Create one centralized API client.

Responsibilities:

- Credentials handling
- CSRF headers
- Error normalization
- Timeout handling
- Authentication failure handling
- Request cancellation where appropriate
- File upload support
- Secure file download support

Do not scatter raw fetch calls across every component.

## 19.4 Server state

Use TanStack Query.

Implement:

- Query keys
- Cache invalidation
- Loading states
- Error states
- Pagination
- Mutations
- Optimistic updates only where safe

Do not optimistically show a quiz as published before the backend validates publication.

## 19.5 UI forms

Use React Hook Form and Zod for:

- Login
- Password change
- Teacher creation
- Quiz creation
- Quiz settings
- Question editing
- Excel import confirmation

Avoid duplicated validation definitions where possible.

## 19.6 Error handling

Display understandable Uzbek messages.

Examples:

- "Majburiy maydonni to‘ldiring."
- "Login yoki parol noto‘g‘ri."
- "Ushbu testga kirish huquqingiz yo‘q."
- "Fayl formati qo‘llab-quvvatlanmaydi."
- "Savollar importida xatolik aniqlandi."
- "Internet bilan bog‘lanishda muammo yuz berdi."

Do not expose stack traces to users.

## 19.7 Performance

Implement:

- Route-based code splitting
- Efficient data table rendering
- Server-side pagination
- Reasonable query caching
- Optimized image loading
- Avoidance of unnecessary re-renders
- Minimal blocking JavaScript

Ensure dashboard performance is reasonable on ordinary laptops and phones.

---

# PART 20 — BOT ENGINEERING

## 20.1 Aiogram architecture

Separate:

- Main entry point
- Routers
- Handlers
- Keyboards
- Middlewares
- State definitions
- Bot services
- Message formatting
- Error handling

Avoid one giant handler file.

## 20.2 Telegram interface constraints

Telegram is not a browser.

Respect:

- Inline keyboard limitations
- Message length limits
- Media caption limits
- Callback data limits
- API rate limits
- Message edit restrictions
- Deleted messages
- Stale callbacks
- Connectivity interruptions

Do not build an interface that assumes HTML/CSS rendering inside Telegram messages.

## 20.3 Bot UX

Keep messages clear and concise.

Use consistent emoji sparingly.

Show:

- Quiz name
- Current question number
- Remaining time
- Answer options
- Navigation buttons when permitted
- Finish action
- Back/menu actions where safe

Avoid sending excessive redundant messages.

## 20.4 Bot error recovery

Gracefully handle:

- Telegram API failures
- Invalid callbacks
- Expired attempts
- Removed quizzes
- Temporarily unavailable backend
- Redis outages
- Missing media
- Student blocking the bot

Avoid crashing the entire bot because one message fails.

## 20.5 FSM and persistence

Use Redis for transient conversation state as appropriate.

Persist exam-critical data in Django models.

Make it possible to recover an attempt even if Redis state is lost.

---

# PART 21 — CELERY AND BACKGROUND TASKS

Implement:

- Expired-attempt reconciliation
- Large Excel export generation
- Cleanup of expired temporary imports
- Cleanup of old export files
- Other necessary background tasks

Make tasks idempotent.

Use bounded retries with backoff for transient failures.

Avoid retry loops for permanently invalid input.

Document worker and scheduler startup commands.

Do not run Celery worker operations that depend on interactive terminal input.

---

# PART 22 — TESTING STRATEGY

Testing is mandatory.

## 22.1 Backend unit tests

Test:

- Role permissions
- Password onboarding
- Quiz creation
- Quiz publishing validation
- Access codes
- Question validation
- Scoring
- Ranking
- Attempt state transitions
- Deadline calculations
- Early completion
- Excel parsing
- Embedded images
- ZIP import

## 22.2 Integration tests

Test:

- Teacher login and password change
- Teacher creates quiz
- Teacher imports questions
- Teacher publishes quiz
- Student registers through bot service
- Student starts attempt
- Student answers questions
- Student resumes after interruption
- Attempt expires
- Result is calculated
- Teacher exports report

## 22.3 Race condition tests

Test:

- Duplicate start requests
- Double answer callback
- Simultaneous answer requests
- Answer arriving at deadline
- Finish request racing with timeout
- Duplicate Celery expiration job
- Attempt resume racing with expiration

## 22.4 Security tests

Include explicit negative tests:

- Cross-Teacher access
- Unauthorized exports
- Invalid or manipulated callback IDs
- Expired quiz code
- Brute-force prevention
- Malicious ZIP paths
- Oversized uploads
- Invalid spreadsheet content
- Formula injection handling

## 22.5 Frontend tests

Use an appropriate React testing framework.

Test:

- Login validation
- Protected routes
- Teacher forms
- Quiz wizard
- Import preview
- Result visibility settings
- Dark mode
- Empty states
- Error states
- Confirmation dialogs

## 22.6 End-to-end tests

Where practical, use Playwright for critical web journeys.

Test at least:

1. Super Admin login.
2. Teacher creation.
3. Teacher first login.
4. Password change.
5. Quiz creation.
6. Question import.
7. Quiz publication.
8. Results display.
9. Excel export.

For Telegram, use service-level and mocked Bot API tests where real Telegram integration cannot be safely automated.

Never claim a live Telegram test passed unless it actually ran.

---

# PART 23 — USER EXPERIENCE QUALITY GATES

The project MUST NOT be considered complete merely because pages render.

Verify:

- Every navigation item works.
- Every button has a genuine purpose.
- Forms save to the backend.
- Refreshing the page preserves database-backed records.
- Search filters actual data.
- Pagination works.
- Import processes actual files.
- Reports generate actual XLSX files.
- Theme changes apply everywhere.
- Permissions remain enforced.
- Mobile layouts are usable.
- The Telegram bot can complete a real quiz end-to-end.

Remove placeholder content from production flows.

Seed/demo data, if provided, must be explicit and opt-in.

---

# PART 24 — PERFORMANCE AND RELIABILITY

## 24.1 Database performance

Add indexes for common queries:

- Quiz owner
- Quiz status
- Attempt Student
- Attempt Quiz
- Attempt status
- Attempt deadline
- Attempt creation time

Use `select_related` and `prefetch_related` appropriately.

Avoid N+1 query problems.

## 24.2 Pagination

Paginate:

- Teachers
- Students
- Quizzes
- Questions
- Attempts
- Reports

Do not return the entire database in one response.

## 24.3 Database transactions

Use transactions around:

- Attempt start
- Answer acceptance
- Attempt completion
- Score calculation
- Quiz import confirmation

Take SQLite concurrency limitations into account.

Do not depend on database locking features that SQLite does not support.

## 24.4 Backups

Document:

- SQLite backup procedure
- Media directory backup
- Restore procedure
- Environment variable preservation
- Migration procedure

Do not include actual secret files in distributable backups.

## 24.5 Observability

Add useful application logs for:

- Login errors
- Authorization denial
- Failed imports
- Failed background jobs
- Quiz publication
- Attempt finalization
- Report generation failures

Avoid logging sensitive data.

---

# PART 25 — DEPLOYMENT AND MACOS DEVELOPMENT

## 25.1 Local prerequisites

Document:

- Python version
- Node.js version
- Redis installation
- Python virtual environment
- Required Python packages
- Required npm packages

## 25.2 Startup instructions

Provide explicit commands to run:

1. Redis
2. Django backend
3. Celery worker
4. Celery Beat if used
5. Aiogram bot
6. Vite frontend

Ensure commands work from the intended directories.

## 25.3 Environment configuration

Provide `.env.example` containing names and safe example values for:

```text
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
DATABASE_URL=
REDIS_URL=
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
TELEGRAM_BOT_TOKEN=
PUBLIC_BASE_URL=
CSRF_TRUSTED_ORIGINS=
```

Adapt values to the actual implemented configuration.

Never put real credentials in `.env.example`.

## 25.4 Git ignore

Ensure `.gitignore` includes appropriate rules for:

- `.env`
- Python virtual environments
- Python bytecode
- Node modules
- Build output
- SQLite runtime database
- Local caches
- Sensitive logs
- Generated reports
- Temporary import files

Do not accidentally ignore source files or migrations.

## 25.5 Production readiness

Document:

- Django debug disabled
- Secure secret management
- HTTPS
- Secure cookies
- Correct allowed hosts
- Static file serving
- Protected media serving
- Redis protection
- Celery process management
- Bot process management
- Backup and restore
- Database migration
- Logging
- Security checks

The development environment is macOS without Docker.

Production deployment can be documented for a standard Linux server without making containerization mandatory.

---

# PART 26 — DOCUMENTATION

Create a genuinely useful README.

It must contain:

1. Project overview
2. Architecture
3. Tech stack
4. Directory structure
5. Installation requirements
6. Local macOS installation
7. Environment configuration
8. Database migration
9. Super Admin creation
10. Teacher onboarding
11. Redis startup
12. Celery startup
13. Bot startup
14. Frontend startup
15. Excel template format
16. Image import rules
17. Authentication model
18. Permissions model
19. Quiz lifecycle
20. Timer and resume rules
21. Scoring rules
22. Ranking rules
23. Testing commands
24. Production deployment notes
25. Troubleshooting

Include examples of expected commands and outcomes.

Do not document functionality that has not actually been implemented.

---

# PART 27 — IMPLEMENTATION PLAN

Do not attempt the entire platform as one undifferentiated code generation step.

Use controlled phases.

## Phase 0 — Repository audit

- Inspect repository.
- Check Git.
- Identify existing code.
- Identify security concerns.
- Record architecture assumptions.

## Phase 1 — Django foundation

- Django project configuration.
- Custom User.
- Role permissions.
- Authentication.
- Temporary password onboarding.
- Initial migrations.
- Initial tests.

## Phase 2 — React foundation

- Vite.
- Tailwind.
- Shadcn/ui.
- Routing.
- Theme system.
- Sidebar + Header.
- Login.
- Password change.
- API client.
- Protected routes.

## Phase 3 — Teacher management

- Teacher CRUD.
- Account activation/deactivation.
- Temporary password reset.
- Authorization tests.

## Phase 4 — Quiz and question management

- Quiz models.
- Question models.
- CRUD.
- Quiz wizard.
- Publishing.
- Duplication.
- Object-level permissions.

## Phase 5 — Excel and images

- Template generation.
- XLSX parsing.
- ZIP images.
- Embedded images.
- Preview.
- Validation.
- Confirm import.
- Security tests.

## Phase 6 — Telegram foundation

- Aiogram project.
- Bot commands.
- Student registration.
- Main menu.
- Quiz discovery.
- Private codes.

## Phase 7 — Examination engine

- Attempt model.
- Question snapshots.
- Sequential mode.
- Free navigation mode.
- Answer persistence.
- Callback validation.
- Duplicate request protection.

## Phase 8 — Timer and completion

- Deadline.
- Resume.
- Early finish confirmation.
- Time expiration.
- Celery tasks.
- Reconciliation.
- Scoring.

## Phase 9 — Results and rankings

- Result visibility.
- Release timing.
- Per-quiz ranking.
- Overall ranking.
- Telegram result messages.
- Web result tables.

## Phase 10 — Reporting

- Filtering.
- Analytics.
- XLSX export.
- Background exports.
- Secure downloads.

## Phase 11 — Hardening

- Security tests.
- UI accessibility.
- Responsive behavior.
- Error states.
- Performance.
- Production configuration.
- Documentation.

---

# PART 28 — IMPLEMENTATION EXECUTION RULES

You are expected to IMPLEMENT the software, not merely describe it.

For every phase:

1. Inspect relevant existing code.
2. State briefly what needs to be built.
3. Implement backend models/services/API.
4. Implement frontend or Telegram interfaces as applicable.
5. Wire the components together.
6. Add tests.
7. Run available validation commands.
8. Fix discovered errors.
9. Update documentation.
10. Report what is complete and what remains.

Do not treat compilation as proof of correctness.

Do not claim a feature works without appropriate verification.

## 28.1 No fake implementations

Forbidden shortcuts include:

- Hardcoded dashboard values presented as real.
- Mocked logins in the final application.
- Buttons that only display a toast without performing their stated operation.
- A static Telegram chat mockup instead of an Aiogram bot.
- Fake Excel import that only reads filenames.
- Fake download that does not return a valid XLSX.
- Fake ranking that sorts hardcoded Students.
- Timer implementation relying solely on a displayed countdown.
- Permission enforcement existing only in React.

## 28.2 Coding quality

Use:

- Clear naming
- Type annotations where useful
- Small focused functions
- Reusable services
- Predictable error handling
- Explicit transactions
- Consistent API contracts
- Maintainable component structure

Avoid:

- Giant files
- Circular dependencies
- Unnecessary abstraction
- Undocumented magic constants
- Duplicate business logic
- Hardcoded credentials
- Excessive dependencies

## 28.3 Error correction

When a command fails:

1. Read the error.
2. Diagnose the actual cause.
3. Make a targeted correction.
4. Retry validation.
5. Do not hide the failure.
6. Do not introduce insecure workarounds merely to make tests pass.

## 28.4 Environment limitations

If required services or dependencies cannot be installed in the current environment:

- Implement everything possible.
- Clearly report the blocker.
- Provide exact commands needed.
- Do not falsely claim runtime verification.
- Continue with independent tasks that do not require the unavailable service.

Do not erase or overwrite existing project data to make setup easier.

---

# PART 29 — REQUIRED ACCEPTANCE TEST SCENARIOS

The finished platform must satisfy at least these scenarios.

### Scenario A — Teacher onboarding

Super Admin creates Teacher → receives one-time temporary password → Teacher logs in → forced password change → dashboard becomes accessible.

### Scenario B — Unauthorized access prevention

Teacher A creates a quiz → Teacher B attempts to retrieve, edit, or export its results → API denies unauthorized access.

### Scenario C — Quiz creation

Teacher creates draft → adds valid questions → configures access and results → publishes quiz → quiz becomes available through intended Telegram workflow.

### Scenario D — Excel without images

Teacher downloads template → fills questions → uploads XLSX → preview validates → confirms → questions appear in the correct quiz.

### Scenario E — ZIP images

Teacher uploads XLSX + ZIP images → importer validates files and mapping → images are stored → Telegram displays the corresponding images.

### Scenario F — Embedded images

Teacher inserts images into supported XLSX positions → importer correctly associates each image with the intended question.

### Scenario G — Public quiz

Student registers → opens public quiz list → selects quiz → starts → answers → completes → sees permitted result.

### Scenario H — Private quiz

Teacher publishes private quiz → receives code → gives code to Student → Student enters code → quiz access is validated.

### Scenario I — Sequential navigation

Student answers a question → next question appears → old callback cannot alter prior answer.

### Scenario J — Free navigation

Student navigates backward → changes an answer within permitted time → final result uses the latest valid answer.

### Scenario K — Internet interruption

Student begins attempt → Telegram closes → bot restarts → Student returns → same attempt resumes → prior answers remain → deadline has not reset.

### Scenario L — Timeout

Student answers some questions → deadline passes → attempt finalizes → answered questions receive earned points → unanswered questions receive zero → no late answer is accepted.

### Scenario M — Early finish

Student presses Finish → confirmation appears → Cancel returns to attempt → Confirm finalizes exactly once.

### Scenario N — Result visibility

Teacher disables detailed answer review → Student completes quiz → scores are visible as configured → correct answer details are not disclosed.

### Scenario O — Rankings

Students complete quizzes → per-quiz and overall rankings update according to documented rules → Teacher sees only their permitted scope.

### Scenario P — Excel report

Teacher filters results → exports XLSX → file opens correctly → includes real authorized rows → cross-Teacher records are excluded.

### Scenario Q — Security

Malicious ZIP paths, unauthorized IDs, manipulated Telegram callbacks, expired codes, and oversized uploads are rejected safely.

### Scenario R — UI quality

Light and Dark mode work → mobile navigation works → forms validate → loading/empty/error states are correct → no critical button is inert.

---

# PART 30 — DEFINITION OF DONE

Do not declare the application complete until:

- All mandatory features are implemented.
- Frontend and backend communicate successfully.
- Aiogram bot uses real examination services.
- Database migrations run.
- Excel template generation works.
- Both image import methods work for documented supported formats.
- Timer and resume work correctly.
- Role and object permissions are enforced.
- Results and rankings are calculated consistently.
- Excel exports contain correct scoped data.
- Light and Dark mode work.
- Responsive layouts are verified.
- Critical security tests pass.
- Relevant automated tests pass.
- README contains accurate setup instructions.
- No known critical security vulnerabilities remain.
- Existing user files and Git work are preserved.

If anything remains incomplete, clearly state exactly what is missing.

Do not mark unverified features as completed.

---

# PART 31 — REQUIRED FINAL REPORT

After implementation, provide:

## A. Completed features

List exactly what is implemented.

## B. Changed files

Summarize important created and modified files.

## C. Database

List migrations and model relationships.

## D. API

List implemented endpoints.

## E. UI

Describe actual implemented pages and components.

## F. Telegram

Describe actual commands, handlers, and flows.

## G. Security

Report implemented controls and tests.

## H. Validation

Include the commands run and their results.

## I. Known limitations

Identify all remaining limitations honestly.

## J. How to run

Give exact macOS startup commands.

## K. Next recommended improvements

List non-blocking improvements only after mandatory requirements are satisfied.

---

# FINAL EXECUTION INSTRUCTION

You are building an actual integrated educational examination platform.

Prioritize, in order:

1. Correctness
2. Data integrity
3. Authorization and security
4. Reliability
5. UI/UX quality
6. Maintainability
7. Performance

Do not prioritize visual polish at the expense of security or functioning business logic.

Do not silently change approved requirements.

When a minor implementation detail is unspecified, choose a secure, simple, documented default.

Do not ask repetitive clarification questions about requirements already defined here.

**Begin by auditing the existing `quiz_bot` repository and then implement the project phase by phase.**

Continue through the planned phases as the execution environment permits, running tests and reporting verified results.

The final deliverable is a functional, secure, polished Quiz Bot platform — not a proposal, template, or demonstration.
