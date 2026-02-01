from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.partner_quote import PartnerQuote, TransportMode
from app.schemas.partner_quote import PartnerQuoteCreate

class QuoteService:
    @staticmethod
    def get_by_id(db: Session, quote_id: str) -> Optional[PartnerQuote]:
        return db.query(PartnerQuote).filter(PartnerQuote.id == quote_id).first()

    @staticmethod
    def create_quote(db: Session, quote_in: PartnerQuoteCreate) -> PartnerQuote:
        db_quote = PartnerQuote(
            partner_id=quote_in.partner_id,
            transport_mode=quote_in.transport_mode,
            origin_postal_code=quote_in.origin_postal_code,
            origin_city=quote_in.origin_city,
            origin_country=quote_in.origin_country,
            dest_postal_code=quote_in.dest_postal_code,
            dest_city=quote_in.dest_city,
            dest_country=quote_in.dest_country,
            weight_min=quote_in.weight_min,
            weight_max=quote_in.weight_max,
            volume_min=quote_in.volume_min,
            volume_max=quote_in.volume_max,
            cost=quote_in.cost,
            currency=quote_in.currency,
            delivery_time=quote_in.delivery_time,
            valid_from=quote_in.valid_from,
            valid_until=quote_in.valid_until,
            meta_data=quote_in.meta_data
        )
        db.add(db_quote)
        db.commit()
        db.refresh(db_quote)
        return db_quote

    @staticmethod
    def list_quotes(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        partner_id: Optional[str] = None,
        transport_mode: Optional[TransportMode] = None
    ) -> List[PartnerQuote]:
        query = db.query(PartnerQuote)
        
        if partner_id:
            query = query.filter(PartnerQuote.partner_id == partner_id)
        if transport_mode:
            query = query.filter(PartnerQuote.transport_mode == transport_mode)
            
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def count_quotes(db: Session, partner_id: Optional[str] = None) -> int:
        """Retourne le nombre total de tarifs, éventuellement filtré par partenaire."""
        query = db.query(PartnerQuote)
        if partner_id:
            query = query.filter(PartnerQuote.partner_id == partner_id)
        return query.count()

    @staticmethod
    def delete_quote(db: Session, quote_id: str) -> bool:
        db_quote = QuoteService.get_by_id(db, quote_id)
        if not db_quote:
            return False
        db.delete(db_quote)
        db.commit()
        return True

    @staticmethod
    def delete_all_by_partner(db: Session, partner_id: str) -> int:
        """Supprime tous les tarifs d'un partenaire."""
        # Import local pour éviter les cycles
        from app.models.customer_quote import CustomerQuoteItem
        
        # 1. Détacher les tarifs des devis clients (SET NULL) pour éviter IntegrityError
        # On cherche tous les items qui pointent vers des quotes de ce partenaire
        quotes_to_delete_subquery = db.query(PartnerQuote.id).filter(PartnerQuote.partner_id == partner_id)
        
        from datetime import datetime
        print(f"[{datetime.utcnow()}] QuoteService: Detaching quotes...")

        db.query(CustomerQuoteItem).filter(
            CustomerQuoteItem.partner_quote_id.in_(quotes_to_delete_subquery)
        ).update({CustomerQuoteItem.partner_quote_id: None}, synchronize_session=False)

        print(f"[{datetime.utcnow()}] QuoteService: Quotes detached. Deleting...")

        # 2. Supprimer les tarifs
        num_deleted = db.query(PartnerQuote).filter(PartnerQuote.partner_id == partner_id).delete(synchronize_session=False)
        db.commit()
        return num_deleted
