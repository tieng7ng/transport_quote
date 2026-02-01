from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from app.core import database as deps
from app.schemas.customer_quote import (
    CustomerQuoteCreate,
    CustomerQuoteUpdate,
    CustomerQuoteResponse,
    CustomerQuoteItemResponse,
    CustomerQuoteItemUpdate,
    CustomerQuoteItemCreate
)
from app.services.customer_quote_service import CustomerQuoteService
from app.models.customer_quote import CustomerQuoteItem, CustomerQuote

router = APIRouter()

@router.post("/", response_model=CustomerQuoteResponse)
def create_quote(
    quote_in: CustomerQuoteCreate,
    db: Session = Depends(deps.get_db)
):
    """Créer un nouveau brouillon de devis."""
    return CustomerQuoteService.create_quote(db, quote_in)

@router.get("/", response_model=List[CustomerQuoteResponse])
def read_quotes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """Lister les devis."""
    return CustomerQuoteService.get_quotes(db, skip=skip, limit=limit)

@router.get("/{quote_id}", response_model=CustomerQuoteResponse)
def read_quote(
    quote_id: str,
    db: Session = Depends(deps.get_db)
):
    """Obtenir le détail d'un devis."""
    quote = CustomerQuoteService.get_quote(db, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

# --- Items Transport ---

@router.post("/{quote_id}/items", response_model=CustomerQuoteItemResponse)
def add_transport_item(
    quote_id: str,
    item_in: CustomerQuoteItemCreate,
    db: Session = Depends(deps.get_db)
):
    """Ajouter une ligne de transport (copie du tarif partenaire)."""
    if not item_in.partner_quote_id:
        raise HTTPException(status_code=400, detail="partner_quote_id required for transport items")
        
    try:
        # Poids par défaut à 100kg si non fourni (provisoire)
        weight = item_in.weight if item_in.weight is not None else 100.0
        return CustomerQuoteService.add_transport_item(
            db, quote_id, item_in.partner_quote_id, weight
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Items Frais ---

@router.post("/{quote_id}/fees", response_model=CustomerQuoteItemResponse)
def add_fee_item(
    quote_id: str,
    item_in: CustomerQuoteItemCreate,
    db: Session = Depends(deps.get_db)
):
    """Ajouter une ligne de frais manuels."""
    return CustomerQuoteService.add_fee_item(
        db, quote_id, item_in.description, item_in.sell_price
    )

# --- Modification Items ---

@router.put("/{quote_id}/items/{item_id}", response_model=CustomerQuoteItemResponse)
def update_item(
    quote_id: str,
    item_id: str,
    item_in: CustomerQuoteItemUpdate,
    db: Session = Depends(deps.get_db)
):
    """Modifier une ligne (prix, marge, description)."""
    item = CustomerQuoteService.update_item(db, item_id, item_in)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/{quote_id}/items/{item_id}")
def remove_item(
    quote_id: str,
    item_id: str,
    db: Session = Depends(deps.get_db)
):
    """Supprimer une ligne."""
    success = CustomerQuoteService.remove_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "success"}

@router.put("/{quote_id}", response_model=CustomerQuoteResponse)
def update_quote(
    quote_id: str,
    quote_in: CustomerQuoteUpdate,
    db: Session = Depends(deps.get_db)
):
    """Mettre à jour un devis."""
    quote = CustomerQuoteService.update_quote(db, quote_id, quote_in)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@router.delete("/{quote_id}")
def delete_quote(
    quote_id: str,
    db: Session = Depends(deps.get_db)
):
    """Supprimer un devis."""
    success = CustomerQuoteService.delete_quote(db, quote_id)
    if not success:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"status": "success"}
