"""
Tests unitaires — services/alert_service.py

Les fonctions testées sont privées (préfixe _). On les importe directement.
Chaque test insère des logs via SQL raw dans user_activity_logs, puis vérifie
les alertes créées dans security_alerts.
"""
import pytest
from sqlalchemy import text

from app.services.alert_service import (
    _process_login_failure_alerts,
    _process_suspicious_activity_alerts,
)
from app.models.security_alert import SecurityAlert
from app.models.user import User, UserRole
from app.core import security as sec


def _insert_login_failures(db, login: str, ip: str, count: int, minutes_ago: int = 5):
    """Insère `count` échecs de connexion dans user_activity_logs."""
    for _ in range(count):
        db.execute(text("""
            INSERT INTO user_activity_logs (action, details, ip_address, created_at)
            VALUES (
                'auth.login_failed',
                jsonb_build_object('attempted_login', :login, 'reason', 'invalid_credentials'),
                :ip,
                NOW() - INTERVAL '1 minute' * :minutes_ago
            )
        """), {"login": login, "ip": ip, "minutes_ago": minutes_ago})
    db.flush()


def _insert_user_actions(db, user_login: str, user_id: str, count: int, minutes_ago: int = 2):
    """Insère `count` actions d'un utilisateur authentifié."""
    db.execute(text("""
        INSERT INTO user_activity_logs (action, user_id, user_login, details, created_at)
        SELECT 'search.performed',
               :user_id::uuid,
               :user_login,
               '{}',
               NOW() - INTERVAL '1 minute' * :minutes_ago
        FROM generate_series(1, :count)
    """), {"user_login": user_login, "user_id": user_id, "minutes_ago": minutes_ago, "count": count})
    db.flush()


class TestLoginFailureAlerts:
    def test_6_failures_creates_medium_alert(self, db):
        _insert_login_failures(db, "alice", "10.0.0.1", 6)
        _process_login_failure_alerts(db)
        db.flush()

        alerts = db.query(SecurityAlert).filter_by(type="login_failures").all()
        assert len(alerts) == 1
        assert alerts[0].severity == "medium"

    def test_11_failures_creates_critical_alert(self, db):
        _insert_login_failures(db, "bob", "10.0.0.2", 11)
        _process_login_failure_alerts(db)
        db.flush()

        alert = db.query(SecurityAlert).filter_by(type="login_failures").first()
        assert alert is not None
        assert alert.severity == "critical"

    def test_no_duplicate_within_30_minutes(self, db):
        # Create an existing alert
        db.add(SecurityAlert(
            type="login_failures",
            severity="medium",
            details={"login": "carol", "ip_address": "10.0.0.3", "failures": 6},
        ))
        db.flush()

        _insert_login_failures(db, "carol", "10.0.0.3", 6)
        _process_login_failure_alerts(db)
        db.flush()

        alerts = db.query(SecurityAlert).filter_by(type="login_failures").all()
        assert len(alerts) == 1  # still only 1

    def test_below_threshold_no_alert(self, db):
        _insert_login_failures(db, "dave", "10.0.0.4", 3)
        _process_login_failure_alerts(db)
        db.flush()

        alert = db.query(SecurityAlert).filter_by(type="login_failures").first()
        assert alert is None


class TestSuspiciousActivityAlerts:
    def test_55_actions_creates_alert(self, db):
        import uuid
        uid = str(uuid.uuid4())
        _insert_user_actions(db, "eve", uid, 55)
        _process_suspicious_activity_alerts(db)
        db.flush()

        alert = db.query(SecurityAlert).filter_by(type="suspicious_activity").first()
        assert alert is not None
        assert alert.details["user_login"] == "eve"

    def test_no_duplicate_within_30_minutes(self, db):
        import uuid
        uid = str(uuid.uuid4())
        # Existing alert
        db.add(SecurityAlert(
            type="suspicious_activity",
            severity="medium",
            details={"user_login": "frank", "action_count": 55},
        ))
        db.flush()

        _insert_user_actions(db, "frank", uid, 55)
        _process_suspicious_activity_alerts(db)
        db.flush()

        alerts = db.query(SecurityAlert).filter_by(type="suspicious_activity").all()
        assert len(alerts) == 1

    def test_below_threshold_no_alert(self, db):
        import uuid
        uid = str(uuid.uuid4())
        _insert_user_actions(db, "grace", uid, 30)
        _process_suspicious_activity_alerts(db)
        db.flush()

        alert = db.query(SecurityAlert).filter_by(type="suspicious_activity").first()
        assert alert is None
