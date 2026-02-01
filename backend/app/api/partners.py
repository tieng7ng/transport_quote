from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.partner import PartnerCreate, PartnerUpdate, PartnerResponse
from app.services.partner_service import PartnerService
from app.services.quote_service import QuoteService

router = APIRouter()

@router.post("/", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
def create_partner(
    partner_in: PartnerCreate,
    db: Session = Depends(get_db)
):
    """Créer un nouveau partenaire."""
    # Vérifier doublon code
    existing = PartnerService.get_by_code(db, partner_in.code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un partenaire avec le code '{partner_in.code}' existe déjà."
        )
    return PartnerService.create_partner(db, partner_in)

@router.get("/", response_model=List[PartnerResponse])
def list_partners(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lister tous les partenaires."""
    return PartnerService.list_partners(db, skip=skip, limit=limit)

@router.get("/{partner_id}", response_model=PartnerResponse)
def get_partner(
    partner_id: str,
    db: Session = Depends(get_db)
):
    """Récupérer un partenaire par son ID."""
    partner = PartnerService.get_by_id(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")
    return partner

@router.put("/{partner_id}", response_model=PartnerResponse)
def update_partner(
    partner_id: str,
    partner_in: PartnerUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un partenaire."""
    partner = PartnerService.update_partner(db, partner_id, partner_in)
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")
    return partner

@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(
    partner_id: str,
    db: Session = Depends(get_db)
):
    """Supprimer un partenaire."""
    success = PartnerService.delete_partner(db, partner_id)
    if not success:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")
    return None

@router.delete("/{partner_id}/quotes", status_code=status.HTTP_200_OK)
def delete_partner_quotes(
    partner_id: str,
    db: Session = Depends(get_db)
):
    """
    Supprimer tous les tarifs associés à un partenaire spécifique.
    Retourne le nombre de tarifs supprimés.
    """
    # Vérifier l'existence du partenaire (optionnel mais recommandé)
    partner = PartnerService.get_by_id(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")
        
    num_deleted = QuoteService.delete_all_by_partner(db, partner_id)
    return {"message": "Tarifs supprimés avec succès", "count": num_deleted}
