"""
Tests unitaires — services/activity_service.py
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from app.services.activity_service import log_activity, purge_old_logs
from app.models.activity_log import UserActivityLog
from app.models.user import User, UserRole


def _make_user(login="testuser") -> User:
    user = User()
    user.id = "00000000-0000-0000-0000-000000000001"
    user.login = login
    user.role = UserRole.COMMERCIAL
    return user


class TestLogActivity:
    def test_inserts_one_row_with_correct_fields(self, db):
        user = _make_user()
        log_activity(db, "search.performed", user=user, resource="search",
                     details={"origin": "Paris", "results_count": 3})
        db.flush()

        row = db.query(UserActivityLog).filter_by(action="search.performed").first()
        assert row is not None
        assert row.user_login == "testuser"
        assert row.user_role == UserRole.COMMERCIAL.value
        assert row.action == "search.performed"
        assert row.resource == "search"
        assert row.details["results_count"] == 3

    def test_anonymous_login_failure(self, db):
        log_activity(db, "auth.login_failed",
                     details={"attempted_login": "hacker", "reason": "invalid_credentials"})
        db.flush()

        row = db.query(UserActivityLog).filter_by(action="auth.login_failed").first()
        assert row is not None
        assert row.user_id is None
        assert row.user_login is None

    def test_ip_address_from_x_forwarded_for(self, db):
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        request.client = None

        log_activity(db, "search.performed", request=request)
        db.flush()

        row = db.query(UserActivityLog).filter_by(action="search.performed").first()
        assert row.ip_address == "10.0.0.1"

    def test_ip_address_none_without_request(self, db):
        log_activity(db, "search.performed")
        db.flush()

        row = db.query(UserActivityLog).filter_by(action="search.performed").first()
        assert row.ip_address is None

    def test_does_not_commit(self, db):
        """log_activity ne doit jamais appeler db.commit()."""
        original_commit = db.commit
        committed = []
        db.commit = lambda: committed.append(True)

        log_activity(db, "test.action")

        assert len(committed) == 0
        db.commit = original_commit

    def test_purge_removes_old_logs(self, db):
        from sqlalchemy import text
        # Insert a log older than 1 year directly
        db.execute(text("""
            INSERT INTO user_activity_logs (action, details, created_at)
            VALUES ('old.action', '{}', NOW() - INTERVAL '2 years')
        """))
        # Insert a recent log
        log_activity(db, "recent.action")
        db.flush()

        count_before = db.query(UserActivityLog).count()
        assert count_before >= 2

        purge_old_logs(db)

        remaining = db.query(UserActivityLog).all()
        assert all(r.action != "old.action" for r in remaining)

    def test_purge_empty_table_no_error(self, db):
        # Should not raise
        deleted = purge_old_logs(db)
        assert isinstance(deleted, int)
