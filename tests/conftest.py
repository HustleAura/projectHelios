"""
Shared test fixtures for Project Helios.

Provides:
- Async test database session (uses a separate test DB or transactions)
- Mocked Firebase token verification (bypasses real Firebase in tests)
- httpx AsyncClient wired to the FastAPI app
- Pre-created test user
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import app
from app.models import Base
from app.models.user import User

# Use the same DB URL for tests — in CI you'd point this to a test-specific DB.
# For local dev, you can override via TEST_DATABASE_URL env var.
TEST_DATABASE_URL = settings.DATABASE_URL

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_test = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)

# ---------------------------------------------------------------------------
# Fake Firebase user for tests
# ---------------------------------------------------------------------------
FAKE_FIREBASE_UID = "test-firebase-uid-12345"
FAKE_EMAIL = "testuser@example.com"


def _mock_verify_firebase_token(token: str) -> dict:
    """Return fake decoded Firebase token claims."""
    if token == "invalid":
        raise Exception("Invalid token")
    return {
        "uid": FAKE_FIREBASE_UID,
        "email": FAKE_EMAIL,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_db():
    """Create all tables before tests, drop after."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    async with async_session_test() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    httpx AsyncClient with:
      - DB session override (uses the test session)
      - Firebase token verification mocked
    """

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with patch(
        "app.dependencies.verify_firebase_token",
        side_effect=_mock_verify_firebase_token,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"Authorization": "Bearer test-token"},
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create and return a test user in the database."""
    user = User(
        firebase_uid=FAKE_FIREBASE_UID,
        email=FAKE_EMAIL,
    )
    db_session.add(user)
    await db_session.flush()
    return user
