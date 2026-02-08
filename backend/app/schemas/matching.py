from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator, field_serializer
from datetime import date
from app.models.partner_quote import TransportMode
from app.schemas.partner_quote import PartnerQuoteResponse


class PriceBreakdown(BaseModel):
    pricing_type: str                    # "PER_100KG", "LUMPSUM", "PER_KG"
    unit_price: float                    # Prix unitaire de base (ex: 17.00 €/100kg)
    actual_weight: float                 # Poids demandé par l'utilisateur (ex: 250 kg)
    billable_weight: float               # Poids facturé après arrondi (ex: 300 kg)
    base_cost: float                     # unit_price × (billable_weight / 100) ou forfait
    handling_melzo: float = 0.0
    handling_local: float = 0.0
    fuel_surcharge_pct: float = 0.0
    fuel_surcharge_amount: float = 0.0
    total: float                         # Prix final
    formula: str                         # Formule lisible : "17.00 × 3 = 51.00 €"

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
    price_breakdown: Optional[PriceBreakdown] = None

    @field_serializer('cost')
    def serialize_cost(self, cost: Decimal, _info):
        return f"{cost:.2f}"
