from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.partner_quote import PartnerQuote

class CityService:
    @staticmethod
    def suggest_cities(db: Session, query: str, limit: int = 10) -> List[dict]:
        """
        Suggérer des villes basées sur les tarifs existants.
        Recherche insensible à la casse dans origin_city et dest_city.
        Retourne une liste de {city: str, country: str, count: int}
        """
        if not query or len(query) < 2:
            return []
            
        search = f"%{query}%"
        
        # Recherche dans les origines
        origins = (
            db.query(
                PartnerQuote.origin_city.label("city"),
                PartnerQuote.origin_country.label("country"),
                func.count(PartnerQuote.id).label("count")
            )
            .filter(PartnerQuote.origin_city.ilike(search))
            .group_by(PartnerQuote.origin_city, PartnerQuote.origin_country)
        )
        
        # Recherche dans les destinations
        destinations = (
            db.query(
                PartnerQuote.dest_city.label("city"),
                PartnerQuote.dest_country.label("country"),
                func.count(PartnerQuote.id).label("count")
            )
            .filter(PartnerQuote.dest_city.ilike(search))
            .group_by(PartnerQuote.dest_city, PartnerQuote.dest_country)
        )
        
        # Union et tri
        # Note: SQLAlchemy union might be tricky with complex ordering, 
        # simpler to fetch both and merge in python for this use case 
        # as the number of unique cities is essentially low.
        
        results = {}
        
        for row in origins.all():
            key = (row.city, row.country)
            results[key] = results.get(key, 0) + row.count
            
        for row in destinations.all():
            key = (row.city, row.country)
            results[key] = results.get(key, 0) + row.count
            
        # Convertir en liste triée
        final_list = [
            {"city": city, "country": country, "count": count}
            for (city, country), count in results.items()
        ]
        
        # Tri par pertinence (nombre de tarifs) puis alphabétique
        final_list.sort(key=lambda x: (-x["count"], x["city"]))
        
        return final_list[:limit]
