"""One-shot: copy every file under MEDIA_ROOT/profiles/* up to R2.

Usage:
    # Verify R2 settings are present in the DB then dry-run:
    python -m scripts.migrate_photos_to_r2 --dry-run

    # Actually upload:
    python -m scripts.migrate_photos_to_r2

After successful upload, flip storage_provider to "r2" via /admin/settings
or directly in the DB. Local files remain on disk untouched as a revert
safety net.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from app.config import MEDIA_ROOT
from app.db import AsyncSessionLocal
from app.services import storage as storage_svc
from app.services.settings import settings_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("migrate")


def _content_type(name: str) -> str:
    n = name.lower()
    if n.endswith(".jpg") or n.endswith(".jpeg"):
        return "image/jpeg"
    if n.endswith(".png"):
        return "image/png"
    if n.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


async def main(dry_run: bool) -> int:
    # Force-load settings + force R2 backend (independent of the active
    # storage_provider setting — we want to push to R2 regardless).
    async with AsyncSessionLocal() as s:
        await settings_service.ensure_loaded(s)

    # Build R2 directly so this script doesn't require flipping the
    # provider setting first.
    endpoint = settings_service.get_str("r2_endpoint", "")
    bucket = settings_service.get_str("r2_bucket", "")
    ak = settings_service.get_str("r2_access_key_id", "")
    sk = settings_service.get_str("r2_secret_access_key", "")
    pub = settings_service.get_str("r2_public_base_url", "")
    if not all([endpoint, bucket, ak, sk, pub]):
        log.error("R2 settings incomplete. Set r2_endpoint, r2_bucket, "
                  "r2_access_key_id, r2_secret_access_key, r2_public_base_url "
                  "in /admin/settings before running.")
        return 1

    r2 = storage_svc.R2Storage(endpoint, bucket, ak, sk, pub)
    log.info("Migrating photos from %s to R2 bucket %s", MEDIA_ROOT, bucket)

    profiles_root = MEDIA_ROOT / "profiles"
    if not profiles_root.exists():
        log.warning("No %s directory — nothing to migrate", profiles_root)
        return 0

    total = 0
    skipped = 0
    failed = 0
    for path in profiles_root.rglob("*"):
        if not path.is_file():
            continue
        # Build the storage key relative to MEDIA_ROOT (e.g., "profiles/<pid>/<photo_id>/passport.jpg")
        key = str(path.relative_to(MEDIA_ROOT))
        if dry_run:
            log.info("[dry-run] would upload %s (%d bytes)", key, path.stat().st_size)
            total += 1
            continue
        try:
            data = path.read_bytes()
            # Skip if already present and same size — cheap idempotency
            # check so re-running the script doesn't re-upload everything.
            try:
                head = r2._client.head_object(Bucket=bucket, Key=key)  # noqa: SLF001
                if int(head.get("ContentLength", -1)) == len(data):
                    skipped += 1
                    continue
            except Exception:
                pass  # not present → upload
            r2.write(key, data, content_type=_content_type(path.name))
            total += 1
            if total % 25 == 0:
                log.info("  uploaded %d files...", total)
        except Exception as exc:
            log.exception("Failed to upload %s: %s", key, exc)
            failed += 1

    log.info("Done. uploaded=%d, skipped(unchanged)=%d, failed=%d", total, skipped, failed)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="List what would be uploaded; don't write to R2")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(dry_run=args.dry_run)))
