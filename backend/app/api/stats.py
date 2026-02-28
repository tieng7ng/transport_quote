"""
Endpoints statistiques — indicateurs d'activité agrégés.
Accès réservé ADMIN et SUPER_ADMIN.
"""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import UserRole

router = APIRouter()

_ADMIN_ROLES = (UserRole.ADMIN, UserRole.SUPER_ADMIN)


def _date_params(from_date: Optional[date], to_date: Optional[date]) -> dict:
    today = date.today()
    return {
        "from_date": from_date or (today - timedelta(days=30)),
        "to_date": to_date or today,
    }


@router.get("/overview")
def stats_overview(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    """KPIs globaux : utilisateurs actifs, recherches, devis, taux de conversion."""
    p = _date_params(from_date, to_date)
    base_filter = "created_at BETWEEN :from_date AND :to_date + INTERVAL '1 day'"

    active_users = db.execute(text(f"""
        SELECT COUNT(DISTINCT user_id) FROM user_activity_logs
        WHERE {base_filter}
    """), p).scalar()

    searches = db.execute(text(f"""
        SELECT COUNT(*) FROM user_activity_logs
        WHERE action = 'search.performed' AND {base_filter}
    """), p).scalar()

    quotes_created = db.execute(text(f"""
        SELECT COUNT(*) FROM user_activity_logs
        WHERE action = 'quote.created' AND {base_filter}
    """), p).scalar()

    quotes_sent = db.execute(text(f"""
        SELECT COUNT(*) FROM user_activity_logs
        WHERE action = 'quote.status_changed'
          AND details->>'new_status' = 'SENT' AND {base_filter}
    """), p).scalar()

    quotes_accepted = db.execute(text(f"""
        SELECT COUNT(*) FROM user_activity_logs
        WHERE action = 'quote.status_changed'
          AND details->>'new_status' = 'ACCEPTED' AND {base_filter}
    """), p).scalar()

    conversion_rate = round(quotes_accepted / quotes_sent * 100, 1) if quotes_sent else 0

    return {
        "period": {"from": str(p["from_date"]), "to": str(p["to_date"])},
        "active_users": active_users,
        "searches": searches,
        "quotes_created": quotes_created,
        "quotes_sent": quotes_sent,
        "quotes_accepted": quotes_accepted,
        "conversion_rate_pct": conversion_rate,
    }


@router.get("/activity")
def stats_daily_activity(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    """Activité journalière : connexions + recherches sur la période."""
    p = _date_params(from_date, to_date)
    rows = db.execute(text("""
        SELECT DATE(created_at) AS day,
               COUNT(*) AS total,
               COUNT(DISTINCT user_id) AS unique_users
        FROM user_activity_logs
        WHERE created_at BETWEEN :from_date AND :to_date + INTERVAL '1 day'
          AND action IN ('auth.login_success', 'search.performed')
        GROUP BY DATE(created_at)
        ORDER BY day
    """), p).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/searches")
def stats_searches(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    limit: int = Query(10, ge=1, le=50),
):
    """Top routes recherchées, répartition par mode de transport, taux résultat nul."""
    p = _date_params(from_date, to_date)
    filter_clause = "action = 'search.performed' AND created_at BETWEEN :from_date AND :to_date + INTERVAL '1 day'"

    top_routes = db.execute(text(f"""
        SELECT details->>'origin_city'    AS origin,
               details->>'dest_city'      AS destination,
               details->>'transport_mode' AS mode,
               COUNT(*) AS search_count
        FROM user_activity_logs
        WHERE {filter_clause}
        GROUP BY details->>'origin_city', details->>'dest_city', details->>'transport_mode'
        ORDER BY search_count DESC
        LIMIT :limit
    """), {**p, "limit": limit}).fetchall()

    by_mode = db.execute(text(f"""
        SELECT details->>'transport_mode' AS mode, COUNT(*) AS count
        FROM user_activity_logs
        WHERE {filter_clause}
        GROUP BY details->>'transport_mode'
        ORDER BY count DESC
    """), p).fetchall()

    total = db.execute(text(f"SELECT COUNT(*) FROM user_activity_logs WHERE {filter_clause}"), p).scalar()
    no_results = db.execute(text(f"""
        SELECT COUNT(*) FROM user_activity_logs
        WHERE {filter_clause} AND (details->>'results_count')::int = 0
    """), p).scalar()

    return {
        "top_routes": [dict(r._mapping) for r in top_routes],
        "by_transport_mode": [dict(r._mapping) for r in by_mode],
        "total_searches": total,
        "no_results_count": no_results,
        "no_results_rate_pct": round(no_results / total * 100, 1) if total else 0,
    }


@router.get("/quotes")
def stats_quotes(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    """Entonnoir de conversion des devis + activité par commercial."""
    p = _date_params(from_date, to_date)
    base = "created_at BETWEEN :from_date AND :to_date + INTERVAL '1 day'"

    funnel = db.execute(text(f"""
        SELECT user_login, user_role,
               COUNT(*) FILTER (WHERE action = 'quote.created') AS created,
               COUNT(*) FILTER (WHERE action = 'quote.status_changed'
                   AND details->>'new_status' = 'SENT')         AS sent,
               COUNT(*) FILTER (WHERE action = 'quote.status_changed'
                   AND details->>'new_status' = 'ACCEPTED')     AS accepted,
               COUNT(*) FILTER (WHERE action = 'quote.status_changed'
                   AND details->>'new_status' = 'REJECTED')     AS rejected
        FROM user_activity_logs
        WHERE action IN ('quote.created', 'quote.status_changed') AND {base}
        GROUP BY user_login, user_role
        ORDER BY created DESC
    """), p).fetchall()

    return {"by_user": [dict(r._mapping) for r in funnel]}


@router.get("/imports")
def stats_imports(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    """Statistiques des imports : taux de succès, volumes par partenaire."""
    p = _date_params(from_date, to_date)
    base = "created_at BETWEEN :from_date AND :to_date + INTERVAL '1 day'"

    rows = db.execute(text(f"""
        SELECT details->>'partner' AS partner,
               COUNT(*) FILTER (WHERE action = 'import.completed') AS completed,
               COUNT(*) FILTER (WHERE action = 'import.failed')    AS failed,
               SUM((details->>'rows_imported')::int)
                   FILTER (WHERE action = 'import.completed')      AS total_rows
        FROM user_activity_logs
        WHERE action IN ('import.completed', 'import.failed') AND {base}
        GROUP BY details->>'partner'
        ORDER BY completed DESC
    """), p).fetchall()

    return [dict(r._mapping) for r in rows]


@router.get("/security")
def stats_security(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*_ADMIN_ROLES)),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    """Échecs de connexion et IPs suspectes sur la période."""
    p = _date_params(from_date, to_date)
    base = "created_at BETWEEN :from_date AND :to_date + INTERVAL '1 day'"

    failures = db.execute(text(f"""
        SELECT details->>'attempted_login' AS login,
               ip_address,
               COUNT(*) AS failures
        FROM user_activity_logs
        WHERE action = 'auth.login_failed' AND {base}
        GROUP BY details->>'attempted_login', ip_address
        ORDER BY failures DESC
        LIMIT 20
    """), p).fetchall()

    return {"login_failures": [dict(r._mapping) for r in failures]}
