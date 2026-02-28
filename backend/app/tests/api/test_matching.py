"""
Tests fonctionnels — api/matching.py
Couvre les cas 4.1 à 4.6 du PLAN_FONCTIONNELS.md
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


SEARCH_PAYLOAD = {
    "origin": "Paris",
    "destination": "Lyon",
    "transport_mode": "road",
    "weight": 100.0,
}


# 4.1 — Recherche valide avec résultats possibles
def test_search_authenticated_returns_200(client, db):
    user = _make_user(db, "searcher", "searcher@test.com")
    r = client.post("/api/v1/matching/search", json=SEARCH_PAYLOAD, headers=_headers(user))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# 4.2 — Recherche sans résultat probable (critères très spécifiques)
def test_search_no_results(client, db):
    user = _make_user(db, "searcher2", "searcher2@test.com")
    payload = {**SEARCH_PAYLOAD, "origin": "ZZZ_VILLE_INEXISTANTE", "destination": "ZZZ_DEST"}
    r = client.post("/api/v1/matching/search", json=payload, headers=_headers(user))
    assert r.status_code == 200
    assert r.json() == []


# 4.3 — Recherche non authentifiée
def test_search_unauthenticated(client, db):
    r = client.post("/api/v1/matching/search", json=SEARCH_PAYLOAD)
    assert r.status_code == 401


# 4.4 — Critères invalides (poids négatif → erreur de validation Pydantic)
def test_search_invalid_weight(client, db):
    user = _make_user(db, "searcher3", "searcher3@test.com")
    payload = {**SEARCH_PAYLOAD, "weight": -10}
    r = client.post("/api/v1/matching/search", json=payload, headers=_headers(user))
    assert r.status_code == 422


# 4.5 — Recherche crée un log search.performed
def test_search_creates_log(client, db):
    user = _make_user(db, "log_searcher", "log_searcher@test.com")
    client.post("/api/v1/matching/search", json=SEARCH_PAYLOAD, headers=_headers(user))
    row = db.query(UserActivityLog).filter_by(action="search.performed").first()
    assert row is not None
    assert row.user_login == "log_searcher"


# 4.6 — Le log contient results_count correct
def test_search_log_contains_results_count(client, db):
    user = _make_user(db, "count_searcher", "count_searcher@test.com")
    r = client.post("/api/v1/matching/search", json=SEARCH_PAYLOAD, headers=_headers(user))
    results = r.json()

    row = db.query(UserActivityLog).filter_by(action="search.performed").order_by(
        UserActivityLog.created_at.desc()
    ).first()
    assert row is not None
    assert row.details["results_count"] == len(results)
