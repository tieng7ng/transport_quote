from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import datetime

class CustomerQuoteStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class CustomerQuoteItemType(str, enum.Enum):
    TRANSPORT = "TRANSPORT"   # Trajet issu d'un tarif partenaire
    FEE = "FEE"               # Frais ajouté manuellement

class CustomerQuote(Base):
    __tablename__ = "customer_quotes"

    id = Column(String, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)  # DEV-2026-XXXX
    status = Column(Enum(CustomerQuoteStatus), default=CustomerQuoteStatus.DRAFT, index=True)

    # Client (optionnel en brouillon)
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_company = Column(String, nullable=True)
    # Relation optionnelle vers un Customer enregistré
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)

    # Totaux
    transport_subtotal = Column(Numeric(10, 2), default=0)  # Sous-total transports
    fees_total = Column(Numeric(10, 2), default=0)          # Total frais
    total = Column(Numeric(10, 2), default=0)               # Grand total
    total_margin = Column(Numeric(10, 2), default=0)        # Marge totale
    currency = Column(String, default="EUR")

    # Validité et tracking
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    sent_at = Column(DateTime, nullable=True)

    # Relations
    items = relationship("CustomerQuoteItem", back_populates="quote", cascade="all, delete-orphan")
    customer = relationship("Customer")

    # Author Tracking
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships with User
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

class CustomerQuoteItem(Base):
    __tablename__ = "customer_quote_items"

    id = Column(String, primary_key=True, index=True)
    quote_id = Column(String, ForeignKey("customer_quotes.id", ondelete="CASCADE"), index=True)

    # Type de ligne (TRANSPORT ou FEE)
    item_type = Column(Enum(CustomerQuoteItemType), default=CustomerQuoteItemType.TRANSPORT)

    # Description (généré pour transport, saisi pour frais)
    description = Column(String)  # Ex: "Paris → Lyon" ou "Frais de dossier"

    # Référence au tarif source (NULL pour les frais)
    partner_quote_id = Column(String, ForeignKey("partner_quotes.id"), nullable=True)

    # Snapshot des données transport (NULL pour les frais)
    origin_city = Column(String, nullable=True)
    origin_country = Column(String, nullable=True)
    dest_city = Column(String, nullable=True)
    dest_country = Column(String, nullable=True)
    partner_name = Column(String, nullable=True)
    transport_mode = Column(String, nullable=True)
    delivery_time = Column(String, nullable=True)
    weight = Column(Numeric(10, 2), nullable=True)

    # Prix
    cost_price = Column(Numeric(10, 2), default=0)   # Prix d'achat (0 pour frais)
    sell_price = Column(Numeric(10, 2))              # Prix de vente
    margin_percent = Column(Numeric(5, 2))           # Marge en %
    margin_amount = Column(Numeric(10, 2))           # Marge en EUR

    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # Relations
    quote = relationship("CustomerQuote", back_populates="items")
    source_quote = relationship("PartnerQuote")
