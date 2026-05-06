# marathakalyanam — admin guide

Operational guide for administrators of Maratha Kalyanam.

## Admin role

An administrator has access to the **Admin** dashboard and can approve profiles, approve detail
requests, manage users, and adjust settings.

### Who can be an admin?

Currently, the first admin is bootstrapped automatically on initial deployment (see
[First-time bootstrap](#first-time-bootstrap)).

### Approving new users

After a user verifies their email, they appear in the **Users** tab with `Approved: No`. Admin
must click **Approve** to allow them to create profiles. Users receive an email confirmation
when approved. Admins can also revoke approval (sets is_approved=false).

The Users tab uses an interactive ag-Grid table — click a row to select a user, then use the
action panel below to:
- **Approve** (sets is_approved=true)
- **Revoke Approval** (sets is_approved=false)
- **Verify Email** (marks email_verified=true, useful if needed)
- **Make Admin** (grants admin privileges)

### Promoting another user to admin

1. Log in as an admin
2. Go to **Admin > Users**
3. Click a row to select a user
4. In the action panel, click **Make Admin**
5. They will now see the **Admin** link in the top navigation

**Note:** Only admins can promote other users. Make sure you trust them before granting access.

## Approving profiles

Profiles are submitted by users and queued for review.

### Flow

1. User fills out their profile (personal, astrology, photo, etc.) and clicks **Submit**
2. Profile status changes to "pending" (only visible to owner)
3. Admin receives a notification (email to `owner_email` setting)

### Reviewing a pending profile

1. Log in and go to **Admin > Profiles**
2. Filter by status: **Pending**
3. Click on a profile to view full details, including:
   - All fields (name, age, education, occupation, income, etc.)
   - Thumbnail photos (all variants)
   - Admin notes field (if it was previously rejected)
4. Assess:
   - Is the information complete and plausible?
   - Are photos appropriate (single face, clear, passport-style)?
   - Does it comply with community guidelines?
5. Click **Approve** or **Reject**:
   - **Approve:** profile becomes public (appears in search). Owner gets approval email.
   - **Reject:** profile returns to draft. Owner gets rejection email with your notes (explaining why, so they can fix and resubmit).

### Approval actions

| Action | Field | Purpose |
|--------|-------|---------|
| Approve | Admin notes (optional) | Message sent in approval email (optional, e.g. "Great profile!") |
| Reject | Admin notes (required) | Explain reason to owner; they can edit and resubmit |

**Best practices:**
- Be consistent: similar profiles should get similar treatment
- Be constructive in rejections: point out specific issues (e.g. "Please use a clearer photo")
- Don't approve profiles with missing info or inappropriate photos
- For unclear cases, reject with notes asking for clarification; don't guess

## Approving full-detail requests

When a user requests full details about another's approved profile, admin must approve.

### Flow

1. Requester clicks **Request Full Details** on a profile they like
2. Request status: "pending"
3. Admin receives notification (email to `owner_email`)

### Reviewing a request

1. Log in and go to **Admin > Requests**
2. Filter by status: **Pending**
3. Each request shows:
   - Requester's email address
   - Profile ID they're requesting
   - Their message (if any)
   - Created date
4. Assess: is this a genuine request? (usually yes, unless spam/abuse)
5. Click **Approve** or **Reject**:
   - **Approve:** requester receives email with:
     - Profile's full details (name, income, all fields)
     - Clear, full-size photos (passport variants)
     - Profile owner's email address (if shared) so they can contact directly
   - **Reject:** requester gets rejection note; no details sent

### Request approval actions

| Action | Field | Purpose |
|--------|-------|---------|
| Approve | Admin notes (optional) | Internal note; not sent to requester |
| Reject | Admin notes (optional) | Reason for rejection (not visible to requester) |

**Best practices:**
- Approve genuine requests (people interested in connecting)
- Reject only if: spam detected, abusive message, or request violates guidelines
- Monitor trends: if one user makes too many requests, consider limiting them

## Settings page

The Settings page is the **only safe place to enter sensitive data** (SMTP credentials).

### Accessing settings

1. Log in as admin
2. Go to **Admin > Settings**
3. All settings appear as editable fields

### All settings

| Key | Type | Default | Purpose | Edit? |
|-----|------|---------|---------|-------|
| owner_email | string | admin.marathakalyanam@gmail.com | Recipient for admin notifications (profile requests, rejections, Telegram alerts, etc.) | Yes |
| smtp_host | string | localhost | SMTP server hostname (e.g. "mail.example.com"). **IMPORTANT: Never hardcode in code; always set here.** | Yes |
| smtp_port | int | 1025 | SMTP port (465 = implicit TLS, 587 = STARTTLS) | Yes |
| smtp_user | string | (empty) | SMTP auth username (leave blank if not needed) | Yes |
| smtp_password | string | (empty) | SMTP auth password. **MASKED in UI (shown as `***` if set).** Edit only via this page, never in code. | Yes |
| smtp_from | string | no-reply@marathakalyanam.com | "From:" email address in outbound mail | Yes |
| photo_max_kb | int | 180 | Max passport-variant JPEG size after compression (KB). Smaller = faster but lower quality. | Yes |
| photo_min_kb | int | 12 | Passport JPEG floor (informational; not a hard reject). | Yes |
| photo_blur_max_kb | int | 50 | Blurred variant cap (KB). | Yes |
| photo_thumb_max_kb | int | 12 | Thumb variant cap (KB). | Yes |
| photo_passport_width | int | 413 | Slot 1 (face) width (pixels) | No |
| photo_passport_height | int | 531 | Slot 1 (face) height (pixels) | No |
| photo_body_width | int | 600 | Slot 2 (full body) width (pixels) | No |
| photo_body_height | int | 900 | Slot 2 (full body) height (pixels) | No |
| photo_blur_width | int | 600 | Blurred variant width (pixels, for search results) | Yes |
| photo_blur_radius | int | 14 | Gaussian blur radius (pixels); higher = more blurred | Yes |
| photo_thumb_size | int | 150 | Thumbnail size (square, pixels, for admin interface) | Yes |
| photo_min_dimension_px | int | 600 | Source min shortest side. Smaller is upscaled rather than rejected. | Yes |
| photo_max_dimension_px | int | 3500 | Source longest side; longer is downscaled before processing. | Yes |
| photos_max_per_profile | int | 2 | Max photos per profile (slot 1 face, slot 2 body) | Yes |
| upload_max_mb | int | 6 | Max raw upload size (MB) | Yes |
| upload_min_kb | int | 20 | Min raw upload size (KB). Below = thumbnail/icon, rejected. | Yes |
| require_face_detection | bool | false | Enforce single-face photo validation via OpenCV. **Off by default** — over-rejects normal phone shots. | Yes |
| require_admin_approval_for_profiles | bool | true | If true: profiles go to pending on submit, admin must approve. If false: auto-approve on submit. | Yes |
| is_prod | bool | false | When true: reject duplicate email/phone registrations (production mode). When false: allow multiple accounts with same contact info (testing mode). | Yes |
| site_url | string | https://marathakalyanam.com | Base URL injected into all email templates for links (verify_email, approve, etc.). Update if domain changes. | Yes |
| storage_provider | string | local | **Photo storage backend.** `local` = host filesystem under `MEDIA_ROOT`. `r2` = Cloudflare R2 via S3 API. Flip via this page; effective immediately on the next request. | Yes |
| r2_endpoint | string | (empty) | R2 S3 API URL: `https://<account-id>.r2.cloudflarestorage.com` | Yes |
| r2_bucket | string | (empty) | R2 bucket name | Yes |
| r2_access_key_id | string | (empty) | R2 token Access Key ID | Yes |
| r2_secret_access_key | string | (empty) | R2 token secret. **MASKED in UI**. | Yes |
| r2_public_base_url | string | (empty) | Public R2 URL for blurred/thumb (e.g. `https://pub-XXX.r2.dev`). Empty → all URLs signed (private bucket mode). | Yes |
| r2_signed_url_ttl_sec | int | 3600 | TTL (seconds) for signed passport URLs | Yes |

### Common adjustments

- **Slow email delivery?** Check `smtp_host`, `smtp_port`, and credentials.
- **Photos uploads being rejected?** Check `upload_max_mb` and `upload_min_kb`. The pipeline only rejects on raw size out-of-bounds — dimensions, format, post-compression byte count are all handled gracefully.
- **Too many spam profiles?** Keep `require_admin_approval_for_profiles` at `true` (default).
- **Switching photo storage from local disk to Cloudflare R2:** see "Photo storage migration" below.

**⚠️ SMTP credentials are sensitive:** never log them, never put them in `.env` (bootstrap secrets only). Use the Settings UI.

## Photo storage migration (local ↔ Cloudflare R2)

The site can store photos either on the host filesystem (`local`) or in
a Cloudflare R2 bucket (`r2`). Default is `local`. The active backend
is chosen by the `storage_provider` setting and can be flipped at
runtime — the next request reads the new value, no service restart.

### When to use each

| Backend | Best for |
|---|---|
| `local` | Single-server deployment, low traffic, no externalisation needed. Photos in `MEDIA_ROOT/profiles/<pid>/<photo_id>/`. |
| `r2` | Multi-server, edge-cacheable public assets (blurred + thumb), durability without on-host backups. Cost ≈ $0.02 / GB / month. |

### Set up R2 (one-time)

Detailed walkthrough: `backend/scripts/R2_SETUP.md`. Summary:

1. Cloudflare → R2 → **Create bucket** (e.g. `marathakalyanam-photos`).
2. R2 → **Manage R2 API Tokens** → Create token with **Object Read & Write**, scoped to that bucket.
3. Bucket → **Settings** → enable **Public R2.dev URL** (or set up a custom domain). Copy the public URL.
4. In `/admin/settings`, set:
   - `r2_endpoint` → `https://<account-id>.r2.cloudflarestorage.com`
   - `r2_bucket` → bucket name
   - `r2_access_key_id` → token AKID
   - `r2_secret_access_key` → token secret
   - `r2_public_base_url` → public URL from step 3 (or leave empty for signed-only mode)
5. **Don't flip `storage_provider` to `r2` yet** — first migrate.

### Migrate existing local photos to R2

```bash
ssh ramboq "cd /opt/marathakalyanam/backend && source .venv/bin/activate && \
  python -m scripts.migrate_photos_to_r2 --dry-run"   # preview
ssh ramboq "cd /opt/marathakalyanam/backend && source .venv/bin/activate && \
  python -m scripts.migrate_photos_to_r2"             # actual upload
```

The script is idempotent — re-running skips files already present in R2.
Local files are NOT deleted by the migration; they remain as a revert
safety net.

### Flip the active backend

In `/admin/settings`, change `storage_provider` from `local` to `r2`.
Effective immediately. Verify via:

- `/search` (anonymous) — blurred URLs should now point at the R2 host
- A profile detail page (logged in) — passport URLs should be signed
  S3 URLs ending in `?X-Amz-Signature=...`

### Reverting

Flip `storage_provider` back to `local`. Local files are still on disk;
the site recovers cleanly. Files written to R2 between flip and revert
are orphaned — purge manually if needed.

### Cleaning up orphans

Past user/profile deletes before the v2 cleanup fix may have left
orphan photo files (no matching `Photo` row). Use:

```bash
ssh ramboq "cd /opt/marathakalyanam/backend && source .venv/bin/activate && \
  python /tmp/cleanup_orphans.py"           # report only
ssh ramboq "cd /opt/marathakalyanam/backend && source .venv/bin/activate && \
  python /tmp/cleanup_orphans.py --delete"  # delete from BOTH local + R2
```

The script lives at `/tmp` because it's a one-shot. Re-create from
`backend/scripts/cleanup_orphans.py` if you ever ship it permanently.

## Suspending vs revoking users

Three escalating admin actions are available per user. They serve
distinct purposes — pick the right one:

| Action | Effect on login | Effect on profile visibility | Reversible by |
|---|---|---|---|
| **Suspend** (admin) | Login still allowed | Profile hidden from search, can't create new ones | Admin only |
| **Revoke** (admin) | **Blocks login** entirely | Profile hidden | Admin (reinstate) |
| **Pause** (user, self-service) | Login still allowed | Profile hidden | User can self-unpause |

Use **Suspend** when you need to investigate without permanent
escalation (TOS hold, identity verification pending). The user can
still log in and respond to admin messages. Use **Revoke** when the
account should be locked out entirely (TOS violation, abuse). Use
**Reinstate** to reverse a revoke.

The admin user-action panel surfaces buttons contextually — Suspend
appears when the user isn't already suspended, Unsuspend when they
are. Same for revoke / reinstate.

## Sending a broadcast email

From the admin dashboard, go to the **Broadcast Email** tab. Fill in:
- **Subject:** Email subject line (recommended: include your org name)
- **Message:** Plain text or simple HTML for the email body

Choose audience filters:
- **Only email-verified users:** Include only users who have verified their email
- **Only admin-approved users:** Include only users who have been admin-approved

Click **Send Broadcast**. The result shows how many emails were delivered vs failed. Emails are
sent using the configured SMTP credentials and use the same branded template. Use this for
announcements, feature updates, or important notices.

## Bootstrap & first-time setup

### On first startup

When the backend service starts for the first time (fresh database), it automatically:

1. Runs Alembic migrations (0001 through 0011) to create the database schema and all fields
2. Seeds default settings from [CLAUDE.md#settings-keys](CLAUDE.md#settings-keys)
3. Creates a bootstrap admin user at the `OWNER_EMAIL` address (default:
   admin.marathakalyanam@gmail.com)

The startup log shows:

```
======================================================
BOOTSTRAP ADMIN CREATED
Email: admin.marathakalyanam@gmail.com
Temporary password: aB3XyZ9kL2qP5wX
One-time reset token: 12345abcdef...
Change your password immediately after first login.
======================================================
```

Check the backend logs:

```bash
journalctl -u marathakalyanam_api.service
```

### Initial configuration

After bootstrap, complete these steps:

1. **Log in as admin:**
   - Go to https://marathakalyanam.com/login
   - Email: `admin.marathakalyanam@gmail.com` (or your `OWNER_EMAIL`)
   - Password: (the temp password from startup logs)

2. **Change your password immediately:**
   - Click your name (top right) → Account Settings
   - Enter a new, strong password

3. **Update notification email (if needed):**
   - Go to **Admin > Settings**
   - Update `owner_email` if you want admin notifications sent elsewhere
   - Telegram bot (MarathaKalaynamBot) also alerts on `owner_email` for: new registrations,
     profile submissions/approvals/rejections, and view request activity

4. **Configure SMTP:**
   - Go to **Admin > Settings**
   - For Gmail: use `smtp.gmail.com`, port `587`, your Gmail address, and an App Password
     (not your regular password). Generate App Passwords at myaccount.google.com/apppasswords
   - Set `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`
   - Test by submitting a profile; you should receive an approval notification email

5. **Enable production mode (when ready to go live):**
   - Go to **Admin > Settings**
   - Set `is_prod=true` to prevent duplicate accounts (same email/phone can't register twice)
   - Leave `is_prod=false` during testing to allow multiple accounts with same contact info

### Password recovery

If you lose your password:

1. Access the server: `ssh ramboq`
2. Connect to the database and reset your password hash:
   ```bash
   psql -U marathakalyanam -d marathakalyanam
   ```
3. Or request another admin to reset it (future feature)

## Production deployment

### Server access

Production server: **ramboq** (root@69.62.78.136)

```bash
ssh ramboq
# or directly:
ssh root@69.62.78.136
```

Application directory: `/opt/marathakalyanam`

### Services

Two systemd services run on the production server:

| Service | Port | Purpose |
|---------|------|---------|
| `marathakalyanam_web.service` | 3003 | SvelteKit frontend (Node.js) |
| `marathakalyanam_api.service` | 8003 | Litestar API backend (Python) |

Both are managed by systemd and auto-restart on failure.

### Viewing logs

View service logs in real time:

```bash
# Frontend logs
journalctl -u marathakalyanam_web.service -f

# Backend logs
journalctl -u marathakalyanam_api.service -f
```

### Deploying changes

```bash
ssh ramboq "cd /opt/marathakalyanam && bash deploy/webhook-deploy.sh"
```

This script:
1. Pulls latest code from the repository
2. Rebuilds and restarts both services
3. Runs database migrations (if schema changes exist)
4. Sends a Telegram notification on completion to the configured bot

### Database migrations after schema changes

After pulling code that includes new Alembic migrations:

```bash
ssh ramboq "cd /opt/marathakalyanam/backend && \
  source .venv/bin/activate && \
  alembic upgrade head"
```

Verify migration success in the backend service logs:

```bash
ssh ramboq "journalctl -u marathakalyanam_api.service -n 50"
```

### Nginx proxy

Nginx on the production server reverse-proxies traffic to both services:

- `https://marathakalyanam.com` → port 3003 (frontend)
- `https://marathakalyanam.com/api/*` → port 8003 (backend)

SSL/TLS is handled by Nginx; certificates are managed by Certbot.

## Backups & maintenance

Maratha Kalyanam stores two critical asset types:

### 1. Database (PostgreSQL)

Back up the entire database regularly. On the production server:

```bash
ssh ramboq

# Full database dump
pg_dump -h localhost -U marathakalyanam -d marathakalyanam \
  > /backups/marathakalyanam_$(date +%Y%m%d_%H%M%S).sql

# Compress
gzip /backups/marathakalyanam_*.sql

# Example: daily automated backup via cron
0 2 * * * pg_dump -h localhost -U marathakalyanam -d marathakalyanam \
  | gzip > /backups/mk_$(date +\%Y\%m\%d).sql.gz
```

### 2. Media files (user photos)

All uploaded profile photos are stored at `/opt/marathakalyanam/var/media`. Back up
this directory:

```bash
# From your local machine, rsync to a backup location
rsync -av --delete ramboq:/opt/marathakalyanam/var/media/ \
  /local/backup/marathakalyanam-media/

# Or set up automated daily backup on the server via cron
0 3 * * * rsync -av --delete /opt/marathakalyanam/var/media/ \
  backup-user@backup.example.com:/backups/marathakalyanam-media/
```

### Backup retention & testing

- Keep database backups for at least 30 days (rotate old ones)
- Keep media backups in sync; `rsync --delete` removes orphaned files
- Test restore procedures monthly to ensure backups are valid

### Disaster recovery

To restore from backup on the production server:

```bash
ssh ramboq

# 1. Stop services to prevent writes during restore
systemctl stop marathakalyanam_web.service marathakalyanam_api.service

# 2. Restore database
gunzip < /backups/marathakalyanam_YYYYMMDD.sql.gz | \
  psql -h localhost -U marathakalyanam -d marathakalyanam

# 3. Restore media files
rsync -av /backups/marathakalyanam-media/ \
  /opt/marathakalyanam/var/media/

# 4. Restart services
systemctl start marathakalyanam_web.service marathakalyanam_api.service

# 5. Verify the restore
journalctl -u marathakalyanam_api.service -f
```

## Photo upload pipeline

When users upload a profile photo, the system automatically:

1. **Validates file:**
   - Maximum size: `upload_max_mb` setting (default 10 MB)
   - Format: JPEG or PNG

2. **Face detection (if enabled):**
   - Uses OpenCV `CascadeClassifier` to detect faces
   - If `require_face_detection=true` (default), enforces exactly 1 face per photo
   - Rejects if 0 or multiple faces detected
   - Can be disabled in **Admin > Settings** for testing (not recommended for production)

3. **Auto-crop:**
   - Automatically crops to the face bounding box with padding
   - Preserves portrait orientation

4. **Resize & compress:**
   - Resizes to passport dimensions: `photo_passport_width` × `photo_passport_height`
     (default 413 × 531 pixels)
   - Re-encodes as JPEG and compresses until ≤ `photo_max_kb` (default 500 KB)

5. **Store three variants:**
   - **passport.jpg:** Full-resolution clear photo (stored at
     `/opt/marathakalyanam/var/media/profiles/{profile_id}/{photo_id}/`)
   - **blurred.jpg:** Gaussian blur (radius `photo_blur_radius`, default 14 pixels);
     shown in search results
   - **thumb.jpg:** Square thumbnail (`photo_thumb_size`, default 150×150); used in
     admin lists

### Photo settings (adjust in Admin > Settings)

| Setting | Default | Purpose |
|---------|---------|---------|
| `upload_max_mb` | 10 | Max upload file size |
| `photo_max_kb` | 500 | Max compressed JPEG size |
| `photo_passport_width` | 413 | Passport photo width |
| `photo_passport_height` | 531 | Passport photo height |
| `photo_blur_width` | 600 | Blurred variant width (preview) |
| `photo_blur_radius` | 14 | Gaussian blur amount (higher = more blurred) |
| `photo_thumb_size` | 150 | Thumbnail size (square) |
| `photos_max_per_profile` | 5 | Max photos per profile |
| `require_face_detection` | true | Enforce single-face validation |

## Monitoring

- **Error logs:** Check application logs for warnings/errors
  ```bash
  journalctl -u marathakalyanam_api.service -f
  journalctl -u marathakalyanam_web.service -f
  ```
- **Email delivery:** Verify outbound emails by checking mail server logs or test inbox
- **Pending queue:** Admin dashboard shows counts of pending profiles and detail requests;
  investigate if queue grows unexpectedly (may indicate slow review process)
- **Disk space:** Monitor `/opt/marathakalyanam/var/media/` for large photo accumulation

## Support & troubleshooting

### Can't log in?

1. Check the admin email from bootstrap logs: `journalctl -u marathakalyanam_api.service | grep BOOTSTRAP`
2. Verify email spelling and capitalization match
3. If you lost the temp password, access the server and reset via database (see
   [Password recovery](#password-recovery))

### SMTP not sending?

1. Go to **Admin > Settings** and verify:
   - `smtp_host` is correct (e.g. "mail.example.com", not "localhost")
   - `smtp_port` matches your server (465 = implicit TLS, 587 = STARTTLS)
   - `smtp_user` and `smtp_password` are correct
2. Test connectivity from the server:
   ```bash
   ssh ramboq
   telnet <smtp_host> <smtp_port>
   ```
3. Check firewall rules on both the application and SMTP servers
4. Review backend logs for SMTP errors:
   ```bash
   journalctl -u marathakalyanam_api.service | grep -i smtp
   ```

### Photos not processing or face detection failing?

1. Verify OpenCV is installed on the backend:
   ```bash
   ssh ramboq
   cd /opt/marathakalyanam/backend
   source .venv/bin/activate
   python -c "import cv2; print(cv2.__version__)"
   ```
2. Check that `/opt/marathakalyanam/var/media/` is writable:
   ```bash
   ssh ramboq
   ls -ld /opt/marathakalyanam/var/media/
   # Should show write permissions for the app user
   ```
3. Check backend logs for upload errors:
   ```bash
   journalctl -u marathakalyanam_api.service -f
   # Look for error messages during photo upload
   ```
4. If face detection is causing issues, temporarily disable in **Admin > Settings** for testing
   (not recommended for production)

### Disk space full?

1. Check available space:
   ```bash
   ssh ramboq
   df -h /opt/marathakalyanam
   ```
2. If media files are consuming space, consider:
   - Archiving old photos to backup storage
   - Running cleanup script (if available)
3. If database is full, check PostgreSQL:
   ```bash
   ssh ramboq
   du -sh /var/lib/postgresql/
   ```

### Service won't start or keeps crashing

1. Check logs for errors:
   ```bash
   journalctl -u marathakalyanam_api.service -n 50
   journalctl -u marathakalyanam_web.service -n 50
   ```
2. Verify database is accessible:
   ```bash
   ssh ramboq
   psql -U marathakalyanam -d marathakalyanam -c "SELECT 1;"
   ```
3. Manually restart the service:
   ```bash
   ssh ramboq
   systemctl restart marathakalyanam_api.service
   systemctl restart marathakalyanam_web.service
   ```

For other issues or persistent errors, contact the development team with:
- Full service logs from `journalctl`
- Error messages from the UI
- Steps to reproduce the issue
