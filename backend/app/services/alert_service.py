"""
Service de détection des alertes de sécurité.
Les fonctions sont appelées par le job asyncio alert_check_loop() dans main.py.
"""
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.security_alert import SecurityAlert
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


# =============================================================================
# Fonctions de détection (appelées par le job de fond)
# =============================================================================

def _process_login_failure_alerts(db: Session) -> None:
    """
    Crée une alerte pour chaque compte avec >= 5 échecs de connexion
    en 10 minutes, en évitant les doublons sur une fenêtre de 30 minutes.
    """
    rows = db.execute(text("""
        SELECT details->>'attempted_login' AS login,
               ip_address,
               COUNT(*) AS failures
        FROM user_activity_logs
        WHERE action = 'auth.login_failed'
          AND created_at > NOW() - INTERVAL '10 minutes'
        GROUP BY details->>'attempted_login', ip_address
        HAVING COUNT(*) >= 5
    """)).fetchall()

    for row in rows:
        already_exists = db.execute(text("""
            SELECT id FROM security_alerts
            WHERE type = 'login_failures'
              AND details->>'login' = :login
              AND resolved_at IS NULL
              AND created_at > NOW() - INTERVAL '30 minutes'
        """), {"login": row.login}).fetchone()

        if not already_exists:
            db.add(SecurityAlert(
                type="login_failures",
                severity="critical" if row.failures >= 10 else "medium",
                details={
                    "login": row.login,
                    "ip_address": row.ip_address,
                    "failures": row.failures,
                },
            ))


def _process_suspicious_activity_alerts(db: Session) -> None:
    """
    Crée une alerte si un utilisateur dépasse 50 actions en 5 minutes.
    Dédoublonnage sur 30 minutes.
    """
    rows = db.execute(text("""
        SELECT user_id, user_login, COUNT(*) AS action_count
        FROM user_activity_logs
        WHERE created_at > NOW() - INTERVAL '5 minutes'
          AND user_id IS NOT NULL
        GROUP BY user_id, user_login
        HAVING COUNT(*) >= 50
    """)).fetchall()

    for row in rows:
        already_exists = db.execute(text("""
            SELECT id FROM security_alerts
            WHERE type = 'suspicious_activity'
              AND details->>'user_login' = :login
              AND resolved_at IS NULL
              AND created_at > NOW() - INTERVAL '30 minutes'
        """), {"login": row.user_login}).fetchone()

        if not already_exists:
            db.add(SecurityAlert(
                type="suspicious_activity",
                severity="medium",
                details={
                    "user_login": row.user_login,
                    "action_count": row.action_count,
                },
            ))


# =============================================================================
# Boucles asyncio (démarrées via lifespan dans main.py)
# =============================================================================

async def alert_check_loop() -> None:
    """Vérifie les alertes toutes les 2 minutes."""
    while True:
        await asyncio.sleep(120)
        db = SessionLocal()
        try:
            _process_login_failure_alerts(db)
            _process_suspicious_activity_alerts(db)
            db.commit()
        except Exception as exc:
            logger.error(f"alert_check_loop error: {exc}", exc_info=True)
            db.rollback()
        finally:
            db.close()


async def daily_purge_loop() -> None:
    """Purge les logs de plus d'un an, chaque nuit à minuit UTC."""
    while True:
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        next_midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        await asyncio.sleep((next_midnight - now).total_seconds())
        db = SessionLocal()
        try:
            result = db.execute(text(
                "DELETE FROM user_activity_logs WHERE created_at < NOW() - INTERVAL '1 year'"
            ))
            db.commit()
            logger.info(f"daily_purge_loop: {result.rowcount} logs supprimés")
        except Exception as exc:
            logger.error(f"daily_purge_loop error: {exc}", exc_info=True)
            db.rollback()
        finally:
            db.close()
