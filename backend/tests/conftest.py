"""Test configuration and fixtures.

Tests run against a real PostgreSQL database (the Docker one from docker-compose).
Set TEST_DATABASE_URL env var to override.
"""
import asyncio
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://marathakalyanam:marathakalyanam@localhost:5432/marathakalyanam",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.main import app
from app.models.base import Base
from app.db import AsyncSessionLocal


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create async engine for tests — creates all tables fresh."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    """Provide a DB session that rolls back after each test."""
    async with test_engine.connect() as conn:
        transaction = await conn.begin()
        session_factory = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with session_factory() as session:
            yield session
        await transaction.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Provide an async HTTP client against the Litestar app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c
