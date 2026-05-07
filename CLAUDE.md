# marathakalyanam — engineering guide

Matrimonial site for Maratha people living in Andhra Pradesh, Telangana and other states.
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
        BilingualLabel.svelte  Bilingual English + active indic-language form label
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

1. User uploads JPEG/PNG/WebP via `/profiles/{id}/photos`
2. `images.process_upload()` validates ONLY size:
   - Raw upload size between `upload_min_kb` (20) and `upload_max_mb` (6)
   - Smaller / lower-res inputs are upscaled instead of rejected
   - Face detection is **off by default** (`require_face_detection=false`)
3. Crop based on slot:
   - Slot 1 (primary): **413×531** face headshot (`photo_passport_width/height`)
   - Slot 2 (secondary): **600×900** full-body (`photo_body_width/height`)
4. Three variants encoded via iterative quality stepping (`_encode_jpeg`):
   - **passport.jpg** — main display variant (face or body crop), capped at `photo_max_kb` (180)
   - **blurred.jpg** — Gaussian blur r=14, capped at `photo_blur_max_kb` (50)
   - **thumb.jpg** — 150×150 square, capped at `photo_thumb_max_kb` (12)
5. Photos written + URLs served via the **storage abstraction**
   (`services/storage.py`) — see Storage backend below
6. Record `Photo` row with path + byte_size; first photo flagged primary
7. **Rollback safety**: if DB commit fails after the storage writes, the
   three uploaded objects are deleted before re-raising — no orphans

**Storage backend:**

Photos route through `services/storage.py` instead of writing directly
to the filesystem. The active backend is selected by the `storage_provider`
setting:

| `storage_provider` | What happens |
|---|---|
| `local` (default) | Writes to `MEDIA_ROOT/profiles/<pid>/<photo_id>/<variant>.jpg`. URLs are `marathakalyanam.com/media/...`. The existing `/media/` Litestar route serves them. |
| `r2` | Writes to a Cloudflare R2 bucket via the S3 API (boto3). `blurred` + `thumb` URLs point to `r2_public_base_url/<key>` (cacheable, public). `passport` URLs are signed S3 GET URLs with `r2_signed_url_ttl_sec` TTL — privacy stays gated even with a public bucket. If `r2_public_base_url` is empty, all URLs are signed (private bucket mode). |

Flipping `storage_provider` between `local` and `r2` via `/admin/settings`
takes effect on the next request — `get_storage()` builds a fresh backend
each call. Local files are not auto-deleted when flipping to r2; they
remain on disk as a revert safety net until purged.

To migrate live photos from local → R2, see `backend/scripts/R2_SETUP.md`
and `backend/scripts/migrate_photos_to_r2.py`. The migration script is
idempotent (skips files already present in R2 with matching size).

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
| GET | /admin/profiles/{id}/pdf | super | Render the profile as a print-quality PDF dossier (photos embedded, owner contact included). Default: `Content-Disposition: inline`. Pass `?download=true` for a forced download. Super-only — exposes contact info. |
| GET | /admin/requests | admin | List all detail requests |
| POST | /admin/requests/{id}/approve | admin | Approve + email full profile + photos |
| POST | /admin/requests/{id}/reject | admin | Reject |
| GET | /admin/users | admin | List all users |
| POST | /admin/users/{id}/promote | super | Grant admin role. Target must be approved + verified + not revoked. |
| POST | /admin/users/{id}/approve | admin | Approve user account (sets is_approved=true) + send account_approved email. Super-only on admin targets. |
| POST | /admin/users/{id}/unapprove | admin | Revoke user approval. Super-only on admin targets. |
| POST | /admin/users/{id}/verify_email | admin | Mark email as verified. Super-only on admin targets. |
| POST | /admin/users/{id}/resend_verification | admin | Regenerate verification token + re-send email. |
| POST | /admin/users/{id}/demote | super | Strip admin role from a user. |
| POST | /admin/users/{id}/revoke | admin | Soft-revoke (login blocked, is_approved=False). Super-only on admin targets. Cascade-revokes user's pending requests. |
| POST | /admin/users/{id}/reinstate | admin | Reverse revoke. Sets is_approved=True only if email_verified. |
| POST | /admin/users/{id}/suspend | admin | Admin enforcement hold. Login still works; profiles drop from search; can't create new ones. Super-only on admin targets. |
| POST | /admin/users/{id}/unsuspend | admin | Lift admin suspension. Does NOT clear is_paused (user-only toggle). |
| POST | /admin/users/{id}/delete | admin | Hard-delete a user. Cascades profiles, photos, detail requests. Cannot delete self. |
| POST | /auth/me/pause | self | Vacation mode — set is_paused=True. Profile hides from search; can still log in. |
| POST | /auth/me/unpause | self | Clear self-pause. Cannot clear admin's is_suspended. |
| POST | /auth/me/delete | self | Self-service account deletion. Requires current password + typed `DELETE` confirmation. Super-users blocked (bootstrap-pinned). |
| POST | /auth/me/resend-verification | self | Self-service: regenerate token + re-send verification email. |
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
| **User** | id (UUID), email, full_name, user_handle (unique), phone_number, password_hash, email_verified, is_admin, is_super, is_approved, is_revoked, is_paused, is_suspended, created_at | Five role/state flags: `is_admin` (admin powers), `is_super` (above admin — super-tier hidden from regular admins), `is_approved` (can create profiles), `is_revoked` (banned — login blocked), `is_paused` (self vacation mode — login OK, profile hidden), `is_suspended` (admin enforcement — login OK, profile hidden, only admin can lift). Bootstrap users seeded on every boot from `services/bootstrap.py`. |
| **Profile** | id, owner_user_id (FK User), gender, first_name, last_name, dob, demographic + astro + family + lifestyle fields, status (draft/pending/approved/revoked), admin_notes, rejected_at, created_at, updated_at | Stateful: draft → pending → approved/revoked. Owner edit drops approved→pending. `rejected_at` enforces "must edit before resubmit" guard. Visible in search only when status=approved AND owner is_approved AND NOT (is_revoked / is_paused / is_suspended). |
| **Photo** | id, profile_id (FK), original_filename, passport_path, blurred_path, thumb_path, byte_size, is_primary, created_at | Three variants. Storage backend (local disk under `MEDIA_ROOT` or Cloudflare R2) chosen at runtime by `storage_provider` setting. Max 2 per profile. |
| **DetailRequest** | id, requester_user_id (FK User), profile_id (FK Profile), status (pending/approved/revoked), message, admin_notes, responded_at, created_at | Unique constraint on (requester_user_id, profile_id). User-revoke / profile-revoke cascade-revoke pending requests. Approve → email full profile + passport bytes (read via storage). |
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
| photo_max_kb | int | 180 | Max passport-variant JPEG size after compression |
| photo_min_kb | int | 12 | Passport-variant JPEG floor (informational; not enforced as rejection) |
| photo_blur_max_kb | int | 50 | Blurred-variant JPEG cap |
| photo_thumb_max_kb | int | 12 | Thumb-variant JPEG cap |
| photo_passport_width / height | int | 413 / 531 | Slot 1 (face) crop dimensions |
| photo_body_width / height | int | 600 / 900 | Slot 2 (full body) crop dimensions |
| photo_blur_width | int | 600 | Blurred variant width (for preview) |
| photo_blur_radius | int | 14 | Gaussian blur radius (pixels) |
| photo_thumb_size | int | 150 | Thumbnail size (square) |
| photo_min_dimension_px | int | 600 | Source min shortest side; smaller is upscaled (no longer rejected) |
| photo_max_dimension_px | int | 3500 | Source longest side; longer is downscaled to save CPU |
| photos_max_per_profile | int | 2 | Max photos per profile |
| upload_max_mb | int | 6 | Max raw upload size (MB) |
| upload_min_kb | int | 20 | Min raw upload size (KB) — rejects thumbnails / icons |
| require_face_detection | bool | false | Enforce single-face photo validation via OpenCV (off by default) |
| require_admin_approval_for_profiles | bool | true | Profiles require admin approval (pending→approved) or auto-approve on submit |
| storage_provider | string | local | Photo storage backend. `local` = host filesystem under MEDIA_ROOT. `r2` = Cloudflare R2 via S3 API. Flip via `/admin/settings`; effective immediately. |
| r2_endpoint | string | (empty) | S3 API URL `https://<account-id>.r2.cloudflarestorage.com` (only used when `storage_provider=r2`) |
| r2_bucket | string | (empty) | R2 bucket name |
| r2_access_key_id | string | (empty) | R2 token AKID |
| r2_secret_access_key | string | (empty) | R2 token secret (masked in UI) |
| r2_public_base_url | string | (empty) | Public host for blurred/thumb URLs (e.g. `https://pub-XXX.r2.dev` or custom domain). Empty → all URLs signed (private bucket mode). |
| r2_signed_url_ttl_sec | int | 3600 | TTL for signed passport URLs (seconds) |
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

## v2.0 — May 2026

This is a milestone release. Major surfaces redesigned: user lifecycle,
photo storage, admin UI, SEO posture.

**User lifecycle — three independent state-flag axes**

  - `is_revoked` — admin ban; **blocks login**
  - `is_paused` — user-controlled vacation mode; login still works,
    profile hidden from search, can't create new profiles
  - `is_suspended` — admin enforcement hold; same external effect as
    paused but only an admin can lift it
  - `is_approved` — admin OK-to-create; gated regardless of the three
    above
  Cascade behaviour: revoke + reject-profile both revoke pending detail
  requests; cleanup paths are storage-backend-aware.

**Photo storage abstraction (`services/storage.py`)**

  - `storage_provider` setting: `local` (default) | `r2`
  - LocalStorage writes to `MEDIA_ROOT`, R2Storage writes via boto3 to
    a Cloudflare R2 bucket (S3 API)
  - Slot 1 = passport-style face headshot (413×531), slot 2 = full-body
    (600×900); both go through iterative-quality JPEG encoding under
    per-variant size caps
  - Upload rollback safety: DB commit failure deletes the just-written
    storage objects so no orphans accumulate
  - Migration tooling at `backend/scripts/migrate_photos_to_r2.py` +
    `R2_SETUP.md`

**Admin dashboard**

  - `/admin/dashboard` returns stats + pending lists; stats include
    photos_count + photos_total_bytes for storage visibility
  - users_admins / users_super counts withheld for non-super callers
  - Admin tier (rows where is_admin=True) hidden from non-super
    `/admin/users` listing
  - Selected-profile / selected-request panels stack vertically on
    mobile so labels don't overlap action buttons
  - "Suspend / Unsuspend" buttons + status chips per user

**SSR + SEO**

  - SvelteKit SSR enabled (was SPA-only). `hooks.server.ts` proxies
    `/api/*` to the local backend (port 8003) so SSR-time fetches don't
    short-circuit through SvelteKit's internal dispatcher
  - `app.html` carries title + JSON-LD + `<noscript>` body fallback so
    text-only crawl pass sees full content
  - nginx sends `www.marathakalyanam.com` 301 → apex (no more duplicate
    content)
  - sitemap.xml published; submitted in GSC

**Other**

  - 4 canonical bootstrap users: ambore (super), super (super-handle,
    Venkat Somajigiri), rambo (admin), admin (admin)
  - Phase 1 (March-April 2026) features still standing: i18n in 5 indic
    langs, settings-driven config, telegram ops alerts, soft-revoke
    lifecycle, request cascade
  - Image baseline: home.jpg 556 KB, logo.png 76 KB
  - ag-Grid v33 requires explicit ModuleRegistry registration

## v2.1 — May 2026

Incremental release; polish on reporting, SEO, and super-user operations.

**Profile PDF dossier (super-only)**

  - New endpoint `GET /admin/profiles/{id}/pdf?download=bool` renders
    an A4 print-quality PDF with embedded photos, owner contact
    (email + phone), and brand badge
  - Implemented via WeasyPrint (HTML+CSS) + Jinja2 template at
    `backend/app/templates/pdf/profile.html`
  - Brand logo bundled at `backend/app/templates/pdf/logo.png`; cached
    as base64 data URL at module import
  - Photos read via `storage_svc.read_async()` and embedded as base64
    — works with both `local` and `r2` storage backends
  - Frontend "View PDF" + "Download PDF" buttons on admin
    selected-profile action panel; gated behind `loggedInUser?.is_super`
  - **Super-only** — dossier exposes contact details so regular admins
    cannot access the endpoint or UI buttons
  - i18n keys `viewPdf` / `downloadPdf` added across en/te/mr/kn/ta/hi
  - Server prerequisite: `apt install -y libpango-1.0-0 libpangoft2-1.0-0
    libharfbuzz0b libfontconfig1 libgdk-pixbuf-2.0-0` (WeasyPrint
    runtime deps; documented in `services/pdf.py` docstring)

**SEO tightening**

  - JSON-LD `Organization` now includes structured `ImageObject` for
    logo: url + contentUrl + width/height (512) + caption. Top-level
    `image` field also added.
  - `/favicon.ico` now served via SvelteKit endpoint
    (`frontend/src/routes/favicon.ico/+server.ts`) with explicit
    `Content-Type: image/x-icon` and 1-day immutable cache. Static
    favicon moved from `frontend/static/` to `frontend/src/lib/` so
    route handler wins over SvelteKit's static middleware. Fixes
    Google's favicon fetcher getting empty content-type from
    adapter-node.

**Home hero polish**

  - Indic-text plate background opacity lightened (alpha 0.55 → 0.30)
    for improved legibility against home background photo

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
  approved/revoked. Editing an approved profile resets it to pending for re-approval.
  Re-submitting a revoked profile requires the owner to actually edit (`updated_at >
  rejected_at`) — `submit_profile` 409s otherwise.
- **Photo storage:** all photo I/O goes through `services/storage.py`. Never read/write
  `MEDIA_ROOT` directly from route handlers. The active backend (`local` or `r2`) is chosen
  at runtime by `storage_provider` setting, no service restart needed to flip.
- **Email fallback:** if `smtp_host` is empty or unreachable, `email_svc._send()` logs HTML to
  stdout instead of raising. Useful for dev/test without real SMTP.
- **ag-Grid in frontend:** v33+ requires `ModuleRegistry.registerModules([AllCommunityModule])`
  before instantiating grids. Without this, grids render but silently fail to populate row data.
- **Hardcoded URLs:** always read site_url from settings service; never hardcode
  `https://marathakalyanam.com` in code. Use `/site/info` endpoint on frontend if needed.
