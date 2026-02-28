"""
Service de logging des activités utilisateurs.
Appeler log_activity() dans les routes FastAPI, dans la même transaction.
Le commit se fait dans la route, pas ici.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Request

from app.models.activity_log import UserActivityLog
from app.models.user import User


def log_activity(
    db: Session,
    action: str,
    user: Optional[User] = None,
    resource: Optional[str] = None,
    resource_id=None,
    details: Optional[dict] = None,
    request: Optional[Request] = None,
) -> None:
    """
    Enregistre une action utilisateur dans user_activity_logs.

    Ne fait PAS de commit — celui-ci est géré par la route appelante
    afin que le log et l'action métier soient dans la même transaction.

    Exemples d'usage :
        log_activity(db, "auth.login_success", user=user, resource="user",
                     resource_id=user.id, request=request)

        log_activity(db, "search.performed", user=current_user,
                     details={"origin": "Paris", "results_count": 5},
                     request=request)
    """
    db.add(UserActivityLog(
        user_id     = user.id if user else None,
        user_login  = user.login if user else None,
        user_role   = user.role.value if user else None,
        action      = action,
        resource    = resource,
        resource_id = str(resource_id) if resource_id is not None else None,
        details     = details or {},
        ip_address  = _get_client_ip(request) if request else None,
    ))


def _get_client_ip(request: Request) -> Optional[str]:
    """Extrait l'IP réelle du client en tenant compte des proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return None


def purge_old_logs(db: Session) -> int:
    """
    Supprime les logs de plus d'un an.
    Retourne le nombre de lignes supprimées.
    """
    result = db.execute(
        text("DELETE FROM user_activity_logs WHERE created_at < NOW() - INTERVAL '1 year'")
    )
    db.commit()
    return result.rowcount
