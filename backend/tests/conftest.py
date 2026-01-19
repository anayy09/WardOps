"""
Pytest configuration and fixtures for WardOps backend tests.
"""
import asyncio
import pytest
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models.models import Base


# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with dependency overrides."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_unit_data():
    """Sample unit data for tests."""
    return {
        "name": "Test Unit A",
        "floor": 1,
        "capacity": 24,
    }


@pytest.fixture
def sample_patient_data():
    """Sample patient data for tests."""
    return {
        "mrn": "TEST001",
        "name": "Test Patient",
        "age": 45,
        "gender": "M",
        "acuity": "medium",
        "chief_complaint": "Test complaint",
        "arrival_time": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_scenario_params():
    """Sample scenario parameters for tests."""
    return {
        "name": "Test Scenario",
        "parameters": {
            "arrival_multiplier": 1.5,
            "acuity_low": 30,
            "acuity_medium": 50,
            "acuity_high": 20,
            "beds_available": 24,
            "nurses_per_shift": 6,
            "imaging_capacity": 2,
            "transport_capacity": 3,
        },
        "is_baseline": False,
    }
