"""JWT session middleware.

Reads the ``mk_jwt`` cookie on every request.  If the token is present and
valid the decoded payload is stored at ``request.scope["user_payload"]`` so
that downstream route handlers and dependency providers can read it.

Invalid or missing cookies are silently ignored — authentication enforcement
is the responsibility of individual route guards and dependency providers.
"""
from __future__ import annotations

from typing import Any

from litestar.middleware import ASGIMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send

from app.services.jwt_auth import decode_jwt

_COOKIE_NAME = "mk_jwt"


class JWTSessionMiddleware(ASGIMiddleware):
    """Parse the JWT cookie and inject the payload into request scope."""

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        if scope["type"] in ("http", "websocket"):
            # Extract cookie header — headers is a list of (name, value) byte tuples
            cookie_header = ""
            for name, value in scope.get("headers", []):
                if name.lower() == b"cookie":
                    cookie_header = value.decode("latin-1")
                    break

            payload: dict[str, Any] | None = None
            if cookie_header:
                for part in cookie_header.split(";"):
                    part = part.strip()
                    if part.startswith(f"{_COOKIE_NAME}="):
                        token = part[len(f"{_COOKIE_NAME}="):]
                        payload = decode_jwt(token)
                        break

            scope["user_payload"] = payload  # None if absent/invalid

        await next_app(scope, receive, send)
