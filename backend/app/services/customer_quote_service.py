from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.customer_quote import CustomerQuote, CustomerQuoteItem, CustomerQuoteStatus, CustomerQuoteItemType
from app.models.partner_quote import PartnerQuote
from app.models.partner import Partner
from app.schemas.customer_quote import CustomerQuoteCreate, CustomerQuoteUpdate, CustomerQuoteItemCreate, CustomerQuoteItemUpdate
from app.services.pricing_service import PricingService
from typing import Optional, List
import uuid
import datetime

class CustomerQuoteService:
    @staticmethod
    def generate_reference(db: Session) -> str:
        """Génère une référence unique type DEV-YYYY-XXXX"""
        year = datetime.datetime.now().year
        prefix = f"DEV-{year}-"
        
        # Trouver le dernier numéro
        last_quote = db.query(CustomerQuote).filter(
            CustomerQuote.reference.like(f"{prefix}%")
        ).order_by(CustomerQuote.reference.desc()).first()
        
        if last_quote and last_quote.reference:
            last_num = int(last_quote.reference.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"{prefix}{new_num:04d}"

    @staticmethod
    def create_quote(db: Session, quote_in: CustomerQuoteCreate) -> CustomerQuote:
        reference = CustomerQuoteService.generate_reference(db)
        
        db_quote = CustomerQuote(
            id=str(uuid.uuid4()),
            reference=reference,
            customer_name=quote_in.customer_name,
            customer_email=quote_in.customer_email,
            customer_company=quote_in.customer_company,
            valid_until=quote_in.valid_until,
            currency=quote_in.currency,
            status=CustomerQuoteStatus.DRAFT
        )
        db.add(db_quote)
        db.commit()
        db.refresh(db_quote)
        return db_quote

    @staticmethod
    def get_quote(db: Session, quote_id: str) -> Optional[CustomerQuote]:
        return db.query(CustomerQuote).filter(CustomerQuote.id == quote_id).first()
    
    @staticmethod
    def get_quotes(db: Session, skip: int = 0, limit: int = 100) -> List[CustomerQuote]:
        return db.query(CustomerQuote).order_by(CustomerQuote.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def add_transport_item(db: Session, quote_id: str, partner_quote_id: str, weight: float) -> CustomerQuoteItem:
        quote = CustomerQuoteService.get_quote(db, quote_id)
        if not quote:
            raise ValueError("Quote not found")
            
        partner_quote = db.query(PartnerQuote).filter(PartnerQuote.id == partner_quote_id).first()
        if not partner_quote:
            raise ValueError("Partner rate not found")
            
        partner = db.query(Partner).filter(Partner.id == partner_quote.partner_id).first()
        default_margin = partner.default_margin if partner else 20.0
        
        # Calcul du prix d'achat (cost)
        # TODO: Logique complexe de grille tarifaire si nécessaire (pour l'instant on prend le min_price ou on simule)
        # Pour ce MVP, supposons que le prix du PartnerQuote est le prix d'achat de base pour cette tranche
        # Idéalement PartnerQuote a une structure complexe, ici on simplifie
        # On va assumer que le cost_price est calculé ailleurs ou on prend une valeur de base
        # Disons cost_price = partner_quote.price (si c'est un prix spot) 
        # Si c'est une grille, il faudrait le GridPricingService.
        # Pour avancer, on met un placeholder : cost = 100.0 * (weight/100)
        
        # NOTE: Le modèle PartnerQuote actuel est simple. Supposons qu'il contienne la donnée atomique.
        cost_price = partner_quote.cost # Simplification
        
        sell_price = PricingService.calculate_sell_price(cost_price, default_margin)
        margin_amount = PricingService.calculate_margin_amount(cost_price, sell_price)
        
        item = CustomerQuoteItem(
            id=str(uuid.uuid4()),
            quote_id=quote_id,
            item_type=CustomerQuoteItemType.TRANSPORT,
            partner_quote_id=partner_quote.id,
            description=f"Transport {partner_quote.origin_city} -> {partner_quote.dest_city}",
            
            # Snapshot
            origin_city=partner_quote.origin_city,
            origin_country=partner_quote.origin_country,
            dest_city=partner_quote.dest_city,
            dest_country=partner_quote.dest_country,
            partner_name=partner.name if partner else "Unknown",
            transport_mode=partner_quote.transport_mode,
            delivery_time=partner_quote.delivery_time,
            weight=weight,
            
            # Pricing
            cost_price=cost_price,
            sell_price=sell_price,
            margin_percent=default_margin,
            margin_amount=margin_amount,
            
            position=len(quote.items)
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        CustomerQuoteService.recalculate_quote_totals(db, quote_id)
        return item

    @staticmethod
    def add_fee_item(db: Session, quote_id: str, description: str, price: float) -> CustomerQuoteItem:
        quote = CustomerQuoteService.get_quote(db, quote_id)
        if not quote:
            raise ValueError("Quote not found")
            
        item = CustomerQuoteItem(
            id=str(uuid.uuid4()),
            quote_id=quote_id,
            item_type=CustomerQuoteItemType.FEE,
            description=description,
            
            # Pricing (Frais = Marge 100% ou Cost=0)
            cost_price=0.0,
            sell_price=price,
            margin_percent=100.0,
            margin_amount=price,
            
            position=len(quote.items)
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        CustomerQuoteService.recalculate_quote_totals(db, quote_id)
        return item

    @staticmethod
    def update_item(db: Session, item_id: str, update_data: CustomerQuoteItemUpdate) -> Optional[CustomerQuoteItem]:
        item = db.query(CustomerQuoteItem).filter(CustomerQuoteItem.id == item_id).first()
        if not item:
            return None
            
        # Logique de recalcul smart
        if update_data.sell_price is not None:
            # On fixe le prix de vente -> Recalcul Marge %
            item.sell_price = update_data.sell_price
            item.margin_percent = PricingService.calculate_margin_percent(item.cost_price, item.sell_price)
            item.margin_amount = PricingService.calculate_margin_amount(item.cost_price, item.sell_price)
            
        elif update_data.margin_percent is not None:
            # On fixe la marge % -> Recalcul Prix de vente
            item.margin_percent = update_data.margin_percent
            item.sell_price = PricingService.calculate_sell_price(item.cost_price, item.margin_percent)
            item.margin_amount = PricingService.calculate_margin_amount(item.cost_price, item.sell_price)
            
        if update_data.description:
            item.description = update_data.description
            
        db.commit()
        db.refresh(item)
        CustomerQuoteService.recalculate_quote_totals(db, item.quote_id)
        return item
        
    @staticmethod
    def remove_item(db: Session, item_id: str) -> bool:
        item = db.query(CustomerQuoteItem).filter(CustomerQuoteItem.id == item_id).first()
        if not item:
            return False
            
        quote_id = item.quote_id
        db.delete(item)
        db.commit()
        CustomerQuoteService.recalculate_quote_totals(db, quote_id)
        return True

    @staticmethod
    def recalculate_quote_totals(db: Session, quote_id: str):
        quote = db.query(CustomerQuote).filter(CustomerQuote.id == quote_id).first()
        if not quote:
            return
            
        items = quote.items
        
        transport_subtotal = sum(i.sell_price for i in items if i.item_type == CustomerQuoteItemType.TRANSPORT)
        fees_total = sum(i.sell_price for i in items if i.item_type == CustomerQuoteItemType.FEE)
        total_margin = sum(i.margin_amount for i in items)
        
        quote.transport_subtotal = transport_subtotal
        quote.fees_total = fees_total
        quote.total = transport_subtotal + fees_total
        quote.total_margin = total_margin
        
        db.commit()
        db.refresh(quote)

    @staticmethod
    def delete_quote(db: Session, quote_id: str) -> bool:
        quote = db.query(CustomerQuote).filter(CustomerQuote.id == quote_id).first()
        if not quote:
            return False
            
        db.delete(quote)
        db.commit()
        return True

    @staticmethod
    def update_quote(db: Session, quote_id: str, update_data: CustomerQuoteUpdate) -> Optional[CustomerQuote]:
        quote = db.query(CustomerQuote).filter(CustomerQuote.id == quote_id).first()
        if not quote:
            return None
            
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(quote, key, value)
            
        db.commit()
        db.refresh(quote)
        return quote
