"""
Tests fonctionnels — api/auth.py
Couvre les cas 1.1 à 1.13 du PLAN_FONCTIONNELS.md
"""
import pytest
from fastapi.testclient import TestClient
from app.core import security
from app.models.user import User, UserRole
from app.models.activity_log import UserActivityLog


def _make_user(db, login, email, role=UserRole.VIEWER, is_active=True, must_change_password=False):
    u = User(
        login=login, email=email,
        hashed_password=security.hash_password("Password123!"),
        first_name="Test", last_name="User",
        role=role, is_active=is_active,
        must_change_password=must_change_password,
    )
    db.add(u)
    db.flush()
    return u


# 1.1 — Login valide
def test_login_success(client, db):
    _make_user(db, "loginok", "loginok@test.com")
    r = client.post("/api/v1/auth/login", data={"username": "loginok", "password": "Password123!"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


# 1.2 — Mauvais mot de passe
def test_login_wrong_password(client, db):
    _make_user(db, "wrongpwd", "wrongpwd@test.com")
    r = client.post("/api/v1/auth/login", data={"username": "wrongpwd", "password": "BadPass!"})
    assert r.status_code == 400


# 1.3 — Login inexistant
def test_login_unknown_user(client, db):
    r = client.post("/api/v1/auth/login", data={"username": "nobody", "password": "Password123!"})
    assert r.status_code == 400


# 1.4 — Compte inactif
def test_login_inactive_account(client, db):
    _make_user(db, "inactive", "inactive@test.com", is_active=False)
    r = client.post("/api/v1/auth/login", data={"username": "inactive", "password": "Password123!"})
    assert r.status_code == 400


# 1.5 — Logout avec token valide
def test_logout(client, db):
    user = _make_user(db, "logoutuser", "logout@test.com")
    token = security.create_access_token(user.id)
    r = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


# 1.6 — Le token est blacklisté après logout
def test_token_blacklisted_after_logout(client, db):
    user = _make_user(db, "blacklist_user", "blacklist@test.com")
    token = security.create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/v1/auth/logout", headers=headers)
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 401


# 1.7 — Refresh token valide
def test_refresh_token_valid(client, db):
    _make_user(db, "refreshme", "refresh@test.com")
    r = client.post("/api/v1/auth/login", data={"username": "refreshme", "password": "Password123!"})
    rt = r.json()["refresh_token"]
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


# 1.8 — Refresh token invalide
def test_refresh_token_invalid(client, db):
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage.token.here"})
    assert r.status_code == 401


# 1.9 — Changement de mot de passe valide
def test_change_password_valid(client, db):
    user = _make_user(db, "chgpwd", "chgpwd@test.com")
    token = security.create_access_token(user.id)
    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Password123!", "new_password": "NewPass456!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


# 1.10 — Ancien MDP incorrect
def test_change_password_wrong_old(client, db):
    user = _make_user(db, "chgpwdfail", "chgpwdfail@test.com")
    token = security.create_access_token(user.id)
    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongOld!", "new_password": "NewPass456!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


# 1.11 — Route protégée sans token
def test_protected_route_no_token(client, db):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


# 1.12 — Login réussi logue auth.login_success
def test_login_success_creates_log(client, db):
    _make_user(db, "loggeduser", "loggeduser@test.com")
    client.post("/api/v1/auth/login", data={"username": "loggeduser", "password": "Password123!"})
    row = db.query(UserActivityLog).filter_by(action="auth.login_success").first()
    assert row is not None
    assert row.user_login == "loggeduser"


# 1.13 — Login échoué logue auth.login_failed
def test_login_failed_creates_log(client, db):
    _make_user(db, "faileduser", "faileduser@test.com")
    client.post("/api/v1/auth/login", data={"username": "faileduser", "password": "WrongPass!"})
    row = db.query(UserActivityLog).filter_by(action="auth.login_failed").first()
    assert row is not None
