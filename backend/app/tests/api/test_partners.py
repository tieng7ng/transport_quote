"""
Tests fonctionnels — api/partners.py
Couvre les cas 3.1 à 3.7 du PLAN_FONCTIONNELS.md
"""
import pytest
from app.core import security
from app.models.user import User, UserRole
from app.models.activity_log import UserActivityLog


def _make_user(db, login, email, role=UserRole.VIEWER, is_active=True):
    u = User(
        login=login, email=email,
        hashed_password=security.hash_password("Password123!"),
        first_name="T", last_name="U",
        role=role, is_active=is_active, must_change_password=False,
    )
    db.add(u)
    db.flush()
    return u


def _headers(user):
    return {"Authorization": f"Bearer {security.create_access_token(user.id)}"}


PARTNER_PAYLOAD = {
    "name": "Test Partner",
    "code": "TEST_PART",
    "contact_email": "partner@test.com",
}


# 3.1 — Liste — authentifié
def test_list_partners_authenticated(client, db):
    user = _make_user(db, "op_list", "op_list@test.com", UserRole.OPERATOR)
    r = client.get("/api/v1/partners", headers=_headers(user))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# 3.2 — Liste — non authentifié
def test_list_partners_unauthenticated(client, db):
    r = client.get("/api/v1/partners")
    assert r.status_code == 401


# 3.3 — Créer — SUPER_ADMIN (seul autorisé)
def test_create_partner_super_admin(client, db):
    sa = _make_user(db, "sa_create_p", "sa_create_p@test.com", UserRole.SUPER_ADMIN)
    r = client.post("/api/v1/partners", json=PARTNER_PAYLOAD, headers=_headers(sa))
    assert r.status_code in (200, 201)
    assert r.json()["code"] == "TEST_PART"


# 3.4 — Créer — OPERATOR (interdit)
def test_create_partner_operator_forbidden(client, db):
    op = _make_user(db, "op_create_p", "op_create_p@test.com", UserRole.OPERATOR)
    r = client.post("/api/v1/partners", json=PARTNER_PAYLOAD, headers=_headers(op))
    assert r.status_code == 403


# 3.5 — Modifier — SUPER_ADMIN
def test_update_partner_super_admin(client, db):
    sa = _make_user(db, "sa_upd_p", "sa_upd_p@test.com", UserRole.SUPER_ADMIN)
    # Create first
    r_create = client.post("/api/v1/partners", json={**PARTNER_PAYLOAD, "code": "UPD_CODE"}, headers=_headers(sa))
    partner_id = r_create.json()["id"]
    r = client.put(f"/api/v1/partners/{partner_id}", json={"name": "Updated Name"}, headers=_headers(sa))
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"


# 3.6 — Partenaire inexistant
def test_get_partner_not_found(client, db):
    user = _make_user(db, "op_notfound", "op_notfound@test.com", UserRole.OPERATOR)
    import uuid
    r = client.get(f"/api/v1/partners/{uuid.uuid4()}", headers=_headers(user))
    assert r.status_code == 404


# 3.7 — Création loguée
def test_create_partner_creates_log(client, db):
    sa = _make_user(db, "sa_log_p", "sa_log_p@test.com", UserRole.SUPER_ADMIN)
    client.post("/api/v1/partners", json={**PARTNER_PAYLOAD, "code": "LOG_CODE"}, headers=_headers(sa))
    row = db.query(UserActivityLog).filter_by(action="partner.created").first()
    assert row is not None
