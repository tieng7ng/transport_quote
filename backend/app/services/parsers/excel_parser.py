import pandas as pd
from typing import List, Dict, Any
from app.services.parsers.base_parser import BaseParser

class ExcelParser(BaseParser):
    def parse(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:
        # Lire le fichier Excel avec pandas
        sheet_name = kwargs.get("sheet_name")
        if sheet_name is None:
            sheet_name = 0
        header_row = kwargs.get("header_row", 0) # Défaut: 1ère ligne
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
        except Exception as e:
            raise ValueError(f"Erreur lecture Excel: {str(e)}")
            
        # Nettoyer les noms de colonnes
        df.columns = [str(c).lower().strip().replace(" ", "_") for c in df.columns]
        
        # Convertir en liste de dictionnaires (avec gestion des NaN -> None)
        return df.where(pd.notnull(df), None).to_dict(orient='records')
