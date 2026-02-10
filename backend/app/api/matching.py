from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.matching import QuoteSearchRequest, QuoteMatchResult
from app.services.matching_service import MatchingService

router = APIRouter()

@router.post("/", response_model=List[QuoteMatchResult])
def match_quotes(
    criteria: QuoteSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche des tarifs correspondants aux critères.
    """
    return MatchingService.search_quotes(db, criteria)
