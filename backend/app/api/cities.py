from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.city_service import CityService
from pydantic import BaseModel

router = APIRouter()

class CitySuggestion(BaseModel):
    city: str
    country: str
    count: int
    zip: Optional[str] = None

@router.get("/suggest", response_model=List[CitySuggestion])
def suggest_cities(
    q: str = Query(..., min_length=2, description="Requête de recherche (min 2 caractères)"),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Suggérer des villes pour l'autocomplétion.
    Retourne les villes correspondantes triées par pertinence (nombre de tarifs).
    """
    return CityService.suggest_cities(db, q, limit)


@router.get("/countries")
def get_countries(db: Session = Depends(get_db)):
    """
    Retourne les pays distincts disponibles dans les tarifs.
    """
    return CityService.get_countries(db)
