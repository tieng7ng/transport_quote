from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel
from app.models.generated_quote import QuoteStatus


class GeneratedQuoteCreate(BaseModel):
    """Création d'un devis."""
    customer_id: str
    items: list[dict[str, Any]]
    valid_until: datetime
    metadata: Optional[dict[str, Any]] = None


class GeneratedQuoteResponse(BaseModel):
    """Réponse devis."""
    id: str
    quote_number: str
    customer_id: str
    status: QuoteStatus
    items: list[dict[str, Any]]
    total_amount: Decimal
    currency: str
    pdf_url: Optional[str] = None
    valid_until: datetime
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
