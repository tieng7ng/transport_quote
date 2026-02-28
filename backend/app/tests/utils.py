"""
Utilitaires partagés entre les tests.
"""
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.core import security


TEST_PASSWORD = "Password123!"


def create_test_user(
    db: Session,
    login: str = "testuser",
    email: str = "test@transport-quote.com",
    role: str = "VIEWER",
    is_active: bool = True,
    must_change_password: bool = False,
) -> User:
    """Crée (ou retourne si déjà existant) un utilisateur de test."""
    user = db.query(User).filter(User.login == login).first()
    if user:
        return user

    user = User(
        login=login,
        email=email,
        hashed_password=security.hash_password(TEST_PASSWORD),
        first_name="Test",
        last_name="User",
        role=UserRole(role),
        is_active=is_active,
        must_change_password=must_change_password,
    )
    db.add(user)
    db.flush()
    return user


def get_token(client, login: str, password: str = TEST_PASSWORD) -> str:
    """Effectue un login via l'API et retourne l'access_token."""
    r = client.post("/api/v1/auth/login", data={"username": login, "password": password})
    assert r.status_code == 200, f"get_token failed: {r.json()}"
    return r.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
