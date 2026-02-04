"""
Pytest configuration and fixtures.
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.models import Base
from app.database import get_db
from app.config import get_settings


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://grocery:grocery@localhost:5432/grocery_test"


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
        poolclass=NullPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers() -> dict:
    """Headers for admin API requests."""
    settings = get_settings()
    return {"X-Admin-API-Key": settings.ADMIN_API_KEY}


@pytest.fixture
async def sample_category(db_session: AsyncSession):
    """Create a sample category."""
    from app.models.product import Category
    
    category = Category(
        name="Test Category",
        slug="test-category",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture
async def sample_product(db_session: AsyncSession, sample_category):
    """Create a sample product."""
    from app.models.product import Product
    from decimal import Decimal
    
    product = Product(
        name="Test Product",
        slug="test-product",
        price=Decimal("29.99"),
        unit="stk",
        category_id=sample_category.id,
        stock_quantity=100,
        is_active=True
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest.fixture
async def sample_postcode(db_session: AsyncSession):
    """Create a sample service postcode."""
    from app.models.address import ServicePostcode
    from decimal import Decimal
    
    postcode = ServicePostcode(
        postcode="2100",
        city="København Ø",
        is_active=True,
        delivery_fee=Decimal("0"),
        min_order_amount=Decimal("200")
    )
    db_session.add(postcode)
    await db_session.commit()
    await db_session.refresh(postcode)
    return postcode


@pytest.fixture
async def sample_user(db_session: AsyncSession):
    """Create a sample user."""
    from app.models.user import User
    
    user = User(
        firebase_uid="test_firebase_uid",
        email="test@example.com",
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_address(db_session: AsyncSession, sample_user, sample_postcode):
    """Create a sample address."""
    from app.models.address import Address
    
    address = Address(
        user_id=sample_user.id,
        label="Hjem",
        street="Østerbrogade 123",
        postcode=sample_postcode.postcode,
        city=sample_postcode.city,
        is_default=True
    )
    db_session.add(address)
    await db_session.commit()
    await db_session.refresh(address)
    return address
