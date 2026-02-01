import pandas as pd
from typing import List, Dict, Any
from app.services.parsers.base_parser import BaseParser

class CsvParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        # Lire le CSV avec pandas
        # On suppose par défaut un séparateur virgule, mais on peut améliorer la détection
        try:
            df = pd.read_csv(file_path)
        except Exception:
            # Fallback : essayer avec point-virgule si virgule échoue
            df = pd.read_csv(file_path, sep=';')
            
        # Nettoyer les noms de colonnes (minuscules, strip, remplace espaces par _)
        df.columns = [str(c).lower().strip().replace(" ", "_") for c in df.columns]
        
        # Convertir en liste de dictionnaires (avec gestion des NaN -> None)
        return df.where(pd.notnull(df), None).to_dict(orient='records')
