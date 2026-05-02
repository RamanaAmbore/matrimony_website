# marathakalyanam — admin guide

Operational guide for administrators of Maratha Kalyanam.

## Admin role

An administrator has access to the **Admin** dashboard and can approve profiles, approve detail
requests, manage users, and adjust settings.

### Who can be an admin?

Currently, the first admin is bootstrapped automatically on initial deployment (see
[First-time bootstrap](#first-time-bootstrap)).

### Promoting another user to admin

1. Log in as an admin
2. Go to **Admin > Users**
3. Find the user you want to promote
4. Click **Promote**
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
| owner_email | string | ramanamborespam@gmail.com | Recipient for admin notifications (profile requests, rejections, etc.) | Yes |
| smtp_host | string | localhost | SMTP server hostname (e.g. "mail.example.com"). **IMPORTANT: Never hardcode in code; always set here.** | Yes |
| smtp_port | int | 1025 | SMTP port (465 = implicit TLS, 587 = STARTTLS) | Yes |
| smtp_user | string | (empty) | SMTP auth username (leave blank if not needed) | Yes |
| smtp_password | string | (empty) | SMTP auth password. **MASKED in UI (shown as `***` if set).** Edit only via this page, never in code. | Yes |
| smtp_from | string | no-reply@marathakalyanam.com | "From:" email address in outbound mail | Yes |
| photo_max_kb | int | 500 | Max JPEG size after compression (KB). Smaller = faster upload/load but lower quality. | Yes |
| photo_passport_width | int | 413 | Passport photo width (pixels) | No |
| photo_passport_height | int | 531 | Passport photo height (pixels) | No |
| photo_blur_width | int | 600 | Blurred variant width (pixels, for search results) | Yes |
| photo_blur_radius | int | 14 | Gaussian blur radius (pixels); higher = more blurred | Yes |
| photo_thumb_size | int | 150 | Thumbnail size (square, pixels, for admin interface) | Yes |
| photos_max_per_profile | int | 5 | Max photos per profile | Yes |
| upload_max_mb | int | 10 | Max file upload size (MB) | Yes |
| require_face_detection | bool | true | Enforce single-face photo validation via OpenCV. If false, any photo is accepted. | Yes |
| require_admin_approval_for_profiles | bool | true | If true: profiles go to pending on submit, admin must approve. If false: auto-approve on submit. | Yes |

### Common adjustments

- **Slow email delivery?** Check `smtp_host`, `smtp_port`, and credentials.
- **Photos too large?** Reduce `photo_max_kb` or `photo_passport_width`.
- **Too many spam profiles?** Set `require_admin_approval_for_profiles` to `true` (already default).
- **Turn off face detection for testing?** Set `require_face_detection` to `false` (not recommended for production).

**⚠️ SMTP credentials are sensitive:** never log them, never put them in `.env` (bootstrap secrets only). Use the Settings UI.

## First-time bootstrap

On first run (fresh database), the app automatically:

1. Creates the database schema (via Alembic migration)
2. Seeds default settings from [CLAUDE.md#settings-keys](CLAUDE.md#settings-keys)
3. Creates a bootstrap admin user at the `OWNER_EMAIL` address

You'll see a log message like:

```
======================================================
BOOTSTRAP ADMIN CREATED
Email: ramanamborespam@gmail.com
Temporary password: aB3XyZ9kL2qP5wX
One-time reset token: 12345abcdef...
Change your password immediately after first login.
======================================================
```

**Next steps:**

1. Log in at http://marathakalyanam.com/login with:
   - Email: `ramanamborespam@gmail.com` (or your `OWNER_EMAIL`)
   - Password: (the temp password from logs)
2. Go to account settings and change your password immediately
3. Update `owner_email` setting if you want notifications sent elsewhere
4. Configure SMTP settings (go to **Admin > Settings**):
   - Set `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`
   - Test by submitting a profile; you should receive an approval notification

**Password reset:** If you lose your password, you'll need to:
- Access the database directly: `UPDATE users SET password_hash = ... WHERE email = ...`
- Or have an existing admin reset it (future feature)

## Deploy runbook (placeholder)

Production deployment will be on a remote server. This section will contain:

- SSH setup and host details
- nginx vhost configuration (marathakalyanam.com)
- systemd service unit (auto-restart, logging)
- certbot SSL/TLS setup
- Database backup strategy
- Log rotation

**Target deployment host:** ramboq server
**Target domain:** marathakalyanam.com

*Details to be filled in once SSH access is configured.*

## Backups

Maratha Kalyanam has two critical components that must be backed up:

### 1. Database (PostgreSQL)

Backup the entire database regularly:

```bash
# Full database dump
pg_dump -h localhost -U marathakalyanam -d marathakalyanam \
  > /backups/marathakalyanam_$(date +%Y%m%d_%H%M%S).sql

# Compress
gzip /backups/marathakalyanam_*.sql

# Example: daily backup via cron
0 2 * * * pg_dump -h localhost -U marathakalyanam -d marathakalyanam \
  | gzip > /backups/mk_$(date +\%Y\%m\%d).sql.gz
```

### 2. Media files (photos)

All uploaded photos are stored in the `MEDIA_ROOT` directory (default: `./var/media`). Back up
the entire directory:

```bash
# Rsync to backup server
rsync -av --delete /path/to/marathakalyanam/var/media/ \
  backup-user@backup-server:/backups/marathakalyanam-media/

# Example: daily backup via cron
0 3 * * * rsync -av --delete /var/marathakalyanam/media/ \
  backup-user@backup.example.com:/backups/marathakalyanam-media/
```

### Retention

- Keep database backups for at least 30 days (roll off old ones)
- Keep media backups synced continuously (rsync --delete removes orphaned files)
- Test restore procedures monthly

### Disaster recovery

To restore from backup:

```bash
# 1. Restore database
gunzip < /backups/marathakalyanam_YYYYMMDD.sql.gz | \
  psql -h localhost -U marathakalyanam -d marathakalyanam

# 2. Restore media files
rsync -av /backups/marathakalyanam-media/ \
  /path/to/marathakalyanam/var/media/
```

## Monitoring

- **Error logs:** Check application logs for warnings/errors
  - Local dev: stdout (console)
  - Production: systemd journal or log file (to be configured)
- **Email delivery:** Check Mailhog UI (dev) or mail server logs (prod)
- **Pending queue:** Admin dashboard shows count of pending profiles and requests; investigate
  if queue grows unexpectedly

## Support and troubleshooting

**Can't log in?** Check `OWNER_EMAIL` in bootstrap logs; verify email spelling.

**SMTP not sending?** Go to **Admin > Settings** and verify `smtp_host`, `smtp_port`,
credentials. Test with a simple email first. Check firewall/network access to SMTP server.

**Photos not processing?** Check that OpenCV is installed (`pip install pillow opencv-python`).
Verify `MEDIA_ROOT` is writable.

**Database full?** Check disk space on PostgreSQL host. Archive old photos if needed.

For other issues, contact the development team.
