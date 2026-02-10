from fastapi.testclient import TestClient
from app.core import security

def test_login_access_token(client: TestClient, db):
    # 1. Create a user manually in DB
    from app.models.user import User
    user = User(
        email="test@example.com",
        hashed_password=security.hash_password("Password123!"),
        is_active=True,
        role="VIEWER",
        first_name="Test",
        last_name="User"
    )
    db.add(user)
    db.commit()

    # 2. Try to login
    login_data = {
        "username": "test@example.com",
        "password": "Password123!"
    }
    r = client.post("/api/v1/auth/login", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_use_access_token(client: TestClient, db):
    # 1. Create a user
    from app.models.user import User
    user = User(
        email="test2@example.com",
        hashed_password=security.hash_password("Password123!"),
        is_active=True,
        role="ADMIN",
        first_name="Admin",
        last_name="User"
    )
    db.add(user)
    db.commit()

    # 2. Login to get token
    login_data = {
        "username": "test2@example.com",
        "password": "Password123!"
    }
    r = client.post("/api/v1/auth/login", data=login_data)
    access_token = r.json()["access_token"]

    # 3. Use token to get protected route
    headers = {"Authorization": f"Bearer {access_token}"}
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "test2@example.com"

def test_refresh_token(client: TestClient, db):
    # 1. Create a user
    from app.models.user import User
    user = User(
        email="test_refresh@example.com",
        hashed_password=security.hash_password("Password123!"),
        is_active=True,
        role="VIEWER",
        first_name="Refresh",
        last_name="User"
    )
    db.add(user)
    db.commit()

    # 2. Login
    login_data = {
        "username": "test_refresh@example.com",
        "password": "Password123!"
    }
    r = client.post("/api/v1/auth/login", data=login_data)
    tokens = r.json()
    refresh_token = tokens["refresh_token"]

    # 3. Refresh (using body)
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.json()["token_type"] == "bearer"
