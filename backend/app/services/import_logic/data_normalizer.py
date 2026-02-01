from datetime import datetime
from typing import Any, Optional
import re

class DataNormalizer:
    
    @staticmethod
    def normalize_row(row: dict) -> dict:
        """Applique la normalisation sur chaque champ d'une ligne mappée."""
        normalized = {}
        for key, value in row.items():
            if value is None:
                normalized[key] = None
                continue
                
            clean_func_name = f"_clean_{key}"
            if hasattr(DataNormalizer, clean_func_name):
                normalized[key] = getattr(DataNormalizer, clean_func_name)(value)
            else:
                # Par défaut on strip les strings
                if isinstance(value, str):
                    normalized[key] = value.strip()
                else:
                    normalized[key] = value
                    
        return normalized

    @staticmethod
    def _clean_cost(value: Any) -> Optional[float]:
        return DataNormalizer._to_float(value)
        
    @staticmethod
    def _clean_weight_min(value: Any) -> Optional[float]:
        return DataNormalizer._to_float(value)

    @staticmethod
    def _clean_weight_max(value: Any) -> Optional[float]:
        return DataNormalizer._to_float(value)
        
    @staticmethod
    def _clean_volume_min(value: Any) -> Optional[float]:
        return DataNormalizer._to_float(value)

    @staticmethod
    def _clean_volume_max(value: Any) -> Optional[float]:
        return DataNormalizer._to_float(value)

    @staticmethod
    def _clean_transport_mode(value: Any) -> Optional[str]:
        if not value:
            return None
        return str(value).upper().strip()

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        
        # Nettoyage string "1 200,50 €" -> 1200.50
        val_str = str(value).replace(" ", "").replace("€", "").replace("$", "")
        val_str = val_str.replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return None

    @staticmethod
    def _clean_origin_postal_code(value: Any) -> Optional[str]:
        if not value:
            return None
        s = str(value).strip()
        return s[:2] if len(s) > 2 else s

    @staticmethod
    def _clean_origin_city(value: Any) -> Optional[str]:
        if not value:
            return None
        return str(value).strip().upper()

    @staticmethod
    def _clean_dest_city(value: Any) -> Optional[str]:
        if not value:
            return None
        return str(value).strip().upper()
