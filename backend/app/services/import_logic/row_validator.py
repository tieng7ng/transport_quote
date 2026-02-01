import math
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ValidationError, validator, Field
from app.models.partner_quote import TransportMode


def sanitize_value(val: Any) -> Any:
    """Convertit NaN/Infinity en None pour compatibilité JSON."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


class ValidationErrorItem(BaseModel):
    field: str
    message: str
    value: Any

class ValidationResult(BaseModel):
    is_valid: bool
    data: Optional[Dict[str, Any]] = None
    errors: List[ValidationErrorItem] = []

class QuoteImportSchema(BaseModel):
    transport_mode: TransportMode
    origin_city: str
    origin_country: str
    dest_city: str
    dest_country: str
    cost: float = Field(gt=0, description="Le prix doit être positif")
    pricing_type: str = "PER_100KG"
    currency: str = "EUR"
    
    # Champs optionnels
    origin_postal_code: Optional[str] = None
    dest_postal_code: Optional[str] = None
    weight_min: Optional[float] = None
    weight_max: Optional[float] = None
    
    @validator('origin_country', 'dest_country')
    def validate_country_code(cls, v):
        if len(v) != 2:
            raise ValueError('Code pays doit faire 2 caractères (ISO)')
        return v.upper()

class RowValidator:
    def validate(self, row_data: Dict[str, Any]) -> ValidationResult:
        try:
            # Pydantic va valider les types et les contraintes (@validator, Field)
            schema = QuoteImportSchema(**row_data)
            return ValidationResult(is_valid=True, data=schema.model_dump())
            
        except ValidationError as e:
            errors = []
            for err in e.errors():
                # Extraction simplifiée de l'erreur
                field = err["loc"][0] if err["loc"] else "unknown"
                msg = err["msg"]
                val = sanitize_value(row_data.get(str(field)))
                errors.append(ValidationErrorItem(field=str(field), message=msg, value=val))

            return ValidationResult(is_valid=False, errors=errors)
