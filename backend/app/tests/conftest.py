import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import get_settings
from app.core.database import get_db
from app.core import security
from app.models.user import User, UserRole

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db) -> Generator:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helper fixtures ────────────────────────────────────────────────────────────

def _make_user(db, login: str, email: str, role: UserRole, is_active: bool = True) -> User:
    user = User(
        login=login,
        email=email,
        hashed_password=security.hash_password("Password123!"),
        first_name="Test",
        last_name="User",
        role=role,
        is_active=is_active,
        must_change_password=False,
    )
    db.add(user)
    db.flush()   # get id without committing
    return user


def _token_headers(user: User) -> dict:
    token = security.create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer(db):
    return _make_user(db, "viewer_fix", "viewer@test.com", UserRole.VIEWER)

@pytest.fixture
def commercial(db):
    return _make_user(db, "commercial_fix", "commercial@test.com", UserRole.COMMERCIAL)

@pytest.fixture
def operator(db):
    return _make_user(db, "operator_fix", "operator@test.com", UserRole.OPERATOR)

@pytest.fixture
def admin(db):
    return _make_user(db, "admin_fix", "admin@test.com", UserRole.ADMIN)

@pytest.fixture
def super_admin(db):
    return _make_user(db, "superadmin_fix", "superadmin@test.com", UserRole.SUPER_ADMIN)
