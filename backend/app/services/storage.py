"""Photo storage backend — abstracts local-disk vs Cloudflare R2 (S3 API).

Two implementations are exposed via the `get_storage()` factory:

  * LocalStorage  — writes to MEDIA_ROOT on the host filesystem. Default.
                    Behaviour matches the pre-R2 code exactly.
  * R2Storage     — writes to a Cloudflare R2 bucket via the S3-compatible
                    API. Public-read URLs are served from a configured base
                    domain (custom domain or pub-XXX.r2.dev). The
                    "passport" variant uses signed URLs with a short TTL so
                    privacy stays gated even though objects can be public.

Active backend is chosen by the `storage_provider` setting:
  - "local" (default)
  - "r2"

To revert from R2 → local, flip the setting back. Local files remain on
disk after migration as a safety net until explicitly purged.

Settings consumed (all read via settings_service):
  storage_provider          local | r2
  r2_endpoint               https://<account-id>.r2.cloudflarestorage.com
  r2_bucket                 bucket name
  r2_access_key_id          R2 token access key (sensitive)
  r2_secret_access_key      R2 token secret (sensitive — masked in /admin/settings)
  r2_public_base_url        https://r2.marathakalyanam.com  (or pub-xxx.r2.dev)
  r2_signed_url_ttl_sec     default 3600 (1 hour)
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import MEDIA_ROOT
from app.services.settings import settings_service

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Raised when a storage backend op fails."""


class StorageBackend(ABC):
    """Minimal interface every backend implements."""

    @abstractmethod
    def write(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        """Persist `data` under `key`. Overwrites if exists."""

    @abstractmethod
    def read(self, key: str) -> bytes:
        """Return raw bytes at `key`, or raise StorageError on miss."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Best-effort delete. No-op if not found."""

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def public_url(self, key: str) -> str:
        """URL for non-private variants (blurred, thumb). Cacheable."""

    @abstractmethod
    def private_url(self, key: str) -> str:
        """URL for the passport variant. Caller must already be auth-gated;
        this returns a URL bearer (e.g., signed URL with short TTL) that is
        safe to embed in an authorized response body."""


# ────────────────────────────────────────────────────────────────────────────
#  Local disk
# ────────────────────────────────────────────────────────────────────────────

class LocalStorage(StorageBackend):
    """Writes files under MEDIA_ROOT, serves them via the existing /media/*
    Litestar route. URLs are relative-host like
    https://marathakalyanam.com/media/profiles/<pid>/<photo_id>/passport.jpg.

    The "private" variant adds Cache-Control: private,no-store on the wire
    via routes/media.py — defense against Cloudflare caching the passport
    image after auth state changes."""

    def __init__(self, media_root: Path, public_base: str) -> None:
        self._root = media_root
        self._public_base = public_base.rstrip("/")

    def write(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        target = self._root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def read(self, key: str) -> bytes:
        target = self._root / key
        try:
            return target.read_bytes()
        except OSError as exc:
            raise StorageError(f"Cannot read {key}: {exc}") from exc

    def delete(self, key: str) -> None:
        target = self._root / key
        if target.exists():
            try:
                target.unlink()
            except OSError as exc:
                logger.warning("Failed to delete %s: %s", target, exc)
        # Best-effort: prune empty parent dirs up to MEDIA_ROOT.
        parent = target.parent
        while parent.is_relative_to(self._root) and parent != self._root:
            try:
                if not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
                else:
                    break
            except OSError:
                break

    def exists(self, key: str) -> bool:
        return (self._root / key).exists()

    def public_url(self, key: str) -> str:
        return f"{self._public_base}/media/{key}"

    def private_url(self, key: str) -> str:
        # Same URL — privacy is enforced by the /media handler's auth check
        # (or absence of one — local serving currently doesn't gate). For
        # local, "private" and "public" URLs are the same; gate at the
        # API-response layer instead by emitting None for unauthorized
        # callers.
        return self.public_url(key)


# ────────────────────────────────────────────────────────────────────────────
#  Cloudflare R2 (S3-compatible)
# ────────────────────────────────────────────────────────────────────────────

class R2Storage(StorageBackend):
    """Writes to an R2 bucket via boto3 (S3 API). Public URLs are served
    from `r2_public_base_url`; private (passport) URLs are S3 presigned GET
    URLs with TTL.

    The bucket should be configured with public-read access for the public
    URL host to work, or behind a Cloudflare custom domain that allows
    anonymous GETs. The signed URL bypasses any access controls so works
    regardless.
    """

    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
        public_base_url: str,
        signed_ttl_seconds: int = 3600,
    ) -> None:
        # Lazy import keeps boto3 out of the hot path for local-only deploys
        import boto3  # type: ignore

        self._bucket = bucket
        self._public_base = public_base_url.rstrip("/")
        self._signed_ttl = signed_ttl_seconds
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    def write(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                # Long browser cache for the immutable variant URLs (each
                # photo has a unique UUID in the path; a new upload writes
                # to a new path).
                CacheControl="public, max-age=31536000, immutable",
            )
        except Exception as exc:
            raise StorageError(f"R2 put_object failed for {key}: {exc}") from exc

    def read(self, key: str) -> bytes:
        try:
            obj = self._client.get_object(Bucket=self._bucket, Key=key)
            return obj["Body"].read()
        except Exception as exc:
            raise StorageError(f"R2 get_object failed for {key}: {exc}") from exc

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception as exc:
            logger.warning("R2 delete_object failed for %s: %s", key, exc)

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    def public_url(self, key: str) -> str:
        return f"{self._public_base}/{key}"

    def private_url(self, key: str) -> str:
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=self._signed_ttl,
            )
        except Exception as exc:
            raise StorageError(f"R2 sign_url failed for {key}: {exc}") from exc


# ────────────────────────────────────────────────────────────────────────────
#  Factory + thin async wrappers
# ────────────────────────────────────────────────────────────────────────────

def _build() -> StorageBackend:
    provider = settings_service.get_str("storage_provider", "local").lower()
    if provider == "r2":
        endpoint = settings_service.get_str("r2_endpoint", "")
        bucket = settings_service.get_str("r2_bucket", "")
        ak = settings_service.get_str("r2_access_key_id", "")
        sk = settings_service.get_str("r2_secret_access_key", "")
        pub = settings_service.get_str("r2_public_base_url", "")
        ttl = settings_service.get_int("r2_signed_url_ttl_sec", 3600)
        if not all([endpoint, bucket, ak, sk, pub]):
            logger.warning(
                "storage_provider=r2 but R2 settings incomplete; falling back to local"
            )
            return _local()
        return R2Storage(endpoint, bucket, ak, sk, pub, ttl)
    return _local()


def _local() -> StorageBackend:
    public_base = settings_service.get_str("site_url", "https://marathakalyanam.com")
    return LocalStorage(MEDIA_ROOT, public_base)


def get_storage() -> StorageBackend:
    """Build a fresh backend on each call. Cheap (LocalStorage is just two
    fields; R2Storage caches a boto3 client per instance but constructing
    a new client is also cheap). No global cache because flipping
    storage_provider via /admin/settings should take effect immediately."""
    return _build()


# ── Async helpers ────────────────────────────────────────────────────────
# All boto3 calls block the event loop, so wrap in asyncio.to_thread.

async def write_async(key: str, data: bytes, content_type: str = "image/jpeg") -> None:
    storage = get_storage()
    await asyncio.to_thread(storage.write, key, data, content_type)


async def read_async(key: str) -> bytes:
    storage = get_storage()
    return await asyncio.to_thread(storage.read, key)


async def delete_async(key: str) -> None:
    storage = get_storage()
    await asyncio.to_thread(storage.delete, key)
