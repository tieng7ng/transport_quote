from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau brouillon de devis."""
    return CustomerQuoteService.create_quote(db, quote_in, current_user.id)

@router.get("/", response_model=List[CustomerQuoteResponse])
def read_quotes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lister les devis.
    COMMERCIAL : voit uniquement ses devis.
    ADMIN/OPERATOR/SUPER_ADMIN : voient tout.
    """
    owner_id = None
    if current_user.role == "COMMERCIAL":
        owner_id = current_user.id
        
    return CustomerQuoteService.get_quotes(db, skip=skip, limit=limit, owner_id=owner_id)

@router.get("/{quote_id}", response_model=CustomerQuoteResponse)
def read_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir le détail d'un devis."""
    quote = CustomerQuoteService.get_quote(db, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Optional: Check ownership for COMMERCIAL? 
    # For now, plan says "Tous authentifiés"
    
    return quote

# --- Items Transport ---

@router.post("/{quote_id}/items", response_model=CustomerQuoteItemResponse)
def add_transport_item(
    quote_id: str,
    item_in: CustomerQuoteItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "COMMERCIAL", "OPERATOR"))
):
    """Ajouter une ligne de transport (copie du tarif partenaire)."""
    if not item_in.partner_quote_id:
        raise HTTPException(status_code=400, detail="partner_quote_id required for transport items")
        
    try:
        # Poids par défaut à 100kg si non fourni (provisoire)
        weight = item_in.weight if item_in.weight is not None else 100.0
        
        # Note: We might want to update updated_by here too
        # But add_transport_item service doesn't take user_id yet
        # For now, just RBAC
        
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "COMMERCIAL", "OPERATOR"))
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "COMMERCIAL", "OPERATOR"))
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "COMMERCIAL", "OPERATOR"))
):
    """Mettre à jour un devis."""
    quote = CustomerQuoteService.update_quote(db, quote_id, quote_in, current_user.id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@router.delete("/{quote_id}")
def delete_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
):
    """Supprimer un devis."""
    success = CustomerQuoteService.delete_quote(db, quote_id)
    if not success:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"status": "success"}
