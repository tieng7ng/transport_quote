from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.partner import PartnerCreate, PartnerUpdate, PartnerResponse
from app.services.partner_service import PartnerService
from app.services.quote_service import QuoteService
from app.services.activity_service import log_activity

router = APIRouter()

@router.post("/", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
def create_partner(
    partner_in: PartnerCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN"))
):
    """Créer un nouveau partenaire (SUPER_ADMIN)."""
    existing = PartnerService.get_by_code(db, partner_in.code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un partenaire avec le code '{partner_in.code}' existe déjà."
        )
    partner = PartnerService.create_partner(db, partner_in)
    log_activity(db, "partner.created", user=current_user, resource="partner",
                 resource_id=partner.id,
                 details={"name": partner.name, "code": partner.code},
                 request=request)
    db.commit()
    return partner

@router.get("/", response_model=List[PartnerResponse])
def list_partners(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "COMMERCIAL", "OPERATOR", "VIEWER"))
):
    """Lister tous les partenaires (Authentifié)."""
    return PartnerService.list_partners(db, skip=skip, limit=limit)

@router.get("/{partner_id}", response_model=PartnerResponse)
def get_partner(
    partner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "COMMERCIAL", "OPERATOR", "VIEWER"))
):
    """Récupérer un partenaire par son ID (Authentifié)."""
    partner = PartnerService.get_by_id(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")
    return partner

@router.put("/{partner_id}", response_model=PartnerResponse)
def update_partner(
    partner_id: str,
    partner_in: PartnerUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN"))
):
    """Mettre à jour un partenaire (SUPER_ADMIN)."""
    partner = PartnerService.update_partner(db, partner_id, partner_in)
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")
    log_activity(db, "partner.updated", user=current_user, resource="partner",
                 resource_id=partner_id,
                 details={"name": partner.name, "code": partner.code},
                 request=request)
    db.commit()
    return partner

@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(
    partner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN"))
):
    """Supprimer un partenaire (SUPER_ADMIN)."""
    success = PartnerService.delete_partner(db, partner_id)
    if not success:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")
    return None

@router.delete("/{partner_id}/quotes", status_code=status.HTTP_200_OK)
def delete_partner_quotes(
    partner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN"))
):
    """
    Supprimer tous les tarifs associés à un partenaire spécifique (ADMIN).
    Retourne le nombre de tarifs supprimés.
    """
    partner = PartnerService.get_by_id(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")

    num_deleted = QuoteService.delete_all_by_partner(db, partner_id)
    return {"message": "Tarifs supprimés avec succès", "count": num_deleted}
