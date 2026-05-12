"""EmailService — aiosmtplib + Jinja2 templates.

If SMTP creds are missing or host unreachable, logs to stdout instead of raising.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
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

_IST = timezone(timedelta(hours=5, minutes=30))
_ET = timezone(timedelta(hours=-4))  # EDT; change to -5 for EST in winter


def _timestamps() -> dict[str, str]:
    now = datetime.now(timezone.utc)
    ist = now.astimezone(_IST).strftime("%-d %b %Y, %-I:%M %p IST")
    et = now.astimezone(_ET).strftime("%-d %b %Y, %-I:%M %p ET")
    return {"ist_time": ist, "et_time": et}


def _render(template_name: str, **ctx: object) -> str:
    tmpl = _jinja_env.get_template(template_name)
    site_url = settings_service.get_str("site_url", "https://marathakalyanam.com").rstrip("/")
    is_test_mode = not settings_service.get_bool("is_prod", False)
    return tmpl.render(site_url=site_url, is_test_mode=is_test_mode, **_timestamps(), **ctx)


async def _send(
    to: str,
    subject: str,
    html_body: str,
    attachments: list[tuple[bytes, str, str]] | None = None,
) -> None:
    """Send an email. Falls back to stdout if SMTP not configured."""
    if not settings_service.get_bool("is_prod", False):
        subject = f"[TEST] {subject}"
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
            timeout=30,
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


async def send_verification_email(to: str, token: str, full_name: str = "") -> None:
    ts = _timestamps()
    html = _render("verify_email.html", token=token, full_name=full_name)
    await _send(to, f"Verify your Maratha Kalyanam email · {ts['ist_time']}", html)


async def send_account_approved(to: str, full_name: str) -> None:
    ts = _timestamps()
    html = _render("account_approved.html", full_name=full_name)
    await _send(to, f"Your account is approved — Maratha Kalyanam · {ts['ist_time']}", html)


async def send_account_revoked(to: str, full_name: str) -> None:
    ts = _timestamps()
    html = _render("account_revoked.html", full_name=full_name)
    await _send(
        to,
        f"Your Maratha Kalyanam account access has been revoked · {ts['ist_time']}",
        html,
    )


async def send_account_reinstated(to: str, full_name: str, approved: bool) -> None:
    """Sent when an admin un-revokes an account. `approved` reflects whether
    the user is fully approved (email_verified was true at reinstate time)
    or still needs to verify before regaining full access."""
    ts = _timestamps()
    html = _render("account_reinstated.html", full_name=full_name, approved=approved)
    await _send(
        to,
        f"Your Maratha Kalyanam account is reinstated · {ts['ist_time']}",
        html,
    )


async def send_admin_promoted(to: str, full_name: str) -> None:
    ts = _timestamps()
    html = _render("admin_promoted.html", full_name=full_name)
    await _send(
        to,
        f"You are now a Maratha Kalyanam admin · {ts['ist_time']}",
        html,
    )


async def send_admin_demoted(to: str, full_name: str) -> None:
    ts = _timestamps()
    html = _render("admin_demoted.html", full_name=full_name)
    await _send(
        to,
        f"Your Maratha Kalyanam admin access has been removed · {ts['ist_time']}",
        html,
    )


async def send_profile_approved(
    to: str,
    profile_first_name: str,
    admin_notes: str | None,
    profile_id: str = "",
) -> None:
    ts = _timestamps()
    html = _render(
        "profile_approved.html",
        first_name=profile_first_name,
        admin_notes=admin_notes,
        profile_id=profile_id,
    )
    await _send(to, f"Your profile is approved — Maratha Kalyanam · {ts['ist_time']}", html)


async def send_profile_rejected(to: str, profile_first_name: str, admin_notes: str) -> None:
    ts = _timestamps()
    html = _render("profile_rejected.html", first_name=profile_first_name, admin_notes=admin_notes)
    await _send(to, f"Update required for your Maratha Kalyanam profile · {ts['ist_time']}", html)


async def send_detail_request_rejected(
    to: str,
    profile_first_name: str | None,
    admin_notes: str | None,
) -> None:
    ts = _timestamps()
    html = _render(
        "detail_request_rejected.html",
        profile_first_name=profile_first_name,
        admin_notes=admin_notes,
    )
    await _send(to, f"Your detail request was not approved — Maratha Kalyanam · {ts['ist_time']}", html)


async def send_detail_request_approved(
    to: str,
    profile: object,
    photos: list[object],
    photo_bytes_map: dict[str, bytes],
    requester_name: str = "",
) -> None:
    """Send full profile details with inline passport photos."""
    ts = _timestamps()
    html = _render(
        "detail_request_approved.html",
        profile=profile,
        photos=photos,
        requester_name=requester_name,
    )
    attachments: list[tuple[bytes, str, str]] = []
    for photo in photos:
        cid = f"photo_{photo.id}"  # type: ignore[attr-defined]
        raw = photo_bytes_map.get(str(photo.id), b"")  # type: ignore[attr-defined]
        if raw:
            attachments.append((raw, cid, "passport.jpg"))

    await _send(
        to,
        f"Profile details approved — Maratha Kalyanam · {ts['ist_time']}",
        html,
        attachments or None,
    )


async def send_admin_new_user(
    full_name: str,
    email: str,
    phone: str,
    user_handle: str,
) -> None:
    owner = settings_service.get_str("owner_email", "admin.marathakalyanam@gmail.com")
    ts = _timestamps()
    html = _render(
        "admin_new_user.html",
        full_name=full_name,
        email=email,
        phone=phone,
        user_handle=user_handle,
    )
    await _send(owner, f"New registration: {full_name} — Maratha Kalyanam · {ts['ist_time']}", html)


async def send_admin_profile_submitted(
    profile_name: str,
    gender: str,
    age: int,
    city: str,
    state: str,
    gotra: str,
    occupation: str,
    profile_id: str,
) -> None:
    owner = settings_service.get_str("owner_email", "admin.marathakalyanam@gmail.com")
    ts = _timestamps()
    html = _render(
        "admin_profile_submitted.html",
        profile_name=profile_name,
        gender=gender,
        age=age,
        city=city,
        state=state,
        gotra=gotra,
        occupation=occupation,
        profile_id=profile_id,
    )
    await _send(
        owner,
        f"Profile submitted for review: {profile_name} — Maratha Kalyanam · {ts['ist_time']}",
        html,
    )


async def send_admin_view_request(
    requester_name: str,
    requester_email: str,
    profile_name: str,
    profile_id: str,
    message: str | None,
) -> None:
    owner = settings_service.get_str("owner_email", "admin.marathakalyanam@gmail.com")
    ts = _timestamps()
    html = _render(
        "admin_view_request.html",
        requester_name=requester_name,
        requester_email=requester_email,
        profile_name=profile_name,
        profile_id=profile_id,
        message=message,
    )
    await _send(
        owner,
        f"View request: {requester_name} → {profile_name} — Maratha Kalyanam · {ts['ist_time']}",
        html,
    )


async def send_password_reset(to: str, token: str, full_name: str = "") -> None:
    """Send a password reset link to the user.

    Mirrors send_verification_email in structure. Falls back to stdout if
    SMTP is not configured (same _send() fallback applies).
    """
    ts = _timestamps()
    html = _render("password_reset.html", token=token, full_name=full_name)
    await _send(to, f"Reset your Maratha Kalyanam password · {ts['ist_time']}", html)


async def send_broadcast(
    to: str,
    subject: str,
    body_html: str,
    recipient_name: str,
) -> None:
    """Send a broadcast email to a single recipient using the broadcast template."""
    html = _render("broadcast.html", subject=subject, body_html=body_html, recipient_name=recipient_name)
    await _send(to, subject, html)
