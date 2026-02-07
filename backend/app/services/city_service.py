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
                func.count(PartnerQuote.id).label("count"),
                func.max(PartnerQuote.origin_postal_code).label("zip")
            )
            .filter(PartnerQuote.origin_city.ilike(search))
            .group_by(PartnerQuote.origin_city, PartnerQuote.origin_country)
        )
        
        # Recherche dans les destinations
        destinations = (
            db.query(
                PartnerQuote.dest_city.label("city"),
                PartnerQuote.dest_country.label("country"),
                func.count(PartnerQuote.id).label("count"),
                func.max(PartnerQuote.dest_postal_code).label("zip")
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
            # On garde le zip s'il existe (priorité à celui qu'on trouve)
            current_zip = getattr(row, "zip", None)
            if key in results:
                 results[key]["count"] += row.count
                 # Si on avait pas de zip et que maintenant on en a un, on update
                 if not results[key]["zip"] and current_zip:
                      results[key]["zip"] = current_zip
            else:
                 results[key] = {"count": row.count, "zip": current_zip}

        for row in destinations.all():
            key = (row.city, row.country)
            current_zip = getattr(row, "zip", None)
            if key in results:
                 results[key]["count"] += row.count
                 if not results[key]["zip"] and current_zip:
                      results[key]["zip"] = current_zip
            else:
                 results[key] = {"count": row.count, "zip": current_zip}

        # Convertir en liste triée
        final_list = [
            {"city": city, "country": country, "count": data["count"], "zip": data["zip"]}
            for (city, country), data in results.items()
        ]
        
        # Tri par pertinence (nombre de tarifs) puis alphabétique
        final_list.sort(key=lambda x: (-x["count"], x["city"]))
        
        return final_list[:limit]

    @staticmethod
    def get_countries(db: Session) -> dict:
        """
        Retourne les pays distincts présents dans les tarifs.
        Normalise les codes pays (trim + uppercase) pour éviter les doublons.
        """
        origin_countries = (
            db.query(PartnerQuote.origin_country)
            .filter(PartnerQuote.origin_country.isnot(None))
            .distinct()
            .all()
        )
        dest_countries = (
            db.query(PartnerQuote.dest_country)
            .filter(PartnerQuote.dest_country.isnot(None))
            .distinct()
            .all()
        )
        
        # Deduplicate + Normalize -> set
        origins = set()
        for r in origin_countries:
            if r[0]:
                code = r[0].strip().upper()
                if len(code) == 2:
                    origins.add(code)
                    
        dests = set()
        for r in dest_countries:
            if r[0]:
                code = r[0].strip().upper()
                if len(code) == 2:
                    dests.add(code)

        return {
            "origin_countries": sorted(list(origins)),
            "dest_countries": sorted(list(dests)),
        }
