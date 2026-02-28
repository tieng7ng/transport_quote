"""
Endpoints alertes de sécurité : consultation, SSE stream, résolution.
Accès réservé ADMIN et SUPER_ADMIN.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import UserRole
from app.models.security_alert import SecurityAlert

router = APIRouter()

_ADMIN_ROLES = (UserRole.ADMIN, UserRole.SUPER_ADMIN)


@router.get("")
def list_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
):
    """Liste des alertes non résolues, les plus récentes en premier."""
    alerts = (
        db.query(SecurityAlert)
        .filter(SecurityAlert.resolved_at.is_(None))
        .order_by(SecurityAlert.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(a.id),
            "type": a.type,
            "severity": a.severity,
            "details": a.details,
            "seen": a.seen_at is not None,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@router.get("/stream")
async def stream_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
):
    """
    SSE — le client s'abonne et reçoit les nouvelles alertes en temps réel.
    Le frontend utilise EventSource('/api/v1/alerts/stream').
    """
    last_check = datetime.now(timezone.utc)

    async def event_generator():
        nonlocal last_check
        # Message de connexion initiale
        yield "data: {\"type\": \"connected\"}\n\n"
        while True:
            await asyncio.sleep(15)
            new_alerts = (
                db.query(SecurityAlert)
                .filter(
                    SecurityAlert.created_at > last_check,
                    SecurityAlert.resolved_at.is_(None),
                )
                .order_by(SecurityAlert.created_at.desc())
                .all()
            )
            last_check = datetime.now(timezone.utc)
            for alert in new_alerts:
                payload = json.dumps({
                    "id": str(alert.id),
                    "type": alert.type,
                    "severity": alert.severity,
                    "details": alert.details,
                    "created_at": alert.created_at.isoformat(),
                })
                yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Désactive le buffering Nginx
        },
    )


@router.patch("/{alert_id}/seen")
def mark_alert_seen(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
):
    """Marque une alerte comme vue."""
    alert = db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    if not alert.seen_at:
        alert.seen_at = datetime.now(timezone.utc)
        db.commit()
    return {"id": str(alert.id), "seen_at": alert.seen_at.isoformat()}


class ResolveRequest(BaseModel):
    resolution: str  # "account_disabled" | "ignored"


@router.patch("/{alert_id}/resolve")
def resolve_alert(
    alert_id: str,
    body: ResolveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
):
    """Résout une alerte avec une action tracée (qui + quand + comment)."""
    if body.resolution not in ("account_disabled", "ignored"):
        raise HTTPException(status_code=422, detail="resolution doit être 'account_disabled' ou 'ignored'")

    alert = db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    if alert.resolved_at:
        raise HTTPException(status_code=409, detail="Alerte déjà résolue")

    now = datetime.now(timezone.utc)
    alert.resolved_by = current_user.id
    alert.resolved_at = now
    alert.resolution = body.resolution
    if not alert.seen_at:
        alert.seen_at = now
    db.commit()

    return {
        "id": str(alert.id),
        "resolved_by": current_user.login,
        "resolved_at": alert.resolved_at.isoformat(),
        "resolution": alert.resolution,
    }
