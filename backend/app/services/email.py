"""EmailService — aiosmtplib + Jinja2 templates.

If SMTP creds are missing or host unreachable, logs to stdout instead of raising.
"""
from __future__ import annotations

import logging
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.services.settings import settings_service

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _render(template_name: str, **ctx: object) -> str:
    tmpl = _jinja_env.get_template(template_name)
    site_url = settings_service.get_str("site_url", "https://marathakalyanam.com").rstrip("/")
    return tmpl.render(site_url=site_url, **ctx)


async def _send(
    to: str,
    subject: str,
    html_body: str,
    attachments: list[tuple[bytes, str, str]] | None = None,
) -> None:
    """Send an email. Falls back to stdout if SMTP not configured."""
    smtp_host = settings_service.get_str("smtp_host", "localhost")
    smtp_port = settings_service.get_int("smtp_port", 1025)
    smtp_user = settings_service.get_str("smtp_user", "")
    smtp_password = settings_service.get("smtp_password", "")
    smtp_from = settings_service.get_str("smtp_from", "no-reply@marathakalyanam.com")

    msg: MIMEMultipart
    if attachments:
        msg = MIMEMultipart("related")
    else:
        msg = MIMEMultipart("alternative")

    msg["From"] = smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    if attachments:
        for img_bytes, cid, name in attachments:
            mime_img = MIMEImage(img_bytes)
            mime_img.add_header("Content-ID", f"<{cid}>")
            mime_img.add_header("Content-Disposition", "inline", filename=name)
            msg.attach(mime_img)

    # Check if SMTP is effectively configured
    if not smtp_host:
        logger.info(
            "[EMAIL STDOUT FALLBACK] To=%s Subject=%s\n%s", to, subject, html_body
        )
        return

    try:
        use_tls = smtp_port == 465
        start_tls = smtp_port == 587

        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user or None,
            password=str(smtp_password) if smtp_password else None,
            use_tls=use_tls,
            start_tls=start_tls,
        )
        logger.info("Email sent to %s: %s", to, subject)
    except Exception as exc:
        logger.warning(
            "SMTP failed (%s) — logging email to stdout instead. To=%s Subject=%s\n%s",
            exc,
            to,
            subject,
            html_body,
        )


async def send_verification_email(to: str, token: str) -> None:
    html = _render("verify_email.html", token=token, to=to)
    await _send(to, "Verify your MarathaKalyanam email", html)


async def send_profile_approved(to: str, profile_first_name: str, admin_notes: str | None) -> None:
    html = _render("profile_approved.html", first_name=profile_first_name, admin_notes=admin_notes)
    await _send(to, "Your profile has been approved — MarathaKalyanam", html)


async def send_profile_rejected(to: str, profile_first_name: str, admin_notes: str) -> None:
    html = _render("profile_rejected.html", first_name=profile_first_name, admin_notes=admin_notes)
    await _send(to, "Update required for your MarathaKalyanam profile", html)


async def send_detail_request_received(to: str, requester_name: str, profile_name: str) -> None:
    html = _render(
        "detail_request_received.html",
        requester_name=requester_name,
        profile_name=profile_name,
    )
    await _send(to, "New detail request — MarathaKalyanam Admin", html)


async def send_detail_request_rejected(
    to: str,
    profile_first_name: str | None,
    admin_notes: str | None,
) -> None:
    html = _render(
        "detail_request_rejected.html",
        profile_first_name=profile_first_name,
        admin_notes=admin_notes,
    )
    await _send(to, "Your detail request was not approved — MarathaKalyanam", html)


async def send_detail_request_approved(
    to: str,
    profile: object,
    photos: list[object],
    photo_bytes_map: dict[str, bytes],
) -> None:
    """Send full profile details with inline passport photos."""
    html = _render(
        "detail_request_approved.html",
        profile=profile,
        photos=photos,
    )
    attachments: list[tuple[bytes, str, str]] = []
    for photo in photos:
        cid = f"photo_{photo.id}"  # type: ignore[attr-defined]
        raw = photo_bytes_map.get(str(photo.id), b"")  # type: ignore[attr-defined]
        if raw:
            attachments.append((raw, cid, "passport.jpg"))

    await _send(to, "Profile details approved — MarathaKalyanam", html, attachments or None)
