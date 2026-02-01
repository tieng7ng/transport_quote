import pdfplumber
from typing import List, Dict, Any
from app.services.parsers.base_parser import BaseParser

class PdfParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extraction simplifiée pour MVP.
        Tente d'extraire les tableaux de chaque page.
        """
        results = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # Extraire les tableaux
                    tables = page.extract_tables()
                    
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                            
                        # Supposons que la première ligne est le header
                        headers = [str(h).lower().strip().replace(" ", "_") if h else f"col_{i}" for i, h in enumerate(table[0])]
                        
                        # Parcourir les lignes de données
                        for row in table[1:]:
                            # Créer un dictionnaire pour la ligne
                            # On s'assure de ne pas dépasser la longueur des headers
                            row_data = {}
                            for i, val in enumerate(row):
                                if i < len(headers):
                                    row_data[headers[i]] = val
                            
                            # Ignorer les lignes vides
                            if any(row_data.values()):
                                results.append(row_data)
                                
        except Exception as e:
            raise ValueError(f"Erreur lecture PDF: {str(e)}")
            
        return results
