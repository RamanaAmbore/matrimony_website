"""Telegram webhook endpoint."""
from __future__ import annotations

import urllib.parse
import urllib.request
from typing import Any

from litestar import Router, post
from litestar.connection import Request

from app.services.settings import settings_service


@post("/webhook")
async def telegram_webhook(data: dict[str, Any], request: Request) -> dict[str, Any]:
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
