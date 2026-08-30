import uuid
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.models.environment import Environment
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import hash_password, create_access_token
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

SEED_TEST_ENV_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
SEED_TEST_ENV_2_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

SEED_QA_USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SEED_REQUESTER_USER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed environments and users for tests
    async with TestingSessionLocal() as session:
        env1 = Environment(
            id=SEED_TEST_ENV_ID,
            code="PERF01",
            name="Performance Env 01",
            description="Test Env 01",
            active=True
        )
        env2 = Environment(
            id=SEED_TEST_ENV_2_ID,
            code="PERF02",
            name="Performance Env 02",
            description="Test Env 02",
            active=True
        )

        qa_user = User(
            id=SEED_QA_USER_ID,
            username="qa",
            password_hash=hash_password("ChangeMe123!"),
            full_name="QA Lead Manager",
            email="qa.manager@example.com",
            role=UserRole.QA,
            is_active=True
        )

        requester_user = User(
            id=SEED_REQUESTER_USER_ID,
            username="requester",
            password_hash=hash_password("ChangeMe123!"),
            full_name="Application Developer",
            email="requester@example.com",
            role=UserRole.REQUESTER,
            is_active=True
        )

        session.add_all([env1, env2, qa_user, requester_user])
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def qa_headers() -> Dict[str, str]:
    token = create_access_token({"sub": str(SEED_QA_USER_ID), "username": "qa", "role": "QA"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def requester_headers() -> Dict[str, str]:
    token = create_access_token({"sub": str(SEED_REQUESTER_USER_ID), "username": "requester", "role": "Requester"})
    return {"Authorization": f"Bearer {token}"}
