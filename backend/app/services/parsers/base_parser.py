from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse un fichier et retourne une liste de dictionnaires.
        Chaque dictionnaire représente une ligne brute du fichier.
        """
        pass
