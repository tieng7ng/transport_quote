"""
Tests fonctionnels — api/alerts.py
Couvre les cas 9.1 à 9.7 du PLAN_FONCTIONNELS.md
"""
import pytest
from sqlalchemy import text
from app.core import security
from app.models.user import User, UserRole
from app.models.security_alert import SecurityAlert


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


def _seed_alert(db, alert_type="login_failures", severity="medium"):
    alert = SecurityAlert(
        type=alert_type,
        severity=severity,
        details={"login": "hacker", "ip_address": "1.2.3.4", "failures": 6},
    )
    db.add(alert)
    db.flush()
    return alert


# 9.1 — Liste — ADMIN
def test_list_alerts_as_admin(client, db):
    admin = _make_user(db, "admin_alrt", "admin_alrt@test.com")
    _seed_alert(db)
    r = client.get("/api/v1/alerts", headers=_headers(admin))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# 9.2 — Liste — COMMERCIAL (interdit)
def test_list_alerts_as_commercial_forbidden(client, db):
    com = _make_user(db, "com_alrt", "com_alrt@test.com", UserRole.COMMERCIAL)
    r = client.get("/api/v1/alerts", headers=_headers(com))
    assert r.status_code == 403


# 9.3 — Marquer comme lu
def test_mark_alert_seen(client, db):
    admin = _make_user(db, "admin_seen", "admin_seen@test.com")
    alert = _seed_alert(db)
    r = client.patch(f"/api/v1/alerts/{alert.id}/seen", headers=_headers(admin))
    assert r.status_code == 200
    data = r.json()
    assert data["seen"] is True or data.get("seen_at") is not None


# 9.4 — Résoudre — account_disabled
def test_resolve_alert_account_disabled(client, db):
    admin = _make_user(db, "admin_res1", "admin_res1@test.com")
    alert = _seed_alert(db)
    r = client.patch(
        f"/api/v1/alerts/{alert.id}/resolve",
        json={"resolution": "account_disabled"},
        headers=_headers(admin),
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("resolved_at") is not None or data.get("resolution") == "account_disabled"


# 9.5 — Résoudre — ignored
def test_resolve_alert_ignored(client, db):
    admin = _make_user(db, "admin_res2", "admin_res2@test.com")
    alert = _seed_alert(db)
    r = client.patch(
        f"/api/v1/alerts/{alert.id}/resolve",
        json={"resolution": "ignored"},
        headers=_headers(admin),
    )
    assert r.status_code == 200


# 9.6 — Alerte inexistante
def test_mark_nonexistent_alert_seen(client, db):
    admin = _make_user(db, "admin_404", "admin_404@test.com")
    import uuid
    r = client.patch(f"/api/v1/alerts/{uuid.uuid4()}/seen", headers=_headers(admin))
    assert r.status_code == 404


# 9.7 — SSE stream — connexion
def test_sse_stream_connects(client, db):
    admin = _make_user(db, "admin_sse", "admin_sse@test.com")
    # SSE returns 200 with text/event-stream content type
    with client.stream("GET", "/api/v1/alerts/stream", headers=_headers(admin)) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
