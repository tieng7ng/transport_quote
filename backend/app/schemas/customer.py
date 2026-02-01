from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class CustomerBase(BaseModel):
    email: EmailStr
    company: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Création d'un client."""
    pass


class CustomerUpdate(BaseModel):
    """Mise à jour d'un client."""
    company: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class CustomerResponse(CustomerBase):
    """Réponse client."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
