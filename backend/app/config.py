"""Bootstrap configuration from environment variables only.

Runtime config (SMTP, photo limits, etc.) lives in the DB Settings table.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")
# Also load from backend dir if present
load_dotenv(Path(__file__).parent.parent / ".env")


def _require(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(f"Required env var {key!r} is not set")
    return val


DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://marathakalyanam:marathakalyanam@localhost:5432/marathakalyanam",
)

SESSION_SECRET: str = os.environ.get("SESSION_SECRET", "change-me-to-32-random-bytes-xx")

MEDIA_ROOT: Path = Path(os.environ.get("MEDIA_ROOT", "./var/media")).resolve()

OWNER_EMAIL: str = os.environ.get("OWNER_EMAIL", "ramanamborespam@gmail.com")

# CORS
CORS_ORIGINS: list[str] = os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173"
).split(",")

# Environment
ENV: str = os.environ.get("ENV", "development")
IS_PROD: bool = ENV == "production"
