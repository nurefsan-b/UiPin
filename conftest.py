import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio
from typing import AsyncGenerator

# Main ve Database dosyalarından importlar
from main import app
from database import get_db, Base 

# ✅ DOĞRU AYAR: PostgreSQL
# Kullanıcı adı (postgres) ve şifreni (SIFRENIZ) girmeyi unutma!
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:SIFRENIZ@localhost/uipin_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    await init_db()
    yield
    await drop_db()

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
async def client() -> AsyncGenerator:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac