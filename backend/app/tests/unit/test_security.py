"""
Tests unitaires — core/security.py
Testés en isolation, sans DB.
"""
import pytest
from datetime import timedelta
import jwt

from app.core import security
from app.core.config import get_settings

settings = get_settings()


class TestHashPassword:
    def test_returns_bcrypt_hash(self):
        h = security.hash_password("motdepasse")
        assert h.startswith("$2b$")

    def test_correct_password_verifies(self):
        h = security.hash_password("motdepasse")
        assert security.verify_password("motdepasse", h) is True

    def test_wrong_password_fails(self):
        h = security.hash_password("motdepasse")
        assert security.verify_password("mauvais", h) is False


class TestCreateAccessToken:
    def test_returns_decodable_jwt_with_sub(self):
        import uuid
        user_id = uuid.uuid4()
        token = security.create_access_token(user_id)
        payload = security.decode_token(token)
        assert payload["sub"] == str(user_id)
        assert "exp" in payload

    def test_custom_expiration_respected(self):
        from datetime import datetime, timezone
        delta = timedelta(minutes=5)
        token = security.create_access_token("test_sub", expires_delta=delta)
        payload = security.decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = (exp - now).total_seconds()
        # Should be within 5 minutes ± 5 seconds
        assert 290 < diff < 305


class TestDecodeToken:
    def test_valid_token_returns_payload(self):
        token = security.create_access_token("user_123")
        payload = security.decode_token(token)
        assert payload["sub"] == "user_123"

    def test_expired_token_raises(self):
        token = security.create_access_token("user_123", expires_delta=timedelta(seconds=-1))
        with pytest.raises(jwt.ExpiredSignatureError):
            security.decode_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(jwt.PyJWTError):
            security.decode_token("ceci_nest_pas_un_token")
