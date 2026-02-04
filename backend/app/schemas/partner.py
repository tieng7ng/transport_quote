from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class PartnerBase(BaseModel):
    code: str
    name: str
    email: Optional[EmailStr] = None


class PartnerCreate(PartnerBase):
    """Création d'un partenaire."""
    pass


class PartnerUpdate(BaseModel):
    """Mise à jour d'un partenaire."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    rating: Optional[float] = None
    is_active: Optional[bool] = None


class PartnerResponse(PartnerBase):
    """Réponse partenaire."""
    id: str
    rating: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
