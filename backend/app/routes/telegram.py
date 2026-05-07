"""Telegram webhook endpoint."""
from __future__ import annotations

import hmac
import logging
import urllib.parse
import urllib.request
from typing import Any

from litestar import Router, post
from litestar.connection import Request
from litestar.exceptions import HTTPException

from app.services.settings import settings_service

logger = logging.getLogger(__name__)


@post("/webhook")
async def telegram_webhook(data: dict[str, Any], request: Request) -> dict[str, Any]:
    # Telegram echoes the secret we registered with setWebhook into the
    # X-Telegram-Bot-Api-Secret-Token header on every delivery. We refuse
    # the request unless it matches — without this, the endpoint accepts
    # arbitrary JSON from the public internet.
    expected = settings_service.get_str("matrimony_tg_webhook_secret", "")
    received = request.headers.get("x-telegram-bot-api-secret-token", "")
    if not expected or not received or not hmac.compare_digest(expected, received):
        # Don't reveal whether the secret is configured vs. mismatched.
        logger.warning("telegram webhook: rejected (secret mismatch / not configured)")
        raise HTTPException(status_code=401, detail={"code": "unauthorized"})

    try:
        message = data.get("message") or data.get("edited_message", {})
        text = message.get("text", "") if isinstance(message, dict) else ""
        chat = message.get("chat", {}) if isinstance(message, dict) else {}
        chat_id = chat.get("id")

        if chat_id and text and (text.startswith("/start") or text.startswith("/chatid")):
            token = settings_service.get_str("matrimony_tg_token", "")
            if token:
                reply = (
                    f"Your chat ID is: <code>{chat_id}</code>\n"
                    "Configure this in Admin → Settings → matrimony_tg_chat_id"
                )
                post_data = urllib.parse.urlencode({
                    "chat_id": chat_id,
                    "text": reply,
                    "parse_mode": "HTML",
                }).encode()
                req = urllib.request.Request(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data=post_data,
                )
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        resp.read()
                except Exception:
                    pass
    except Exception:
        pass

    return {"ok": True}


TelegramRouter = Router(path="/telegram", route_handlers=[telegram_webhook])
