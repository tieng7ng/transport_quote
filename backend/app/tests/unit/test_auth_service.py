"""
Tests unitaires — services/auth_service.py
Couvre les cas 2.1 à 2.8 du PLAN_UNITAIRES.md

AuthService utilise la DB (pas de mock), on s'appuie
sur la fixture `db` rollback de conftest.py.
"""
import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate, LoginRequest
from app.models.user import User, UserRole
from app.core import security


def _make_user(db, login="existing_user", email="existing@test.com", is_active=True):
    u = User(
        login=login, email=email,
        hashed_password=security.hash_password("Password123!"),
        first_name="T", last_name="U",
        role=UserRole.VIEWER,
        is_active=is_active, must_change_password=False,
    )
    db.add(u)
    db.flush()
    return u


class TestAuthenticateUser:
    def test_correct_credentials_returns_user(self, db):
        _make_user(db, login="alice", email="alice@test.com")
        req = LoginRequest(login="alice", password="Password123!")
        result = AuthService.authenticate_user(db, req)
        assert result is not None
        assert result.login == "alice"

    def test_wrong_password_returns_none(self, db):
        _make_user(db, login="bob", email="bob@test.com")
        req = LoginRequest(login="bob", password="WrongPassword!")
        result = AuthService.authenticate_user(db, req)
        assert result is None

    def test_unknown_login_returns_none(self, db):
        req = LoginRequest(login="nobody", password="Password123!")
        result = AuthService.authenticate_user(db, req)
        assert result is None


class TestCreateUser:
    def _payload(self, login="newuser", email="newuser@test.com"):
        return UserCreate(
            login=login, email=email,
            password="Password123!",
            first_name="New", last_name="User",
            role=UserRole.VIEWER,
        )

    def test_valid_data_creates_user(self, db):
        user = AuthService.create_user(db, self._payload())
        assert user.login == "newuser"
        assert user.must_change_password is True
        assert user.is_active is False  # Inactif par défaut

    def test_duplicate_email_raises_400(self, db):
        _make_user(db, login="other", email="taken@test.com")
        with pytest.raises(HTTPException) as exc_info:
            AuthService.create_user(db, self._payload(login="unique_login", email="taken@test.com"))
        assert exc_info.value.status_code == 400

    def test_duplicate_login_raises_400(self, db):
        _make_user(db, login="taken_login", email="other@test.com")
        with pytest.raises(HTTPException) as exc_info:
            AuthService.create_user(db, self._payload(login="taken_login", email="unique@test.com"))
        assert exc_info.value.status_code == 400


class TestUpdateLastLogin:
    def test_updates_last_login_at(self, db):
        user = _make_user(db, login="logintrack", email="logintrack@test.com")
        assert user.last_login_at is None
        AuthService.update_last_login(db, user.id)
        db.refresh(user)
        assert user.last_login_at is not None
        assert user.last_login_at.tzinfo is not None  # timezone-aware
