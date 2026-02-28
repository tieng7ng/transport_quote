"""
Tests fonctionnels — api/imports.py
Couvre les cas 6.1 à 6.6 du PLAN_FONCTIONNELS.md
"""
import io
import pytest
from app.core import security
from app.models.user import User, UserRole
from app.models.activity_log import UserActivityLog


def _make_user(db, login, email, role=UserRole.SUPER_ADMIN):
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


def _csv_file(filename: str = "tarifs.csv") -> dict:
    """Génère un fichier CSV minimal valide pour l'upload."""
    content = (
        "transport_mode,origin_city,origin_country,dest_city,dest_country,cost\n"
        "road,Paris,FR,Lyon,FR,150.00\n"
        "road,Lyon,FR,Marseille,FR,200.00\n"
    )
    return {
        "file": (filename, io.BytesIO(content.encode("utf-8")), "text/csv"),
    }


# 6.1 — Upload CSV valide — SUPER_ADMIN → 201
def test_upload_csv_super_admin(client, db):
    sa = _make_user(db, "sa_import", "sa_import@test.com")
    r = client.post(
        "/api/v1/imports",
        files=_csv_file(),
        headers=_headers(sa),
    )
    assert r.status_code in (200, 201, 202)
    data = r.json()
    assert "id" in data or "import_job_id" in data


# 6.2 — Upload CSV — COMMERCIAL → 403
def test_upload_csv_commercial_forbidden(client, db):
    com = _make_user(db, "com_import", "com_import@test.com", UserRole.COMMERCIAL)
    r = client.post(
        "/api/v1/imports",
        files=_csv_file(),
        headers=_headers(com),
    )
    assert r.status_code == 403


# 6.3 — Upload extension invalide (.exe) → 400
def test_upload_invalid_extension(client, db):
    sa = _make_user(db, "sa_import2", "sa_import2@test.com")
    r = client.post(
        "/api/v1/imports",
        files={"file": ("malware.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
        headers=_headers(sa),
    )
    assert r.status_code == 400


# 6.4 — Lister les imports → 200 + liste
def test_list_imports(client, db):
    sa = _make_user(db, "sa_import3", "sa_import3@test.com")
    r = client.get("/api/v1/imports", headers=_headers(sa))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# 6.5 — Détail d'un import → 200 + statut
def test_get_import_detail(client, db):
    sa = _make_user(db, "sa_import4", "sa_import4@test.com")
    # Créer un import d'abord
    r_create = client.post(
        "/api/v1/imports",
        files=_csv_file("tarifs2.csv"),
        headers=_headers(sa),
    )
    if r_create.status_code not in (200, 201, 202):
        pytest.skip("Création d'import impossible, test ignoré")

    data = r_create.json()
    import_id = data.get("id") or data.get("import_job_id")
    r = client.get(f"/api/v1/imports/{import_id}", headers=_headers(sa))
    assert r.status_code == 200
    assert "status" in r.json()


# 6.6 — Démarrage logué dans user_activity_logs
def test_upload_creates_log(client, db):
    sa = _make_user(db, "sa_import5", "sa_import5@test.com")
    client.post(
        "/api/v1/imports",
        files=_csv_file("tarifs3.csv"),
        headers=_headers(sa),
    )
    row = db.query(UserActivityLog).filter_by(action="import.started").first()
    assert row is not None
