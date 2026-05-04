# marathakalyanam — engineering guide

Matrimonial site for Telugu-Maratha people settled in Andhra Pradesh and Telangana.
Production domain: **marathakalyanam.com**.

**Tech stack:** Python (Litestar/async) · SQLAlchemy 2.x · PostgreSQL 16 · SvelteKit (Svelte 5)
· Tailwind CSS v4 · Pillow + OpenCV for photo processing.

## Repo layout

```
backend/                       Async Python, Litestar ASGI framework
  app/
    main.py                    Litestar app entry, ASGI + route registration
    config.py                  Bootstrap config from .env (DB URL, session secret)
    db.py                      AsyncSessionLocal, async engine, session dependency
    models/
      base.py                  Declarative base
      user.py                  User model: email, full_name, phone_number, password_hash, email_verified
      profile.py               Profile model: demographics, astrology, status
      photo.py                 Photo model: passport/blurred/thumb variants
      request.py               DetailRequest model: requester → profile
      setting.py               Setting model: runtime config (SMTP, limits, etc.)
    routes/
      auth.py                  POST /auth/{register|login|logout|verify-email}
      profiles.py              CRUD + submit (draft → pending/approved)
      photos.py                POST /profiles/{id}/photos, DELETE, GET
      search.py                GET /search with filters (gender, age, gotra, etc.)
      requests.py              POST /profiles/{id}/request, GET /requests
      admin.py                 Admin: profiles, requests, users, settings, stats
      media.py                 GET /media/* for passport/blurred/thumb files
    schemas/                   msgspec request/response models (typed)
    services/
      auth.py                  Hash/verify password (bcrypt), generate tokens
      email.py                 aiosmtplib + Jinja2 templates; fallback to stdout
      images.py                OpenCV face detect, crop to 413×531, JPEG compress
      settings.py              In-process cache of settings table
      bootstrap.py             Seed admin on first run (log temp password)
    templates/email/           Jinja2 templates for all transactional emails
  alembic/
    versions/
      0001_initial_schema.py   Initial schema; migrations 0001–0011 cover all schema evolution
  tests/                       pytest + pytest-asyncio
  setup.py                     Dependencies: litestar, sqlalchemy, pillow, etc.

frontend/                      SvelteKit (Svelte 5) + Tailwind CSS
  src/
    routes/
      +layout.svelte           Root layout: header, mobile drawer, auth state
      +layout.ts               Load user from /auth/me
      +page.svelte, +page.ts   Home, login, register, dashboard, search, admin
    lib/
      api.ts                   Typed fetch wrapper, error handling
      stores/
        toast.svelte           Toast notifications (Svelte 5 runes)
      components/
        DualRangeSlider.svelte Dual-handle age range slider (min/max on one track)
        BilingualLabel.svelte  Bilingual English+Telugu form label component
        (other components)     Reusable UI: buttons, modals, forms
  vite.config.ts               Proxy /api/* to localhost:8000
  tailwind.config.ts           Tailwind v4 with custom theme block
  package.json                 Dependencies: sveltekits, tailwindcss, lucide-svelte

deploy/                        Production scripts; see [ADMIN_GUIDE](ADMIN_GUIDE.md)
docker-compose.yml             Local: PostgreSQL 16 + Mailhog
.env                           Session secret, database URL (git-ignored)
```

## Backend architecture

**Async-first ASGI app** (Litestar) with typed request/response via msgspec. All DB calls are
async (no sync). SQLAlchemy 2.x with typed Column mappings.

**Request flow:**
1. Litestar middleware parses session cookie (HTTP-only, signed, 30-day max age)
2. Route handlers depend on `db: AsyncSession` (auto-yielded, auto-committed/rolled back)
3. Handlers check `request.session["user"]` for auth state (or call `/auth/me` endpoint)
4. Responses marshalled to JSON via msgspec Structs

**Key features:**

- **Session auth:** cookie-based (not JWT). `CookieBackendConfig` with AES-128 secret,
  samesite=lax, secure in production.
- **Bootstrap admin:** on first startup, if no users exist, seed admin at `OWNER_EMAIL` with
  temp password logged to stderr (check startup logs). Admin must change password on login.
- **Settings cache:** `SettingsService` loads DB settings into memory at startup and on write.
  Avoids N+1 queries. Editable only via `/admin/settings` endpoint. `is_prod` setting controls
  duplicate email/phone rejection (prod mode) vs test mode leniency.
- **Email fallback:** if SMTP unconfigured, `email_service` logs to stdout instead of failing
  (useful for dev/test). All email subjects include `[TEST MODE]` prefix when `is_prod=false`.
  Email templates receive site_url, ist_time, et_time, is_test_mode context variables.
- **Public site info:** `/site/info` endpoint returns `is_prod` and `site_url` so frontend can
  adjust validation strictness and banner injection per deployment.

**Models:** User, Profile (with gender/manglik/diet/astrology fields), Photo (3 variants),
DetailRequest (pending→approved→emailed), Setting (JSON config store).

**Photo pipeline:**

1. User uploads JPEG/PNG via `/profiles/{id}/photos`
2. `images.process_upload()` validates:
   - File size ≤ 10 MB (check `upload_max_mb` setting)
   - OpenCV `CascadeClassifier` detects exactly 1 face (skip if `require_face_detection=false`)
3. Auto-crop to face bounding box + padding
4. Resize to 413×531 (portrait aspect, `photo_passport_*` settings)
5. Re-encode JPEG, compress until ≤ 500 KB (check `photo_max_kb` setting)
6. Store 3 variants:
   - **passport.jpg** (full resolution, stored under `MEDIA_ROOT/profiles/{profile_id}/{photo_id}/`)
   - **blurred.jpg** (Gaussian blur r=14 pixels; shown in search/public)
   - **thumb.jpg** (150×150; admin lists)
7. Record `Photo` model with paths; mark first as primary

**Endpoints:** See [API contract](#api-contract) table below.

## Frontend architecture

**SvelteKit (Svelte 5 runes)** with **Tailwind v4 theme block**. Client-side router, ISR-style
data loading (via `+layout.ts` / `+page.ts` load functions).

**Auth flow:**

1. On mount, `+layout.ts` load calls `GET /auth/me` (via `api.auth.me()`)
2. Session cookie auto-included by browser; response sets `data.user` or null
3. Routes check `data.user` and guard access (e.g., redirect `/login` if unauthenticated)

**Mobile-first layout:**

- Header with branding (Heart icon + "मराठा कल्याणम्" + "Maratha Kalyanam")
- Desktop nav: Home, Search, About, My Profiles (if logged in), Requests, Admin (if admin)
- Navbar role chips: User/Admin status; Test mode badge (when `is_prod=false`)
- Mobile: hamburger drawer (focus-trapped, Escape to close, Tab cycles)
- Tailwind theme: maroon (primary), saffron (accent), cream (light), ink (dark text)

**Admin page lazy loading:**

- On mount, fetches `/api/admin/dashboard` (stats + up to 25 pending items per category)
- Full user/profile/request lists loaded only when tabs clicked (chip navigation)
- ag-Grid v33+ displays filtered/sorted lists; requires `ModuleRegistry.registerModules()`

**API client** (`lib/api.ts`):

- Typed fetch wrapper: credentials: 'include' for cookies
- Error handling: thrown as `ApiError(status, code, message)`
- Endpoints: `.site`, `.auth`, `.profiles`, `.photos`, `.search`, `.requests`, `.admin`, `.settings`

**State management:** Svelte 5 runes (not stores for component state); toast notifications via
`toastStore` for async feedback. Site info (is_prod, site_url) loaded in +layout.ts via `/site/info`.

## API contract

All endpoints return JSON. Auth via session cookie. Errors: `{ code, message }`.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | /auth/register | none | Email + full_name + password + user_handle + phone_number → user created (unverified) |
| POST | /auth/login | none | Email + password → session set |
| POST | /auth/logout | yes | Clear session |
| POST | /auth/verify-email | none | Token → user email_verified=true |
| GET | /auth/me | yes* | Current user (or null if not logged in) |
| GET | /site/info | none | Public config: `{is_prod: bool, site_url: string}` |
| GET | /profiles | yes | List user's own profiles |
| POST | /profiles | yes | Create draft profile |
| GET | /profiles/{id} | yes* | Get profile (full if owner/admin, partial if approved) |
| PATCH | /profiles/{id} | yes | Update profile fields (resets to pending if was approved) |
| DELETE | /profiles/{id} | yes | Delete profile |
| POST | /profiles/{id}/submit | yes | Draft → pending (or approved, if setting allows) |
| POST | /profiles/{id}/photos | yes | Upload photo (multipart) |
| DELETE | /profiles/{id}/photos/{photo_id} | yes | Delete photo |
| POST | /profiles/{id}/photos/{photo_id}/primary | yes | Set photo as primary |
| GET | /search | none | List approved profiles; filters: gender, age_min, age_max, gotra, nakshatram, rashi, city, state, country, pin_code, mother_tongue, manglik, diet, page, per_page |
| POST | /profiles/{id}/request | yes | Create detail request (requester → profile owner) |
| GET | /requests/mine | yes | List user's detail requests (both made + received) |
| GET | /admin/dashboard | admin | Single call returning stats + pending profiles/users/requests (up to 25 each) |
| GET | /admin/profiles | admin | List all profiles with optional status filter |
| POST | /admin/profiles/{id}/approve | admin | Approve profile + send email |
| POST | /admin/profiles/{id}/reject | admin | Reject profile + send email |
| GET | /admin/requests | admin | List all detail requests |
| POST | /admin/requests/{id}/approve | admin | Approve + email full profile + photos |
| POST | /admin/requests/{id}/reject | admin | Reject |
| GET | /admin/users | admin | List all users |
| POST | /admin/users/{id}/promote | admin | Grant admin role |
| POST | /admin/users/{id}/approve | admin | Approve user account (sets is_approved=true) + send account_approved email |
| POST | /admin/users/{id}/unapprove | admin | Revoke user approval |
| POST | /admin/users/{id}/verify_email | admin | Mark email as verified (sets email_verified=true) |
| POST | /admin/users/{id}/demote | admin | Strip admin role from a user. |
| POST | /admin/users/{id}/delete | admin | Hard-delete a user. Cascades profiles, photos, detail requests. Cannot delete self. |
| POST | /admin/broadcast-email | admin | Send broadcast email to filtered user subset. Lives at frontend route `/admin/broadcast`. Body booleans (all optional): `filter_verified_only` (default true), `filter_unverified_only`, `filter_approved_only`, `filter_unapproved_only`, `filter_admin_only`. Verified ↔ unverified and approved ↔ unapproved are mutually exclusive. |
| GET | /admin/settings | admin | Get all settings (mask smtp_password) |
| PUT | /admin/settings | admin | Update settings (JSON body) |
| GET | /health | none | Service health check |
| GET | /media/* | none | Serve photo files (passport/blurred/thumb) |

*GET /auth/me, GET /site/info, and unauthenticated GET /profiles/{id} do not require login but check session.
**Dashboard endpoint replaces /admin/stats; returns expanded stats with profile/request rejection counts plus pending item summaries (lazy-loaded on chip click in frontend).

## Data model

| Entity | Key fields | Notes |
|--------|-----------|-------|
| **User** | id (UUID), email (unique), full_name (VARCHAR 120), user_handle (unique), phone_number, password_hash, email_verified, is_admin, is_approved, created_at | Bootstrap admin created on first startup if no users exist. full_name is mandatory. is_approved: admin must set after email verification before user can create profiles. |
| **Profile** | id, owner_user_id (FK User), gender (bride/groom), first_name, last_name, dob, age, height_cm, weight_kg, complexion, body_type, blood_group, education, college_university, occupation, employer, work_location, annual_income_inr, pin_code, city, state, country, gotra, kuldevata, devak, surname_clan, sub_caste, nakshatram, rashi, time_of_birth, place_of_birth, manglik (yes/no/partial/unknown), mother_tongue (default "Telugu"), marital_status, diet (veg/non-veg/eggetarian), about, partner_expectations, father_occupation, mother_occupation, num_brothers, num_sisters, num_brothers_married, num_sisters_married, family_type, family_status, family_values, native_place, smokes, drinks, hobbies, status (draft/pending/approved/rejected), admin_notes, created_at, updated_at | Stateful: draft → pending (on submit) → approved/rejected (admin). Editing approved profile resets to pending. Extended fields cover personal, professional, family, lifestyle, astrological, and demographic details |
| **Photo** | id, profile_id (FK), original_filename, passport_path, blurred_path, thumb_path, byte_size, is_primary, created_at | Three variants stored under `MEDIA_ROOT/profiles/{profile_id}/{photo_id}/`. Max 5 per profile |
| **DetailRequest** | id, requester_user_id (FK User), profile_id (FK Profile), status (pending/approved/rejected), message, admin_notes, responded_at, created_at | Unique constraint on (requester_user_id, profile_id). Admin approves → email full profile + passport photos to requester |
| **Setting** | key (primary), value (JSON-encoded), updated_at, updated_by (FK User) | Runtime config: SMTP host/port/user/password, photo dimensions/limits, admin email, approval flags |

## Settings keys

All defaults seeded on first migration. Edit via `/admin/settings` (HTTP-only safe entrypoint for
secrets).

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| owner_email | string | admin.marathakalyanam@gmail.com | Recipient for admin notifications (profile requests, etc.) |
| smtp_host | string | localhost | SMTP server hostname (empty = logs to stdout) |
| smtp_port | int | 1025 | SMTP port (465 = TLS, 587 = STARTTLS) |
| smtp_user | string | (empty) | SMTP auth username |
| smtp_password | string | (empty) | SMTP auth password (masked in UI, edited via /admin/settings) |
| smtp_from | string | no-reply@marathakalyanam.com | Email "From" address |
| photo_max_kb | int | 500 | Max JPEG size after compression |
| photo_passport_width | int | 413 | Passport photo width (pixels) |
| photo_passport_height | int | 531 | Passport photo height (pixels) |
| photo_blur_width | int | 600 | Blurred variant width (for preview) |
| photo_blur_radius | int | 14 | Gaussian blur radius (pixels) |
| photo_thumb_size | int | 150 | Thumbnail size (square) |
| photos_max_per_profile | int | 5 | Max photos per profile |
| upload_max_mb | int | 10 | Max file upload size (MB) |
| require_face_detection | bool | true | Enforce single-face photo validation via OpenCV |
| require_admin_approval_for_profiles | bool | true | Profiles require admin approval (pending→approved) or auto-approve on submit |
| is_prod | bool | false | **Production mode flag.** When true: reject duplicate email/phone; email subjects omit `[TEST MODE]` prefix; frontend validation is strict. When false (test): allow duplicates; add `[TEST MODE]` to subjects; frontend can be lenient. |
| site_url | string | https://marathakalyanam.com | Base URL injected into all email templates for links (verify_email, approve, etc.). Read by frontend via `/site/info`. |

## Local dev workflow

**Prerequisites:** Podman (or Docker), Python 3.11+, Node.js 18+

### 1. Bring up local infrastructure

Use **Podman** instead of Docker:

```bash
podman compose up -d
# or if using podman-compose:
podman-compose up -d
# Postgres: localhost:5432 (marathakalyanam/marathakalyanam)
# Mailhog: localhost:8025 (email UI)
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
cp ../.env.example ../.env
# Edit .env if needed (defaults should work locally)
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Startup logs will show:

```
BOOTSTRAP ADMIN CREATED
Email: admin.marathakalyanam@gmail.com
Temporary password: <temp_password>
One-time reset token: <reset_token>
```

Log in at http://localhost:5173/login with temp password. Then go to account settings to
change it.

Mailhog captures all outbound emails: http://localhost:8025

### 3. Frontend setup (new terminal)

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

Vite proxy forwards `/api/*` to `http://localhost:8000`.

## Testing

```bash
cd backend
pytest tests/              # Run all tests
pytest -v                  # Verbose
pytest tests/test_auth.py  # Single file
pytest --cov=app          # Coverage report
```

Tests use `pytest-asyncio` for async fixtures. Use `@pytest.mark.asyncio` on async test
functions.

## Subagents

- **`backend`** — Python/Litestar/SQLAlchemy/Alembic work; `backend/app`, `backend/tests`
- **`frontend`** — SvelteKit/Svelte 5/Tailwind work; `frontend/src`
- **`test`** — pytest coverage; `backend/tests`
- **`doc`** — *.md updates; `CLAUDE.md`, `USER_GUIDE.md`, `ADMIN_GUIDE.md`

## Recent changes (May 2026)

- Added `/site/info` public endpoint for frontend to query `is_prod` and `site_url`
- Added `/admin/dashboard` endpoint returning stats + up to 25 pending items (replaces
  `/admin/stats`); dashboard stats now include `profiles_rejected`, `profiles_draft`,
  `requests_approved`, `requests_rejected`
- Admin UI now lazy-loads full user/profile/request lists on tab chip clicks (no longer pre-fetches)
- Email subjects now include `[TEST MODE]` prefix when `is_prod=false`
- Navbar shows role chips (User/Admin/Test mode badge)
- Image baseline: home.jpg 556 KB JPEG, logo.png 76 KB
- ag-Grid v33 requires explicit ModuleRegistry registration

## Conventions

- **Async-only:** no sync DB calls anywhere. All routes async, all services async, all DB ops
  use AsyncSession.
- **msgspec for I/O:** all request/response bodies are typed msgspec Structs. No bare dicts in
  schemas.
- **Never log secrets:** SMTP password, DB URL, session secret, verification tokens never in
  logs. Use logger.debug() sparingly.
- **Photo files not in git:** all uploaded files under `MEDIA_ROOT` are gitignored. DB seeds
  defaults; user uploads are ephemeral per environment.
- **Settings edited via UI only:** don't read from `.env` after startup. Use
  `/admin/settings` to change SMTP, owner email, etc. This ensures config is consistent across
  all app instances.
- **Profile status machine:** draft → (user submits) → pending → (admin approves/rejects) →
  approved/rejected. Editing an approved profile resets it to pending for re-approval.
- **Email fallback:** if `smtp_host` is empty or unreachable, `email_svc._send()` logs HTML to
  stdout instead of raising. Useful for dev/test without real SMTP.
- **ag-Grid in frontend:** v33+ requires `ModuleRegistry.registerModules([AllCommunityModule])`
  before instantiating grids. Without this, grids render but silently fail to populate row data.
- **Hardcoded URLs:** always read site_url from settings service; never hardcode
  `https://marathakalyanam.com` in code. Use `/site/info` endpoint on frontend if needed.
