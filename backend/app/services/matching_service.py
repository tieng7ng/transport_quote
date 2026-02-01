from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, cast, Date
from app.models.partner_quote import PartnerQuote
from app.schemas.matching import QuoteSearchRequest

class MatchingService:
    @staticmethod
    def search_quotes(db: Session, criteria: QuoteSearchRequest) -> List[PartnerQuote]:
        query = db.query(PartnerQuote)
        
        # 1. Filtre par mode de transport (si spécifié)
        if criteria.transport_mode:
            query = query.filter(PartnerQuote.transport_mode == criteria.transport_mode)
            
        # 2. Filtre par Pays (Correspondance exacte)
        # Note: Idéalement normaliser les codes pays (ISO) en amont
        query = query.filter(
            PartnerQuote.origin_country.ilike(criteria.origin_country),
            PartnerQuote.dest_country.ilike(criteria.dest_country)
        )

        # 2b. Optimisation SQL: Code Postal (2 chars)
        if criteria.origin_postal_code:
             # On ne garde que les 2 premiers caractères pour matcher le format DB
             search_origin = str(criteria.origin_postal_code).strip()[:2]
             query = query.filter(
                 or_(
                     PartnerQuote.origin_postal_code == search_origin,
                     # On garde aussi les NULL pour permettre le matching par Ville plus tard si le CP n'est pas renseigné sur le devis
                     PartnerQuote.origin_postal_code.is_(None)
                 )
             )
             
        if criteria.dest_postal_code:
             search_dest = str(criteria.dest_postal_code).strip()[:2]
             query = query.filter(
                 or_(
                     PartnerQuote.dest_postal_code == search_dest,
                     PartnerQuote.dest_postal_code.is_(None)
                 )
             )
        
        # 3. Filtre par Poids (Range)
        query = query.filter(
            PartnerQuote.weight_min <= criteria.weight,
            PartnerQuote.weight_max >= criteria.weight
        )
        
        # 4. Filtre par Date de validité (Comparaison sur la DATE uniquement, sans l'heure)
        query = query.filter(
            or_(cast(PartnerQuote.valid_from, Date) <= criteria.shipping_date, PartnerQuote.valid_from.is_(None)),
            or_(cast(PartnerQuote.valid_until, Date) >= criteria.shipping_date, PartnerQuote.valid_until.is_(None))
        )
        
        # Exécution de la requête de base
        potential_quotes = query.all()
        
        # 5. Filtrage fin en Python (Codes Postaux OU Ville) ET Calcul du prix
        matched_quotes = []
        
        # Import local pour éviter les cycles si nécessaire, sinon utiliser Math
        import math

        for quote in potential_quotes:
            valid_origin = MatchingService._is_location_match(
                criteria.origin_postal_code, criteria.origin_city,
                quote.origin_postal_code, quote.origin_city
            )
            valid_dest = MatchingService._is_location_match(
                criteria.dest_postal_code, criteria.dest_city,
                quote.dest_postal_code, quote.dest_city
            )
            
            if valid_origin and valid_dest:
                # CLONE the quote to avoid modifying the DB session object directly, 
                # or ensure Pydantic serialization happens from a dict/copy.
                # Actually, sqlalchemy objects are mutable. Modifying them might dirty the session.
                # Safer to construct a response dictionary or let Pydantic handle it, 
                # BUT we need to override 'cost' with 'total_price'.
                # Let's assign the calculated price to 'cost' on the object BUT detach it first or accept it's a Transient object if query didn't lock.
                # Better: Create a copy/dict.
                
                # Logic Calcul
                computed_cost = quote.cost
                pricing_type = getattr(quote, 'pricing_type', 'PER_100KG') # Default if older migration
                
                if pricing_type == 'PER_100KG':
                    # Arrondi à la centaine supérieure
                    # Ex: 150kg -> 200kg. 200/100 * cost
                    billable_weight = math.ceil(criteria.weight / 100) * 100
                    computed_cost = float(quote.cost) * (billable_weight / 100)
                elif pricing_type == 'PER_KG':
                    computed_cost = float(quote.cost) * criteria.weight
                elif pricing_type == 'LUMPSUM':
                    computed_cost = float(quote.cost)
                # else (PER_PALLET, etc.) -> Standard cost if no logic implemented yet
                
                # We need to return an object that looks like PartnerQuote but with updated cost.
                # We can just set quote.cost = computed_cost if we are careful not to commit.
                # Since this is a read-only operation and we don't call db.commit(), strictly speaking it's "safe" 
                # but good practice is to not mutate DB objects.
                # Let's rely on the fact we don't commit.
                quote.cost = computed_cost
                matched_quotes.append(quote)
                
        return matched_quotes

    @staticmethod
    def _is_location_match(search_cp: str, search_city: str, quote_cp: str, quote_city: str) -> bool:
        """
        Vérifie la correspondance géographique.
        Priorité 1: Code Postal (Prefix Match)
        Priorité 2: Ville (Exact Match insensible à la casse) si CP manquant
        """
        # 1. Matching par Code Postal (Prioritaire si le devis en a un)
        if quote_cp:
            if not search_cp:
                # Le devis est spécifique (CP) mais la recherche est large (Ville uniquement ou rien)
                # On ne peut pas garantir que la Ville correspond au CP sans géocodage.
                # Par sécurité, on peut refuser, OU vérifier si la ville match aussi.
                # Pour l'instant: Si user cherche sans CP, on ignore les devis avec CP spécifique ? 
                # Non, "Nice" doit matcher "06000 Nice".
                # Simplification: Si User n'a pas de CP, on check la ville.
                if search_city and quote_city:
                    return search_city.strip().upper() == quote_city.strip().upper()
                return False # Pas de CP recherche et pas de correspondance ville possible
            
            # CP vs CP
            clean_search_cp = str(search_cp).strip().upper()
            clean_quote_cp = str(quote_cp).strip().upper()
            
            if clean_search_cp.startswith(clean_quote_cp):
                 # CP Match OK. Verifions la Ville si demandée
                 if search_city and quote_city:
                     s_city = search_city.strip().upper()
                     q_city = quote_city.strip().upper()
                     
                     if q_city == "ALL": return True
                     if s_city == q_city: return True
                     return False
                     
                 return True

        # 2. Matching par Ville (Si le devis n'a PAS de CP)
        if quote_city:
            if not search_city:
                return False # Devis spécifique ville, recherche sans ville (et sans CP matché avant)
            return search_city.strip().upper() == quote_city.strip().upper()

        # 3. Wildcard (Pas de CP ni Ville sur le devis)
        return True
