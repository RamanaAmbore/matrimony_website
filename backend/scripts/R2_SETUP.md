# Cloudflare R2 setup for photo storage

Phase 1 (storage abstraction) is deployed. To switch from local disk to R2,
follow this checklist.

## 1. Create the R2 bucket

1. Cloudflare dashboard → **R2** → **Create bucket**.
2. Name: `marathakalyanam-photos` (or any DNS-safe slug).
3. Location hint: leave default (auto), or pick a region closest to users.
4. Enable **Public access** → **Allow Access** via the **r2.dev URL**, OR
   set up a **Custom domain** like `r2.marathakalyanam.com` (recommended
   for stable URLs and CDN warming).

After creation, note the **public bucket URL**:

- r2.dev: `https://pub-XXXXXXXXXXXXXXXXXXX.r2.dev`
- Custom domain: `https://r2.marathakalyanam.com`

## 2. Create an R2 API token

1. Cloudflare dashboard → **R2** → **Manage R2 API Tokens** → **Create API Token**.
2. Permissions: **Object Read & Write**.
3. Specify the bucket scope: just `marathakalyanam-photos`.
4. TTL: leave default (no expiry).
5. Click **Create**. **Copy these values once — they won't be shown again:**

```
Access Key ID:        ........................
Secret Access Key:    ........................................
Account ID:           ........................
Endpoint (S3 API):    https://<account-id>.r2.cloudflarestorage.com
```

## 3. Plug values into the running app

Either via `/admin/settings` UI or directly via SQL on prod. In settings:

| Key | Value |
|---|---|
| `r2_endpoint` | `https://<account-id>.r2.cloudflarestorage.com` |
| `r2_bucket` | `marathakalyanam-photos` |
| `r2_access_key_id` | (token's access key) |
| `r2_secret_access_key` | (token's secret) — masked in the UI |
| `r2_public_base_url` | `https://r2.marathakalyanam.com` *(or pub-xxx.r2.dev)* |
| `r2_signed_url_ttl_sec` | `3600` (default; how long passport signed URLs live) |

**Do not flip `storage_provider` to `r2` yet** — first migrate the existing
photos.

## 4. Migrate existing local photos to R2

Once the credentials are set, copy what's already on disk:

```bash
ssh ramboq "cd /opt/marathakalyanam/backend && source .venv/bin/activate && \
  python -m scripts.migrate_photos_to_r2 --dry-run"      # preview

ssh ramboq "cd /opt/marathakalyanam/backend && source .venv/bin/activate && \
  python -m scripts.migrate_photos_to_r2"                # actual upload
```

The script is idempotent — re-running skips files that already match in R2.
Local files are **not** deleted by the script.

## 5. Flip the active backend

In `/admin/settings`, change `storage_provider` from `local` to `r2`.
Effective immediately — the next API call returns R2 URLs and the next
upload writes to R2.

## 6. Verify

- Open `/search` (anonymous): blurred photos should render from
  `r2.marathakalyanam.com/...`
- Open a profile detail page (logged in): passport photos should render
  from a `?X-Amz-Signature=...` URL on the same host.
- Upload a fresh photo via My Profiles → Edit. Confirm the new file
  appears in the R2 bucket browser.

## To revert

Flip `storage_provider` back to `local`. Local files are still on disk
(the migration didn't touch them), so the site reverts cleanly. The
files written to R2 between flip and revert are orphaned in the bucket
— purge manually if needed.

## To purge local files (only after R2 is proven stable)

```bash
ssh ramboq "rm -rf /opt/marathakalyanam/var/media/profiles/*"
```

Once this is done, reverting to `local` will give 404s on existing
photos. Don't run the purge until you're committed.
