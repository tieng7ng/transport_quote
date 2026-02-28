"""
Tests fonctionnels — api/stats.py
Couvre les cas 8.1 à 8.8 du PLAN_FONCTIONNELS.md
"""
import pytest
from app.core import security
from app.models.user import User, UserRole


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


# 8.1 — Overview — ADMIN
def test_stats_overview_admin(client, db):
    admin = _make_user(db, "admin_stat", "admin_stat@test.com")
    r = client.get("/api/v1/stats/overview", headers=_headers(admin))
    assert r.status_code == 200
    data = r.json()
    assert "active_users" in data
    assert "searches" in data
    assert "quotes_created" in data
    assert "conversion_rate_pct" in data


# 8.2 — Overview — COMMERCIAL (interdit)
def test_stats_overview_commercial_forbidden(client, db):
    com = _make_user(db, "com_stat", "com_stat@test.com", UserRole.COMMERCIAL)
    r = client.get("/api/v1/stats/overview", headers=_headers(com))
    assert r.status_code == 403


# 8.3 — Overview avec période
def test_stats_overview_with_period(client, db):
    admin = _make_user(db, "admin_stat2", "admin_stat2@test.com")
    r = client.get(
        "/api/v1/stats/overview?from=2026-01-01&to=2026-12-31",
        headers=_headers(admin),
    )
    assert r.status_code == 200


# 8.4 — Activité journalière
def test_stats_daily_activity(client, db):
    admin = _make_user(db, "admin_dact", "admin_dact@test.com")
    r = client.get("/api/v1/stats/activity", headers=_headers(admin))
    assert r.status_code == 200


# 8.5 — Stats recherches
def test_stats_searches(client, db):
    admin = _make_user(db, "admin_srch", "admin_srch@test.com")
    r = client.get("/api/v1/stats/searches", headers=_headers(admin))
    assert r.status_code == 200


# 8.6 — Stats devis
def test_stats_quotes(client, db):
    admin = _make_user(db, "admin_qstat", "admin_qstat@test.com")
    r = client.get("/api/v1/stats/quotes", headers=_headers(admin))
    assert r.status_code == 200


# 8.7 — Stats imports
def test_stats_imports(client, db):
    admin = _make_user(db, "admin_istat", "admin_istat@test.com")
    r = client.get("/api/v1/stats/imports", headers=_headers(admin))
    assert r.status_code == 200


# 8.8 — Stats sécurité
def test_stats_security(client, db):
    admin = _make_user(db, "admin_secstat", "admin_secstat@test.com")
    r = client.get("/api/v1/stats/security", headers=_headers(admin))
    assert r.status_code == 200
