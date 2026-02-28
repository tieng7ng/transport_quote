from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.matching import QuoteSearchRequest, QuoteMatchResult
from app.services.matching_service import MatchingService
from app.services.activity_service import log_activity

router = APIRouter()

@router.post("/", response_model=List[QuoteMatchResult])
def match_quotes(
    criteria: QuoteSearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche des tarifs correspondants aux critères.
    """
    results = MatchingService.search_quotes(db, criteria)
    log_activity(db, "search.performed", user=current_user, resource="search",
                 details={
                     **criteria.model_dump(exclude_none=True),
                     "results_count": len(results),
                 },
                 request=request)
    db.commit()
    return results
