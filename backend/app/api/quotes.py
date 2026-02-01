from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.partner_quote import TransportMode
from app.schemas.partner_quote import PartnerQuoteCreate, PartnerQuoteResponse
from app.services.quote_service import QuoteService

router = APIRouter()

@router.post("/", response_model=PartnerQuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(
    quote_in: PartnerQuoteCreate,
    db: Session = Depends(get_db)
):
    """Créer un nouveau tarif."""
    return QuoteService.create_quote(db, quote_in)

@router.get("/", response_model=List[PartnerQuoteResponse])
def list_quotes(
    skip: int = 0,
    limit: int = 100,
    partner_id: Optional[str] = Query(None, description="Filtrer par partenaire"),
    transport_mode: Optional[TransportMode] = Query(None, description="Filtrer par mode de transport"),
    db: Session = Depends(get_db)
):
    """Lister les tarifs (avec filtres optionnels)."""
    return QuoteService.list_quotes(
        db, 
        skip=skip, 
        limit=limit,
        partner_id=partner_id,
        transport_mode=transport_mode
    )

@router.get("/count", response_model=int)
def count_quotes(
    partner_id: Optional[str] = Query(None, description="Filtrer par partenaire"),
    db: Session = Depends(get_db)
):
    """Obtenir le nombre total de tarifs."""
    return QuoteService.count_quotes(db, partner_id=partner_id)

@router.get("/{quote_id}", response_model=PartnerQuoteResponse)
def get_quote(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Récupérer un tarif par ID."""
    quote = QuoteService.get_by_id(db, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Tarif non trouvé")
    return quote

@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Supprimer un tarif."""
    success = QuoteService.delete_quote(db, quote_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tarif non trouvé")
    return None
