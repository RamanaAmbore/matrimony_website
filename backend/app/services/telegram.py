"""Telegram notification service — fire-and-forget admin alerts."""
from __future__ import annotations

import asyncio
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from app.services.settings import settings_service

logger = logging.getLogger(__name__)

_IST = timezone(timedelta(hours=5, minutes=30))
_EDT = timezone(timedelta(hours=-4))


def _now_times() -> str:
    now = datetime.now(timezone.utc)
    ist = now.astimezone(_IST).strftime("%d %b %Y %I:%M %p IST")
    edt = now.astimezone(_EDT).strftime("%I:%M %p EDT")
    return f"{ist} · {edt}"


async def _send(text: str) -> None:
    token = settings_service.get_str("matrimony_tg_token", "")
    chat_id = settings_service.get_str("matrimony_tg_chat_id", "")
    if not token or not chat_id:
        return
    if not settings_service.get_bool("matrimony_tg_enabled", True):
        return

    def _post() -> None:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _post)
    except Exception as exc:
        logger.warning("Telegram send failed: %s", exc)


async def notify_user_registered(name: str, email: str, phone: str) -> None:
    await _send(
        f"🆕 <b>New Registration</b>\n{name}\n{email} | {phone}\n{_now_times()}"
    )


async def notify_profile_submitted(profile_id: str, name: str, gender: str) -> None:
    code = profile_id.replace("-", "")[:5].upper()
    mc_code = f"MC-{code}"
    await _send(
        f"📋 <b>Profile Submitted</b>\n{mc_code} — {name} ({gender})\nAwaiting review\n{_now_times()}"
    )


async def notify_profile_approved(name: str, admin_notes: str = "") -> None:
    notes = f"\n{admin_notes}" if admin_notes else ""
    await _send(
        f"✅ <b>Profile Approved</b>\n{name}{notes}\n{_now_times()}"
    )


async def notify_profile_rejected(name: str, admin_notes: str = "") -> None:
    notes = f"\n{admin_notes}" if admin_notes else ""
    await _send(
        f"❌ <b>Profile Rejected</b>\n{name}{notes}\n{_now_times()}"
    )


async def notify_request_received(requester: str, profile_name: str) -> None:
    await _send(
        f"👁 <b>View Request</b>\nFrom: {requester}\nFor: {profile_name}\n{_now_times()}"
    )


async def notify_request_approved(requester: str, profile_name: str) -> None:
    await _send(
        f"✅ <b>View Request Approved</b>\n{requester} → {profile_name}\n{_now_times()}"
    )


async def notify_request_rejected(requester: str, profile_name: str) -> None:
    await _send(
        f"❌ <b>View Request Rejected</b>\n{requester} → {profile_name}\n{_now_times()}"
    )


async def register_webhook() -> None:
    """Register the bot webhook with Telegram on startup."""
    from app.config import IS_PROD

    token = settings_service.get_str("matrimony_tg_token", "")
    if not token:
        return
    if not IS_PROD:
        return

    base_url = "https://marathakalyanam.com/api/telegram/webhook"

    def _set() -> None:
        data = urllib.parse.urlencode({"url": base_url}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/setWebhook",
            data=data,
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _set)
        logger.info("Telegram webhook registered")
    except Exception as exc:
        logger.warning("Failed to register Telegram webhook: %s", exc)
