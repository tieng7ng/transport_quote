from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
from datetime import date
from app.models.partner_quote import TransportMode
from app.schemas.partner_quote import PartnerQuoteResponse

class QuoteSearchRequest(BaseModel):
    origin_country: str = Field(..., description="Code pays ou nom complet")
    origin_postal_code: Optional[str] = Field(default=None, description="Code postal (optionnel si ville renseignée)")
    origin_city: Optional[str] = None
    
    dest_country: str = Field(..., description="Code pays ou nom complet")
    dest_postal_code: Optional[str] = Field(default=None, description="Code postal (optionnel si ville renseignée)")
    dest_city: Optional[str] = None
    
    weight: float = Field(..., gt=0, description="Poids taxable en kg")
    volume: Optional[float] = Field(None, gt=0, description="Volume en m3 (optionnel)")
    
    transport_mode: Optional[TransportMode] = None
    shipping_date: date = Field(default_factory=date.today)

    @model_validator(mode='after')
    def check_location_requirements(self) -> 'QuoteSearchRequest':
        # Check Origin
        if not self.origin_postal_code and not self.origin_city:
            raise ValueError("L'origine nécessite au moins un Code Postal OU une Ville.")
        
        # Check Destination
        if not self.dest_postal_code and not self.dest_city:
            raise ValueError("La destination nécessite au moins un Code Postal OU une Ville.")
            
        return self

class QuoteMatchResult(PartnerQuoteResponse):
    pass
