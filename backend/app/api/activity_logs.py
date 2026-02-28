"""
Endpoints pour la consultation et l'export de l'historique des activités.
Accès réservé aux rôles ADMIN et SUPER_ADMIN.
"""
import csv
import io
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import UserRole

router = APIRouter()

_ADMIN_ROLES = (UserRole.ADMIN, UserRole.SUPER_ADMIN)


@router.get("")
def list_activity_logs(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
    user_login: Optional[str] = Query(None, description="Filtrer par login utilisateur"),
    action: Optional[str] = Query(None, description="Filtrer par type d'action"),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Liste paginée des activités, filtrable par utilisateur, action et période."""
    conditions = ["1=1"]
    params: dict = {}

    if user_login:
        conditions.append("user_login = :user_login")
        params["user_login"] = user_login
    if action:
        conditions.append("action = :action")
        params["action"] = action
    if from_date:
        conditions.append("created_at >= :from_date")
        params["from_date"] = from_date
    if to_date:
        conditions.append("created_at < :to_date + INTERVAL '1 day'")
        params["to_date"] = to_date

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    total = db.execute(
        text(f"SELECT COUNT(*) FROM user_activity_logs WHERE {where}"), params
    ).scalar()

    rows = db.execute(
        text(f"""
            SELECT id, user_login, user_role, action, resource, resource_id,
                   details, ip_address, created_at
            FROM user_activity_logs
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": page_size, "offset": offset},
    ).fetchall()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "items": [dict(r._mapping) for r in rows],
    }


@router.get("/export")
def export_activity_logs(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
    format: str = Query("csv", regex="^(csv)$"),
    user_login: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    """Export CSV de l'historique des activités."""
    conditions = ["1=1"]
    params: dict = {}

    if user_login:
        conditions.append("user_login = :user_login")
        params["user_login"] = user_login
    if action:
        conditions.append("action = :action")
        params["action"] = action
    if from_date:
        conditions.append("created_at >= :from_date")
        params["from_date"] = from_date
    if to_date:
        conditions.append("created_at < :to_date + INTERVAL '1 day'")
        params["to_date"] = to_date

    where = " AND ".join(conditions)

    rows = db.execute(
        text(f"""
            SELECT created_at, user_login, user_role, action,
                   resource, resource_id, details::text, ip_address
            FROM user_activity_logs
            WHERE {where}
            ORDER BY created_at DESC
        """),
        params,
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date_heure", "utilisateur", "role", "action",
                     "ressource", "ressource_id", "details", "ip"])
    for row in rows:
        writer.writerow(list(row))

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=activity_logs.csv"},
    )
