"""Profile → PDF rendering for admin/super dashboards.

Renders a beautiful single-document dossier of a profile (demographics,
astrology, family, photos, owner contact). WeasyPrint converts the
Jinja2-templated HTML to a print-quality PDF.

Photos are read via storage_svc and embedded as base64 data URLs so the
output works whether the storage backend is local disk or Cloudflare R2
(R2 signed URLs would otherwise expire).

Usage:
    pdf_bytes = await render_profile_pdf(profile)

System dependencies (server install):
    apt install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \\
                   libfontconfig1 libgdk-pixbuf-2.0-0
"""
from __future__ import annotations

import asyncio
import base64
import logging
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.profile import Profile
from app.services import storage as storage_svc
from app.services.settings import settings_service

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "pdf"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _calc_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _fmt_height(cm: int | None) -> str:
    if not cm:
        return "—"
    inches_total = round(cm / 2.54)
    feet, inches = divmod(inches_total, 12)
    return f"{cm} cm ({feet}′{inches}″)"


def _fmt_income(inr: int | None) -> str:
    if inr is None:
        return "—"
    if inr >= 10_00_000:
        return f"₹{inr / 1_00_00_000:.2f} Cr"
    if inr >= 1_00_000:
        return f"₹{inr / 1_00_000:.2f} L"
    return f"₹{inr:,}"


def _enum_or_dash(v) -> str:
    if v is None:
        return "—"
    val = getattr(v, "value", v)
    return str(val).replace("_", " ").title() if val else "—"


def _str_or_dash(v) -> str:
    return str(v) if v not in (None, "") else "—"


async def _photo_data_url(key: str) -> str | None:
    """Read photo bytes from active storage backend; return as data URL."""
    try:
        data = await storage_svc.read_async(key)
    except Exception as exc:
        logger.warning("PDF: failed to read photo %s: %s", key, exc)
        return None
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")


async def render_profile_pdf(profile: Profile) -> bytes:
    """Render a Profile (with `photos` and `owner` eager-loaded) to PDF bytes."""
    # Sort photos: primary first, then by created_at.
    photos_sorted = sorted(profile.photos or [], key=lambda p: (not p.is_primary, p.created_at))
    primary_photo = photos_sorted[0] if photos_sorted else None

    # Read passport variants in parallel — they're served from the storage
    # backend and may incur network latency in R2 mode.
    photo_urls: list[str | None] = []
    if photos_sorted:
        photo_urls = await asyncio.gather(
            *(_photo_data_url(p.passport_path) for p in photos_sorted)
        )

    owner = getattr(profile, "owner", None)

    ctx = {
        "p": profile,
        "owner": owner,
        "age": _calc_age(profile.dob),
        "height_str": _fmt_height(profile.height_cm),
        "income_str": _fmt_income(profile.annual_income_inr),
        "photos": [
            {
                "data_url": url,
                "is_primary": photo.is_primary,
            }
            for photo, url in zip(photos_sorted, photo_urls, strict=True)
            if url is not None
        ],
        "primary_photo_url": (
            photo_urls[photos_sorted.index(primary_photo)]
            if primary_photo and photo_urls and photo_urls[photos_sorted.index(primary_photo)]
            else None
        ),
        "site_url": settings_service.get_str(
            "site_url", "https://marathakalyanam.com"
        ).rstrip("/"),
        "generated_at": datetime.now().strftime("%-d %b %Y, %-I:%M %p"),
        "fmt_enum": _enum_or_dash,
        "fmt_str": _str_or_dash,
    }

    template = _jinja_env.get_template("profile.html")
    html_str = template.render(**ctx)

    # WeasyPrint blocks; offload to a thread.
    def _render() -> bytes:
        from weasyprint import HTML  # imported lazily — heavy module

        return HTML(string=html_str, base_url=str(TEMPLATES_DIR)).write_pdf()

    return await asyncio.to_thread(_render)


def safe_pdf_filename(profile: Profile) -> str:
    """Filename safe across Mac/Win/Linux."""
    pieces = [profile.profile_number or "profile", profile.first_name or "", profile.last_name or ""]
    base = "_".join(p for p in pieces if p).strip("_")
    base = "".join(c if c.isalnum() or c in "_-." else "_" for c in base)
    return f"{base or 'profile'}.pdf"
