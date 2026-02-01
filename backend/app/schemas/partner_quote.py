from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.models.partner_quote import TransportMode
from app.schemas.partner import PartnerResponse


class PartnerQuoteBase(BaseModel):
    transport_mode: TransportMode
    origin_postal_code: Optional[str] = Field(None, max_length=2)
    origin_city: str
    origin_country: str
    dest_postal_code: Optional[str] = None
    dest_city: str
    dest_country: str
    weight_min: Optional[float] = None
    weight_max: Optional[float] = None
    volume_min: Optional[float] = None
    volume_max: Optional[float] = None
    cost: Decimal
    pricing_type: Optional[str] = "PER_100KG"
    currency: str = "EUR"
    delivery_time: Optional[str] = None


class PartnerQuoteCreate(PartnerQuoteBase):
    """Création d'un tarif."""
    partner_id: str
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    meta_data: Optional[dict[str, Any]] = None


class PartnerQuoteResponse(PartnerQuoteBase):
    """Réponse tarif."""
    id: str
    partner_id: str
    valid_from: datetime
    valid_until: Optional[datetime]
    is_active: bool
    import_job_id: Optional[str]
    created_at: datetime
    partner: "PartnerResponse"

    class Config:
        from_attributes = True


class MatchRequest(BaseModel):
    """Requête de recherche de tarifs."""
    origin_postal_code: Optional[str] = Field(None, max_length=2)
    origin_city: Optional[str] = None
    origin_country: str
    dest_postal_code: Optional[str] = None
    dest_city: Optional[str] = None
    dest_country: str
    weight: Optional[float] = None
    volume: Optional[float] = None
    transport_mode: Optional[TransportMode] = None
    sort_by: str = "cost"
    limit: int = 10


class MatchResponse(BaseModel):
    """Réponse avec les tarifs correspondants."""
    quotes: list[PartnerQuoteResponse]
    total: int
