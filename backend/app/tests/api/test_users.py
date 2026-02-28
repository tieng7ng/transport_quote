"""
Tests fonctionnels — api/users.py
Couvre les cas 2.1 à 2.9 du PLAN_FONCTIONNELS.md
"""
import pytest
from app.core import security
from app.models.user import User, UserRole
from app.models.activity_log import UserActivityLog


def _make_user(db, login, email, role=UserRole.VIEWER, is_active=True):
    u = User(
        login=login, email=email,
        hashed_password=security.hash_password("Password123!"),
        first_name="Test", last_name="User",
        role=role, is_active=is_active, must_change_password=False,
    )
    db.add(u)
    db.flush()
    return u


def _headers(user):
    return {"Authorization": f"Bearer {security.create_access_token(user.id)}"}


# 2.1 — Liste des utilisateurs — ADMIN
def test_list_users_as_admin(client, db):
    admin = _make_user(db, "admin_list", "admin_list@test.com", UserRole.ADMIN)
    r = client.get("/api/v1/users", headers=_headers(admin))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# 2.2 — Liste des utilisateurs — COMMERCIAL (403)
def test_list_users_as_commercial_forbidden(client, db):
    commercial = _make_user(db, "com_list", "com_list@test.com", UserRole.COMMERCIAL)
    r = client.get("/api/v1/users", headers=_headers(commercial))
    assert r.status_code == 403


# 2.3 — Créer un utilisateur — ADMIN
def test_create_user_as_admin(client, db):
    admin = _make_user(db, "admin_create", "admin_create@test.com", UserRole.ADMIN)
    payload = {
        "login": "newuser", "email": "newuser@test.com",
        "password": "Password123!", "first_name": "New", "last_name": "User", "role": "VIEWER",
    }
    r = client.post("/api/v1/users", json=payload, headers=_headers(admin))
    assert r.status_code in (200, 201)
    assert r.json()["login"] == "newuser"


# 2.4 — Créer un utilisateur — COMMERCIAL (403)
def test_create_user_as_commercial_forbidden(client, db):
    commercial = _make_user(db, "com_create", "com_create@test.com", UserRole.COMMERCIAL)
    payload = {
        "login": "blocked_user", "email": "blocked@test.com",
        "password": "Password123!", "first_name": "X", "last_name": "Y", "role": "VIEWER",
    }
    r = client.post("/api/v1/users", json=payload, headers=_headers(commercial))
    assert r.status_code == 403


# 2.5 — Créer avec login existant
def test_create_user_duplicate_login(client, db):
    admin = _make_user(db, "admin_dup", "admin_dup@test.com", UserRole.ADMIN)
    _make_user(db, "duplicatelogin", "dup@test.com")
    payload = {
        "login": "duplicatelogin", "email": "dup2@test.com",
        "password": "Password123!", "first_name": "X", "last_name": "Y", "role": "VIEWER",
    }
    r = client.post("/api/v1/users", json=payload, headers=_headers(admin))
    assert r.status_code == 400


# 2.6 — Modifier un utilisateur — ADMIN
def test_update_user_as_admin(client, db):
    admin = _make_user(db, "admin_upd", "admin_upd@test.com", UserRole.ADMIN)
    target = _make_user(db, "target_upd", "target_upd@test.com", UserRole.VIEWER)
    r = client.put(
        f"/api/v1/users/{target.id}",
        json={"first_name": "Updated"},
        headers=_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["first_name"] == "Updated"


# 2.7 — Désactiver un utilisateur — ADMIN
def test_delete_user_as_admin(client, db):
    admin = _make_user(db, "admin_del", "admin_del@test.com", UserRole.ADMIN)
    target = _make_user(db, "target_del", "target_del@test.com", UserRole.VIEWER)
    r = client.delete(f"/api/v1/users/{target.id}", headers=_headers(admin))
    assert r.status_code == 200


# 2.8 — Se désactiver soi-même (interdit)
def test_delete_own_account_forbidden(client, db):
    admin = _make_user(db, "admin_self", "admin_self@test.com", UserRole.ADMIN)
    r = client.delete(f"/api/v1/users/{admin.id}", headers=_headers(admin))
    assert r.status_code == 403


# 2.9 — Création loguée
def test_create_user_creates_log(client, db):
    admin = _make_user(db, "admin_log", "admin_log@test.com", UserRole.ADMIN)
    payload = {
        "login": "logged_new", "email": "logged_new@test.com",
        "password": "Password123!", "first_name": "L", "last_name": "N", "role": "VIEWER",
    }
    client.post("/api/v1/users", json=payload, headers=_headers(admin))
    row = db.query(UserActivityLog).filter_by(action="user.created").first()
    assert row is not None
