from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from app.models.customer_quote import CustomerQuoteStatus, CustomerQuoteItemType

# --- Items ---

class CustomerQuoteItemBase(BaseModel):
    item_type: CustomerQuoteItemType = Field(default=CustomerQuoteItemType.TRANSPORT)
    description: str
    position: int = 0
    # Valide pour les deux types
    sell_price: float
    margin_percent: Optional[float] = None
    margin_amount: float
    cost_price: float = 0.0

class CustomerQuoteItemCreate(CustomerQuoteItemBase):
    # Pour TRANSPORT
    partner_quote_id: Optional[str] = None
    weight: Optional[float] = None
    
    # Pour FEE, on attend surtout description + price (+ margin implicite 100% ou cost 0)

class CustomerQuoteItemUpdate(BaseModel):
    # On peut updater le prix / marge
    sell_price: Optional[float] = None
    margin_percent: Optional[float] = None
    description: Optional[str] = None

class CustomerQuoteItemResponse(CustomerQuoteItemBase):
    id: str
    quote_id: str
    
    # Snapshot Transport
    origin_city: Optional[str] = None
    origin_country: Optional[str] = None
    dest_city: Optional[str] = None
    dest_country: Optional[str] = None
    partner_name: Optional[str] = None
    transport_mode: Optional[str] = None
    delivery_time: Optional[str] = None
    weight: Optional[float] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Quotes ---

class CustomerQuoteBase(BaseModel):
    reference: Optional[str] = None # Peut être généré
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_company: Optional[str] = None
    valid_until: Optional[datetime] = None
    currency: str = "EUR"

class CustomerQuoteCreate(CustomerQuoteBase):
    pass

class CustomerQuoteUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_company: Optional[str] = None
    valid_until: Optional[datetime] = None
    status: Optional[CustomerQuoteStatus] = None

class CustomerQuoteResponse(CustomerQuoteBase):
    id: str
    reference: str
    status: CustomerQuoteStatus
    
    transport_subtotal: float
    fees_total: float
    total: float
    total_margin: float
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    items: List[CustomerQuoteItemResponse] = []
    
    class Config:
        from_attributes = True
