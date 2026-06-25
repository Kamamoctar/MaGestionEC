import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.core.security import hash_password
from app.models.utilisateur import Utilisateur, RoleFonctionnel
from app.models.direction import Direction
from app.models.poste import Poste, NiveauAcces

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _create_user(db: AsyncSession, email: str, role: RoleFonctionnel, nom="Test", prenom="User") -> Utilisateur:
    user = Utilisateur(nom=nom, prenom=prenom, email=email, password_hash=hash_password("password123"), role_fonctionnel=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _get_token(client: AsyncClient, email: str) -> str:
    r = await client.post("/auth/token", data={"username": email, "password": "password123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]
