"""ASGI application entry point."""
from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import CORS_ORIGINS
from app.db import AsyncSessionLocal, get_db_session
from app.middleware.jwt_session import JWTSessionMiddleware
from app.routes.auth import AuthController
from app.routes.profiles import ProfileController
from app.routes.photos import PhotoController
from app.routes.search import SearchController
from app.routes.requests import RequestController
from app.routes.admin import AdminController
from app.routes.media import serve_media
from app.routes.site import SiteController
from app.routes.telegram import TelegramRouter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Run bootstrap tasks on startup."""
    from app.services.bootstrap import bootstrap
    from app.services.settings import settings_service
    from app.config import MEDIA_ROOT

    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as session:
        await bootstrap(session)
        await settings_service.load(session)

    from app.services.telegram import register_webhook
    await register_webhook()

    logger.info("MarathaKalyanam backend started")
    yield
    logger.info("MarathaKalyanam backend shutting down")


@get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "marathakalyanam"}


cors_config = CORSConfig(
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


async def db_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """Provide DB session to route handlers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app = Litestar(
    route_handlers=[
        health_check,
        AuthController,
        ProfileController,
        PhotoController,
        SearchController,
        RequestController,
        AdminController,
        serve_media,
        SiteController,
        TelegramRouter,
    ],
    middleware=[JWTSessionMiddleware()],
    cors_config=cors_config,
    lifespan=[lifespan],
    dependencies={"db": db_session_dependency},
    openapi_config=OpenAPIConfig(
        title="MarathaKalyanam API",
        version="1.0.0",
        path="/docs",
    ),
    # Litestar debug=True returns full Python tracebacks on 500s, including
    # file paths and local variable values. We keep that off everywhere
    # network-reachable. Set DEBUG=1 in the local .env to opt in for dev.
    debug=os.environ.get("DEBUG", "0") == "1",
)
