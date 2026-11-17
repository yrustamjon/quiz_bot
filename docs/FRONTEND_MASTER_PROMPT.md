# QUIZ BOT — FRONTEND MASTER PROMPT
## Premium SaaS UI/UX, Accessibility, Security & Production-Ready React Application

### YOUR ROLE

You are a Staff Frontend Engineer, Senior Product Designer, UI/UX Architect, Accessibility Specialist, Frontend Security Engineer, and Quality Assurance Engineer.

Your mission is to build an exceptionally polished, professional, accessible, responsive, and fully integrated frontend for the existing **Quiz Bot** platform.

This is not a design demonstration. This is a real educational SaaS administration platform used by Super Admins and Teachers.

Work inside the existing `quiz_bot/frontend/` directory. Preserve the existing Git repository, backend code, Telegram bot, and user files.

Treat the existing Quiz Bot MASTER IMPLEMENTATION PROMPT as the authoritative functional specification. This prompt adds strict frontend design and engineering requirements.

**A visually impressive interface with broken functionality is unacceptable. A working interface with poor UX is also unacceptable. Both must be excellent.**

---

# 1. APPROVED DESIGN DIRECTION

The design style is **Minimal Premium SaaS Dashboard**.

Mandatory technologies:

- React
- Vite
- TypeScript
- Tailwind CSS
- Shadcn/ui
- Radix UI primitives where appropriate
- Lucide React icons
- React Router
- TanStack Query
- React Hook Form
- Zod
- Recharts

Do not introduce another major UI framework such as Material UI or Ant Design.

Use Shadcn/ui consistently.

Create reusable, composable components rather than duplicated page-specific UI.

The visual result must feel like one coherent product, not several unrelated templates.

## 1.1 Visual identity

Working product name: Quiz Bot.

Style:

- Elegant
- Minimal
- Professional
- Clean
- Modern
- Education-focused
- Trustworthy
- Highly readable

Avoid:

- Excessive gradients
- Neon colors
- Large decorative illustrations
- Random background patterns
- Glassmorphism everywhere
- Unnecessary animations
- Inconsistent icon sizes
- Oversized cards
- Excessive whitespace that reduces usability
- Crowded dashboards

Use restraint and consistent visual hierarchy.

---

# 2. DESIGN TOKENS

Implement design tokens with CSS variables.

Use semantic tokens rather than arbitrary hardcoded colors throughout the application.

## 2.1 Light theme

Suggested starting palette:

- Background: `#F8FAFC`
- Main surface: `#FFFFFF`
- Secondary surface: `#F1F5F9`
- Primary text: `#0F172A`
- Secondary text: `#64748B`
- Primary accent: `#2563EB`
- Primary hover: `#1D4ED8`
- Border: `#E2E8F0`
- Success: `#16A34A`
- Warning: `#D97706`
- Destructive: `#DC2626`

## 2.2 Dark theme

Suggested starting palette:

- Background: `#09090B`
- Main surface: `#18181B`
- Secondary surface: `#27272A`
- Primary text: `#FAFAFA`
- Secondary text: `#A1A1AA`
- Primary accent: `#3B82F6`
- Border: `#3F3F46`
- Success: `#22C55E`
- Warning: `#F59E0B`
- Destructive: `#EF4444`

Refine the exact palette to meet contrast and usability requirements.

Do not blindly use these colors without checking contrast.

## 2.3 Spacing and dimensions

Establish a predictable spacing system.

Recommended:

- Sidebar: 248 px expanded
- Collapsed sidebar: 68–72 px
- Header: 64 px
- Main page padding: 24–32 px on desktop
- Mobile page padding: 16 px
- Standard card radius: 12 px
- Dialog radius: 14 px
- Input/control height: 40–44 px
- Touch targets: approximately 44 px minimum where feasible
- Table row height: 48–56 px
- Main content max-width: approximately 1440 px

Use an 8-point-oriented spacing scale with consistent smaller increments.

Avoid arbitrary dimensions.

## 2.4 Typography

Choose a modern sans-serif font supporting Uzbek Latin characters.

Use a consistent type scale:

- Main page title
- Section heading
- Card heading
- Body
- Caption
- Form helper text

Avoid 10 px primary content text.

Use tabular numerals for:

- Scores
- Percentages
- Statistics
- Rankings
- Durations

Ensure long test names wrap or truncate gracefully.

---

# 3. APPLICATION SHELL

The approved layout is:

**Sidebar + Header**

## 3.1 Desktop sidebar

The sidebar must:

- Display Quiz Bot branding.
- Show appropriate navigation for the current role.
- Indicate active route.
- Support collapsed state.
- Display useful tooltips when collapsed.
- Maintain consistent icon alignment.
- Handle long labels.
- Remain visually balanced.
- Preserve scroll position where appropriate.

Super Admin menu:

1. Dashboard
2. O‘qituvchilar
3. Testlar
4. Savollar
5. O‘quvchilar
6. Guruhlar
7. Natijalar
8. Reyting
9. Hisobotlar
10. Sozlamalar

Teacher menu:

1. Dashboard
2. Testlarim
3. Savollar
4. O‘quvchilarim
5. Natijalar
6. Reyting
7. Hisobotlar
8. Profil

Do not expose forbidden routes in the UI.

## 3.2 Header

The header must contain:

- Breadcrumb or current page context
- Relevant page actions
- Theme toggle
- User avatar
- Account dropdown
- Profile
- Change password
- Logout

Use a compact, professional appearance.

Do not add fake notification controls.

## 3.3 Mobile sidebar

At mobile widths:

- Hide the permanent sidebar.
- Show a menu button.
- Open navigation in an accessible Sheet/Drawer.
- Close after navigation.
- Prevent background scrolling while open.
- Ensure correct keyboard focus and escape behavior.

## 3.4 Responsive breakpoints

Test at:

- 360 px
- 390 px
- 768 px
- 1024 px
- 1280 px
- 1440 px
- 1920 px

There must be no unintended horizontal scrolling of the entire page.

Wide tables may scroll within their own containers.

---

# 4. USER EXPERIENCE PRINCIPLES

## 4.1 Every action must work

All visible controls must be functional.

Examples:

- Create Quiz creates a real draft.
- Publish Quiz sends the real API request.
- Download Template returns a valid XLSX file.
- Import Questions parses a real uploaded file.
- Export Results generates an actual report.
- Theme toggle updates the theme.
- Search filters real data.
- Filters update backend queries.
- Logout invalidates the session.

Never build decorative buttons that do nothing.

## 4.2 Predictable feedback

Every mutation should clearly communicate:

- Processing
- Success
- Failure
- Validation errors

Use consistent toast notifications.

A toast must not replace a proper error state when a user needs to correct specific fields.

## 4.3 Empty states

Build meaningful empty states.

Examples:

No quizzes:

"Hoziroq birinchi testingizni yarating."

No results:

"Hozircha ushbu test bo‘yicha natijalar mavjud emas."

No matching search:

"Qidiruvga mos ma’lumot topilmadi."

Each empty state should offer an appropriate next action when possible.

## 4.4 Loading states

Use Shadcn Skeleton components.

Avoid blocking the entire screen for ordinary background requests.

Buttons should indicate mutation progress.

Prevent duplicate submissions.

## 4.5 Error states

Handle:

- Network failure
- Server error
- Validation failure
- Authentication expiration
- Permission denied
- Missing resource
- File upload failure
- Import validation failure
- Report generation failure

Present understandable Uzbek messages.

Never display raw exception traces in production.

## 4.6 Unsaved changes

Protect users from accidentally losing unsaved forms.

Use navigation confirmation for important unsaved changes.

Do not show confirmation when there is nothing to lose.

---

# 5. AUTHENTICATION UI

## 5.1 Login page

Create a premium, minimal login experience.

Desktop:

- Balanced centered layout or tasteful split layout.
- Compact branding.
- Clear title.
- Login/email input.
- Password input.
- Show/hide password control.
- Submit button.
- Error display.

Mobile:

- Single column.
- Comfortable padding.
- Proper keyboard behavior.
- No horizontal overflow.

Default user-facing language: Uzbek.

Do not expose public Teacher registration.

## 5.2 Login interactions

Implement:

- Controlled form validation
- Keyboard submission
- Loading state
- Disabled repeated submit
- Invalid credentials message
- CSRF bootstrap
- Secure session handling
- Role-aware redirect

## 5.3 First-login password change

If `must_change_password = true`:

- Redirect to mandatory password-change page.
- Explain why password replacement is required.
- Display new password and confirmation.
- Provide password-strength guidance.
- Show server validation errors.
- Block unauthorized access to other app routes until completed.

Do not allow route manipulation to bypass the backend requirement.

## 5.4 Authentication expiration

If a session expires:

- Clear sensitive cached application data.
- Show a friendly notification.
- Redirect to login.
- Preserve a safe return destination when appropriate.

Never leak cached data across different users.

---

# 6. DASHBOARD UI

## 6.1 Visual hierarchy

Dashboard order:

1. Page heading and welcome context.
2. Primary KPI cards.
3. Performance chart.
4. Recent quizzes.
5. Recent attempts/activity.
6. Useful quick actions.

Use a responsive grid.

Avoid displaying too many competing cards.

## 6.2 KPI cards

Each card should have:

- Clear title
- Prominent number
- Small relevant icon
- Optional contextual trend
- Helpful tooltip where necessary

Do not fabricate trend indicators if the backend does not provide comparison data.

## 6.3 Charts

Use Recharts.

Charts must have:

- Accessible labels
- Clear axis values
- Meaningful tooltips
- Loading states
- Empty-data states
- Dark-mode support
- Responsive sizing

Do not render misleading charts with fake values.

## 6.4 Date filters

Support:

- Today
- 7 days
- 30 days
- Custom period, where available

Keep the selected date range consistent across relevant dashboard components.

---

# 7. TEACHER MANAGEMENT UI

Only Super Admin can access Teacher management.

## 7.1 Teacher list

Provide:

- Search
- Status filter
- Pagination
- Table
- Create Teacher action
- View Teacher details
- Activate/deactivate actions

Suggested columns:

- Teacher name
- Username
- Email
- Subject
- Quiz count
- Status
- Created date
- Actions

## 7.2 Create Teacher form

Fields:

- Full name
- Username
- Email
- Subject

Use clear validation.

After creation, display temporary password in a secure one-time dialog.

## 7.3 Temporary password dialog

Must contain:

- Teacher name
- Temporary password
- Copy button
- Security warning
- Confirmation action

Explain:

"Ushbu parol faqat bir marta ko‘rsatiladi. Uni o‘qituvchiga xavfsiz usulda yetkazing."

Do not render temporary passwords in tables.

Do not preserve them in browser storage.

## 7.4 Deactivation

Before deactivating a Teacher:

- Show confirmation.
- Explain access consequences.
- Require explicit action.
- Update backend state.
- Refresh UI.

Ensure existing sessions become invalid.

---

# 8. QUIZ LIST UI

Create a full-featured, professional data table.

Columns:

- Test name
- Subject
- Questions
- Duration
- Access type
- Status
- Participants
- Created date
- Actions

Teacher sees only owned quizzes.

Super Admin sees all authorized quizzes.

## 8.1 Filters

Support:

- Text search
- Subject
- Status
- Access type
- Date ordering

Filters should be resettable.

Support URL query parameters where useful so views can be bookmarked.

## 8.2 Row actions

Use an accessible dropdown menu:

- View
- Edit
- Duplicate
- Publish
- Close
- Results
- Access Code
- Archive

Destructive operations require confirmation.

## 8.3 Status presentation

Use consistent status labels:

- Qoralama
- Faol
- Yopilgan
- Arxivlangan

Do not rely on badge color alone.

---

# 9. QUIZ CREATION WIZARD

This is one of the most important UI components.

Make the workflow exceptionally clear.

## 9.1 Step indicator

Show:

1. Asosiy sozlamalar
2. Savollar
3. Nashr qilish

Indicate:

- Current step
- Completed steps
- Validation errors
- Remaining steps

## 9.2 Navigation

Provide:

- Oldingi
- Keyingi
- Qoralama sifatida saqlash
- Bekor qilish
- Nashr qilish

Preserve form values across steps.

Do not silently lose changes.

## 9.3 Step 1 — Basic Settings

Fields:

- Test title
- Subject
- Description
- Duration
- Question count
- Passing score
- Attempt limit
- Shuffle questions
- Shuffle options
- Navigation mode

Use appropriate input types.

Numeric fields must have validation and sensible boundaries.

### Navigation mode

Two choices:

**Ketma-ket**

"Javob berilgach keyingi savol ochiladi. Oldingi savolga qaytib bo‘lmaydi."

**Erkin**

"Oldingi va keyingi savollarga o‘tish, javoblarni o‘zgartirish mumkin."

Use radio cards or another clearly understandable selection component.

## 9.4 Step 2 — Questions

Present:

- Question list
- Question count
- Add Question
- Select from Bank
- Import Excel
- Reorder
- Edit
- Delete from quiz
- Question preview

Indicate whether each question is valid.

When publishing, show missing requirements clearly.

## 9.5 Step 3 — Publishing

Provide:

- Public/private access selection
- Private code display when available
- Availability dates
- Result visibility configuration
- Result release timing
- Final quiz summary
- Validation checklist
- Publish button

## 9.6 Publish validation

If publishing fails, show specific actionable errors.

Examples:

"Testda kamida bitta savol bo‘lishi kerak."

"3-savolda to‘g‘ri javob belgilanmagan."

"Test davomiyligi noto‘g‘ri kiritilgan."

Avoid generic "Something went wrong" messages.

---

# 10. RESULT VISIBILITY SETTINGS UI

Each quiz has independently configurable settings.

Default:

- Show score: ON
- Show percentage: ON
- Show correct count: ON
- Show incorrect count: ON
- Show detailed answers: OFF
- Show ranking: ON
- Release results immediately

Use accessible switches or checkboxes.

Show a live Telegram-style preview of the result message.

The preview must reflect the current selected settings.

Result release options:

- Test tugashi bilan
- Testning umumiy muddati tugagach
- O‘qituvchi e’lon qilgandan keyin

Clearly explain each option.

Do not imply students can view results when release is disabled.

---

# 11. QUESTION EDITOR UI

Build a reusable QuestionEditor.

Fields:

- Question text
- Image upload
- Image preview
- Option A
- Option B
- Option C
- Option D
- Correct option
- Points

## 11.1 Correct answer selection

Use a radio group.

Only one correct answer is allowed.

Clearly highlight the selected correct answer.

Do not use four independent checkboxes.

## 11.2 Image interactions

Support:

- Drag-and-drop
- File picker
- Preview
- Remove
- Replace
- Validation errors

Show supported formats and maximum size.

Avoid broken image previews.

## 11.3 Save behavior

Provide:

- Save
- Save and add another, where useful
- Cancel

Do not close the editor when validation fails.

---

# 12. EXCEL IMPORT EXPERIENCE

The website generates the official template.

The workflow must be intuitive even for non-technical Teachers.

## 12.1 Import dialog

Design a three-step flow:

1. Fayl yuklash
2. Tekshirish
3. Tasdiqlash

## 12.2 Step 1 — Upload

Display:

- Download XLSX Template
- Upload XLSX
- Upload ZIP with images
- Drag-and-drop zone
- Supported file formats
- File size limitations

Clearly describe the two image methods:

**Excel ichidagi rasmlar**

Images placed directly in supported XLSX cells/anchors.

**Excel + ZIP**

Question images referenced by filename inside a ZIP archive.

## 12.3 Step 2 — Preview

Show:

- Total questions
- Valid questions
- Invalid questions
- Image count
- Question preview table
- Image thumbnails
- Errors grouped by row

Validation errors must be clear and actionable.

Example:

"8-qator: To‘g‘ri javob A, B, C yoki D bo‘lishi kerak."

## 12.4 Step 3 — Confirm

Show:

- Total records to import
- Target quiz
- Warnings
- Confirmation button

Avoid accidental duplicate imports.

After success:

- Show imported count.
- Refresh question list.
- Provide a link to the target quiz.

## 12.5 Error recovery

If import fails:

- Preserve useful preview information.
- Show exact errors.
- Allow corrected file re-upload.
- Avoid partially imported records unless explicitly supported.

---

# 13. STUDENT MANAGEMENT UI

Teacher must see only Students who participated in their quizzes.

Student list:

- Search
- Quiz filter
- Student name
- Participation count
- Average score
- Last activity

Student detail:

- Name
- Relevant attempts
- Relevant results
- Performance chart where meaningful

Super Admin may access the broader Student view.

Do not disclose another Teacher's results.

---

# 14. RESULTS UI

Build a high-quality result management page.

## 14.1 Main table

Columns:

- Student
- Quiz
- Correct answers
- Incorrect answers
- Unanswered
- Score
- Percentage
- Time spent
- Status
- Date

## 14.2 Filtering

Support:

- Quiz
- Date range
- Student name
- Result status

## 14.3 Detail view

Show:

- Student
- Quiz
- Attempt summary
- Score
- Percentage
- Start/end time
- Duration
- Per-question breakdown for authorized Teacher users

Use readable cards and tables.

Do not overwhelm the page.

## 14.4 Export

Provide a functional Excel export button.

Show progress and errors.

Never claim export succeeded before receiving a valid file or completed export job.

---

# 15. RANKING UI

Two ranking views:

- Test reytingi
- Umumiy reyting

Use clear tabs.

Leaderboard columns:

- Rank
- Student
- Percentage
- Eligible quiz count, where relevant
- Time spent, for per-test ranking

Highlight top positions tastefully.

Do not overuse oversized medals.

Explain the ranking calculation with a tooltip or help text.

Teacher views must be scoped to owned quizzes.

---

# 16. REPORTS UI

Provide a reporting workspace.

Features:

- Report type selection
- Quiz filter
- Date range
- Result preview
- Export XLSX
- Export status
- Secure download

Use visual summaries where genuinely helpful.

Avoid redundant charts.

---

# 17. PROFILE AND SETTINGS UI

Teacher profile:

- Full name
- Username
- Email
- Subject
- Change password

Super Admin settings:

- Relevant platform configuration
- Teacher management shortcuts
- Security settings as implemented

Do not expose secret tokens through the frontend.

Do not create dummy settings that are not backed by actual server functionality.

---

# 18. RESPONSIVE TABLE DESIGN

Large tables require special care.

On desktop:

- Full column layout
- Sort controls
- Pagination
- Filters
- Row actions

On tablets:

- Reduced less-important columns where appropriate
- Horizontal scroll for important columns

On phones:

- Responsive row cards or scrollable table
- Clear primary actions
- No impossible-to-tap controls

Do not force all columns into a narrow viewport.

---

# 19. MICROINTERACTIONS

Use subtle transitions.

Good examples:

- Sidebar collapse
- Theme transition
- Dropdown opening
- Button hover
- Dialog entrance
- Skeleton loading
- Success feedback

Respect reduced-motion preferences.

Avoid complex page animations.

Avoid animations that delay normal actions.

---

# 20. FRONTEND SECURITY

## 20.1 Authentication

Use secure Django session authentication.

Never store passwords or session secrets in localStorage.

Handle CSRF correctly.

## 20.2 Authorization

Use ProtectedRoute for frontend routing.

Also rely on backend permission checks.

Never assume hiding a button secures an endpoint.

## 20.3 Sensitive data

Do not leak:

- Temporary Teacher passwords
- Quiz answer keys
- Private reports
- Other Teachers' data
- Bot tokens
- Server secrets

Clear sensitive query caches on logout.

## 20.4 Uploads

Validate file size and extension in the UI for convenience.

Do not rely on frontend validation for security.

Backend must independently enforce all limits.

## 20.5 XSS

Render question text safely.

Do not render arbitrary HTML.

Avoid dangerous HTML injection patterns.

---

# 21. ACCESSIBILITY REQUIREMENTS

Target WCAG 2.2 AA where feasible.

Verify:

- Keyboard access to all controls.
- Visible focus outlines.
- Correct accessible names.
- Input labels.
- Semantic tables.
- Dialog focus trapping.
- Escape-key behavior.
- Accessible validation errors.
- Sufficient contrast.
- Mobile touch target sizes.
- Screen-reader announcements for important state changes.

Do not treat accessibility as optional polish.

---

# 22. QUALITY ASSURANCE

## 22.1 Visual verification

Inspect the application at representative viewport widths.

Verify both Light and Dark themes.

Check for:

- Overlapping elements
- Unreadable text
- Inconsistent spacing
- Broken cards
- Modal overflow
- Table clipping
- Misaligned icons
- Incomplete hover states
- Inconsistent form styles
- Unintended horizontal scrolling

Fix issues before declaring completion.

## 22.2 Functional verification

Every visible control must be tested.

Test real flows:

- Login
- Logout
- Password change
- Teacher creation
- Quiz creation
- Quiz editing
- Quiz publishing
- Question management
- Excel import
- Results filtering
- Ranking
- Excel export

## 22.3 Automated testing

Use suitable tools such as:

- Vitest
- React Testing Library
- Playwright

Test:

- Authentication routing
- Form validation
- Protected routes
- Theme preference
- Quiz wizard
- Import preview
- Result settings
- Data table filters
- Error states
- Accessibility-critical interactions

## 22.4 Performance

Aim for:

- Reasonable initial bundle size
- Route-based code splitting
- Efficient rendering
- Stable layouts
- Responsive interactions
- Avoidance of unnecessary network requests

Do not blindly optimize before measuring.

---

# 23. FRONTEND DEVELOPMENT WORKFLOW

Implement in stages.

### Stage 1 — Foundation

- Inspect existing frontend.
- Configure TypeScript.
- Configure Tailwind.
- Configure Shadcn/ui.
- Set design tokens.
- Implement theme management.
- Implement React Router.
- Implement API client.

### Stage 2 — Application Shell

- Sidebar
- Header
- Responsive navigation
- User menu
- Breadcrumbs
- Protected layouts

### Stage 3 — Authentication

- Login
- First-login password change
- Session handling
- Permission-based redirects

### Stage 4 — Dashboards

- Super Admin dashboard
- Teacher dashboard
- Statistics
- Charts
- Real API integration

### Stage 5 — Teacher Management

- Teacher list
- Create form
- Temporary password dialog
- Activation/deactivation

### Stage 6 — Quiz Management

- Quiz list
- Quiz creation wizard
- Quiz settings
- Quiz publishing
- Quiz duplication
- Quiz details

### Stage 7 — Question Management

- Question bank
- Question editor
- Image management
- Excel import workflow

### Stage 8 — Students and Results

- Students list
- Student profile
- Results
- Ranking
- Reports

### Stage 9 — Quality and Hardening

- Full responsive review
- Light/Dark verification
- Accessibility audit
- Functional testing
- Error handling
- Performance review

---

# 24. AUTONOMOUS EXECUTION AND RECOVERY

Follow the project's persistent progress-tracking protocol.

Maintain a progress file indicating:

- Completed frontend stages
- Remaining stages
- Verified UI components
- Tests executed
- Known blockers
- Exact next task

Work incrementally.

After each meaningful stage:

1. Run TypeScript checks.
2. Run linting.
3. Run relevant tests.
4. Run production build.
5. Fix errors.
6. Update progress tracking.
7. Continue when the environment permits.

If browser automation or screenshot inspection is available, use it.

Do not claim visual verification when no real rendering was inspected.

If a backend endpoint is unavailable, document the dependency and continue with independent frontend work without presenting mock data as a finished integration.

Do not overwrite backend or bot code unless a necessary API contract change has been coordinated.

---

# 25. FRONTEND DEFINITION OF DONE

Frontend is complete only when:

- Every required page exists.
- Every page follows the approved design system.
- Light mode works fully.
- Dark mode works fully.
- Sidebar + Header work.
- Mobile navigation works.
- Login works with Django.
- Teacher onboarding works.
- Role permissions are respected.
- Quiz CRUD is functional.
- Quiz wizard works.
- Question management works.
- Excel import workflow works.
- Results use real data.
- Rankings use real data.
- Report export works.
- All important actions provide meaningful feedback.
- Loading, empty, and error states are implemented.
- Keyboard navigation works.
- Accessibility checks are performed.
- Automated tests pass.
- Production build succeeds.
- No critical broken UI remains.

**Do not stop at "looks good." Verify that it actually works.**

---

# FINAL INSTRUCTION

Create a production-quality frontend for Quiz Bot that looks and behaves like a polished, professionally designed SaaS product.

The frontend must be:

- Beautiful
- Minimal
- Consistent
- Responsive
- Accessible
- Secure
- Fast
- Maintainable
- Fully integrated with Django
- Reliable for real Teachers and Super Admins

Build it systematically, verify every major workflow, and fix defects.

Never sacrifice security or functionality for superficial appearance.

**Start by inspecting the current `frontend/` directory, identify what already exists, and continue implementation without unnecessarily replacing working code.**