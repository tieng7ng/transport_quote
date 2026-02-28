"""
Tests fonctionnels — api/customer_quotes.py
Couvre les cas 5.1 à 5.13 du PLAN_FONCTIONNELS.md
"""
import pytest
from app.core import security
from app.models.user import User, UserRole
from app.models.activity_log import UserActivityLog


def _make_user(db, login, email, role=UserRole.COMMERCIAL):
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


QUOTE_PAYLOAD = {
    "customer_name": "ACME Corp",
    "customer_email": "acme@test.com",
}


def _create_quote(client, db, role=UserRole.COMMERCIAL, login_suffix=""):
    user = _make_user(db, f"qu_{login_suffix}", f"qu_{login_suffix}@test.com", role)
    r = client.post("/api/v1/customer-quotes", json=QUOTE_PAYLOAD, headers=_headers(user))
    return user, r


# 5.1 — Créer un devis — COMMERCIAL
def test_create_quote_commercial(client, db):
    _, r = _create_quote(client, db, UserRole.COMMERCIAL, "c1")
    assert r.status_code in (200, 201)
    assert "id" in r.json()


# 5.2 — Créer un devis — VIEWER (interdit)
def test_create_quote_viewer_forbidden(client, db):
    _, r = _create_quote(client, db, UserRole.VIEWER, "v1")
    assert r.status_code == 403


# 5.3 — Lister les devis
def test_list_quotes(client, db):
    user = _make_user(db, "qu_list", "qu_list@test.com")
    r = client.get("/api/v1/customer-quotes", headers=_headers(user))
    assert r.status_code == 200


# 5.4 — Détail d'un devis
def test_get_quote_detail(client, db):
    user, r_create = _create_quote(client, db, UserRole.COMMERCIAL, "det1")
    quote_id = r_create.json()["id"]
    r = client.get(f"/api/v1/customer-quotes/{quote_id}", headers=_headers(user))
    assert r.status_code == 200
    assert r.json()["id"] == quote_id


# 5.6 — Modifier un devis en DRAFT
def test_update_quote_in_draft(client, db):
    user, r_create = _create_quote(client, db, UserRole.COMMERCIAL, "upd1")
    quote_id = r_create.json()["id"]
    r = client.put(
        f"/api/v1/customer-quotes/{quote_id}",
        json={"customer_name": "Updated ACME"},
        headers=_headers(user),
    )
    assert r.status_code == 200


# 5.8 — Changer statut DRAFT → READY
def test_change_status_draft_to_ready(client, db):
    user, r_create = _create_quote(client, db, UserRole.COMMERCIAL, "st1")
    quote_id = r_create.json()["id"]
    r = client.patch(
        f"/api/v1/customer-quotes/{quote_id}/status",
        json={"status": "READY"},
        headers=_headers(user),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "READY"


# 5.10 — Supprimer un devis en DRAFT
def test_delete_quote_in_draft(client, db):
    user, r_create = _create_quote(client, db, UserRole.COMMERCIAL, "del1")
    quote_id = r_create.json()["id"]
    r = client.delete(f"/api/v1/customer-quotes/{quote_id}", headers=_headers(user))
    assert r.status_code in (200, 204)


# 5.12 — Création loguée
def test_create_quote_creates_log(client, db):
    _, r = _create_quote(client, db, UserRole.COMMERCIAL, "log1")
    assert r.status_code in (200, 201)
    row = db.query(UserActivityLog).filter_by(action="quote.created").first()
    assert row is not None


# 5.13 — Changement de statut logué avec previous/new status
def test_status_change_creates_log(client, db):
    user, r_create = _create_quote(client, db, UserRole.COMMERCIAL, "stlog1")
    quote_id = r_create.json()["id"]
    client.patch(
        f"/api/v1/customer-quotes/{quote_id}/status",
        json={"status": "READY"},
        headers=_headers(user),
    )
    row = db.query(UserActivityLog).filter_by(action="quote.status_changed").first()
    assert row is not None
    assert "previous_status" in row.details
    assert "new_status" in row.details
    assert row.details["new_status"] == "READY"


# 5.5 — Devis d'un autre utilisateur — COMMERCIAL → 403 ou absent de la liste
def test_get_other_user_quote_forbidden_or_filtered(client, db):
    owner, r_create = _create_quote(client, db, UserRole.COMMERCIAL, "own1")
    quote_id = r_create.json()["id"]
    # Autre utilisateur de même rôle
    other = _make_user(db, "other_com", "other_com@test.com", UserRole.COMMERCIAL)
    r = client.get(f"/api/v1/customer-quotes/{quote_id}", headers=_headers(other))
    # Le service doit soit retourner 403, soit filtrer (404)
    assert r.status_code in (403, 404)


# 5.7 — Modifier un devis en SENT → 400 (machine à états)
@pytest.mark.xfail(
    strict=False,
    reason="Machine à états non implémentée dans customer_quote_service.py — à activer après implémentation"
)
def test_update_quote_in_sent_forbidden(client, db):
    user, r_create = _create_quote(client, db, UserRole.COMMERCIAL, "sent1")
    quote_id = r_create.json()["id"]
    # Passer en SENT
    client.patch(f"/api/v1/customer-quotes/{quote_id}/status", json={"status": "READY"}, headers=_headers(user))
    client.patch(f"/api/v1/customer-quotes/{quote_id}/status", json={"status": "SENT"}, headers=_headers(user))
    # Tenter de modifier
    r = client.put(
        f"/api/v1/customer-quotes/{quote_id}",
        json={"customer_name": "Tentative modification"},
        headers=_headers(user),
    )
    assert r.status_code == 400


# 5.9 — Retour arrière de statut READY → DRAFT → 400 (machine à états)
@pytest.mark.xfail(
    strict=False,
    reason="Machine à états non implémentée — transitions inverses à définir"
)
def test_status_rollback_ready_to_draft_forbidden(client, db):
    user, r_create = _create_quote(client, db, UserRole.COMMERCIAL, "rb1")
    quote_id = r_create.json()["id"]
    client.patch(f"/api/v1/customer-quotes/{quote_id}/status", json={"status": "READY"}, headers=_headers(user))
    r = client.patch(
        f"/api/v1/customer-quotes/{quote_id}/status",
        json={"status": "DRAFT"},
        headers=_headers(user),
    )
    assert r.status_code == 400


# 5.11 — Supprimer un devis en SENT → 400 (machine à états)
@pytest.mark.xfail(
    strict=False,
    reason="Suppression d'un devis SENT non bloquée actuellement"
)
def test_delete_quote_in_sent_forbidden(client, db):
    user, r_create = _create_quote(client, db, UserRole.COMMERCIAL, "delsent1")
    quote_id = r_create.json()["id"]
    client.patch(f"/api/v1/customer-quotes/{quote_id}/status", json={"status": "READY"}, headers=_headers(user))
    client.patch(f"/api/v1/customer-quotes/{quote_id}/status", json={"status": "SENT"}, headers=_headers(user))
    r = client.delete(f"/api/v1/customer-quotes/{quote_id}", headers=_headers(user))
    assert r.status_code == 400

