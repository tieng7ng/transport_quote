"""
Tests fonctionnels — api/activity_logs.py
Couvre les cas 7.1 à 7.9 du PLAN_FONCTIONNELS.md
"""
import pytest
from sqlalchemy import text
from app.core import security
from app.models.user import User, UserRole
from app.services.activity_service import log_activity


def _make_user(db, login, email, role=UserRole.ADMIN):
    u = User(
        login=login, email=email,
        hashed_password=security.hash_password("Password123!"),
        first_name="T", last_name="U",
        role=role, is_active=True, must_change_password=False,
    )
    db.add(u)
    db.flush()
    return u


def _headers(user):
    return {"Authorization": f"Bearer {security.create_access_token(user.id)}"}


def _seed_log(db, action="search.performed", user_login="alice"):
    db.execute(text("""
        INSERT INTO user_activity_logs (action, user_login, details, created_at)
        VALUES (:action, :user_login, '{}', NOW())
    """), {"action": action, "user_login": user_login})
    db.flush()


# 7.1 — Liste — ADMIN
def test_list_logs_as_admin(client, db):
    admin = _make_user(db, "admin_logs", "admin_logs@test.com", UserRole.ADMIN)
    _seed_log(db)
    r = client.get("/api/v1/activity-logs", headers=_headers(admin))
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data


# 7.2 — Liste — COMMERCIAL (interdit)
def test_list_logs_as_commercial_forbidden(client, db):
    com = _make_user(db, "com_logs", "com_logs@test.com", UserRole.COMMERCIAL)
    r = client.get("/api/v1/activity-logs", headers=_headers(com))
    assert r.status_code == 403


# 7.3 — Filtre par user_login
def test_filter_logs_by_user_login(client, db):
    admin = _make_user(db, "admin_filt", "admin_filt@test.com", UserRole.ADMIN)
    _seed_log(db, action="search.performed", user_login="alice")
    _seed_log(db, action="search.performed", user_login="bob")
    r = client.get("/api/v1/activity-logs?user_login=alice", headers=_headers(admin))
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(item["user_login"] == "alice" for item in items)


# 7.4 — Filtre par action
def test_filter_logs_by_action(client, db):
    admin = _make_user(db, "admin_act", "admin_act@test.com", UserRole.ADMIN)
    _seed_log(db, action="search.performed")
    _seed_log(db, action="quote.created")
    r = client.get("/api/v1/activity-logs?action=search.performed", headers=_headers(admin))
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(item["action"] == "search.performed" for item in items)


# 7.5 — Filtre par date
def test_filter_logs_by_date(client, db):
    admin = _make_user(db, "admin_date", "admin_date@test.com", UserRole.ADMIN)
    _seed_log(db)
    r = client.get(
        "/api/v1/activity-logs?from=2026-01-01&to=2030-12-31",
        headers=_headers(admin),
    )
    assert r.status_code == 200


# 7.6 — Pagination
def test_pagination(client, db):
    admin = _make_user(db, "admin_pag", "admin_pag@test.com", UserRole.ADMIN)
    for i in range(15):
        _seed_log(db, action=f"action_{i}", user_login="paguser")
    r = client.get("/api/v1/activity-logs?page=2&page_size=5", headers=_headers(admin))
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 2
    assert len(data["items"]) <= 5


# 7.7 — Export CSV
def test_export_csv(client, db):
    admin = _make_user(db, "admin_csv", "admin_csv@test.com", UserRole.ADMIN)
    _seed_log(db)
    r = client.get("/api/v1/activity-logs/export?format=csv", headers=_headers(admin))
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")


# 7.9 — Export avec filtres
def test_export_csv_with_filter(client, db):
    admin = _make_user(db, "admin_csv2", "admin_csv2@test.com", UserRole.ADMIN)
    _seed_log(db, action="quote.created")
    r = client.get(
        "/api/v1/activity-logs/export?format=csv&action=quote.created",
        headers=_headers(admin),
    )
    assert r.status_code == 200
