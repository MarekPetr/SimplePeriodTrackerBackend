import pytest
import pytest_asyncio
import re
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

# Test database URL - using a separate test database
# Parse the production URL and replace only the database name
if "/period_tracker" in settings.database_url:
    TEST_DATABASE_URL = "postgresql+asyncpg://period_tracker_user:yourpassword@localhost:5432/period_tracker"
else:
    # Handle URLs that don't have /period_tracker in them
    # Replace the database name at the end of the URL
    TEST_DATABASE_URL = re.sub(r'/[^/]+$', '/period_tracker_test', settings.database_url)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

# Create test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    Creates tables before test, drops them after.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an AsyncClient for testing API endpoints.
    Overrides the get_db dependency to use test database.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(client: AsyncClient) -> dict:
    """
    Create a test user and return user data with tokens.
    """
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "gender": "woman",
    }

    # Register user
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    user = response.json()

    # Login to get tokens
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()

    return {
        "user": user,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "email": user_data["email"],
        "password": user_data["password"],
    }


@pytest_asyncio.fixture
async def auth_headers(test_user: dict) -> dict:
    """
    Return authorization headers for authenticated requests.
    """
    return {"Authorization": f"Bearer {test_user['access_token']}"}
