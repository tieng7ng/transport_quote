"""
Modèle GeneratedQuote - Converti depuis Prisma schema.

Prisma original:
    model GeneratedQuote {
      id              String      @id @default(uuid())
      quoteNumber     String      @unique @map("quote_number")
      customerId      String      @map("customer_id")
      status          QuoteStatus @default(DRAFT)
      items           Json
      totalAmount     Decimal     @db.Decimal(10, 2) @map("total_amount")
      currency        String      @default("EUR")
      pdfUrl          String?     @map("pdf_url")
      validUntil      DateTime    @map("valid_until")
      sentAt          DateTime?   @map("sent_at")
      viewedAt        DateTime?   @map("viewed_at")
      acceptedAt      DateTime?   @map("accepted_at")
      rejectedAt      DateTime?   @map("rejected_at")
      metadata        Json?
      createdAt       DateTime    @default(now()) @map("created_at")
      updatedAt       DateTime    @updatedAt @map("updated_at")
      customer        Customer    @relation(...)
      @@index([status])
      @@index([customerId])
      @@map("generated_quotes")
    }

    enum QuoteStatus { DRAFT, PENDING, SENT, VIEWED, ACCEPTED, REJECTED, EXPIRED }
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Numeric, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class QuoteStatus(str, PyEnum):
    """Statuts possibles d'un devis généré."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    SENT = "SENT"
    VIEWED = "VIEWED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class GeneratedQuote(Base):
    """Devis généré pour un client."""

    __tablename__ = "generated_quotes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_number = Column(String, unique=True, nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT)

    # Détails
    items = Column(JSON, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="EUR")

    # Fichiers
    pdf_url = Column(String, nullable=True)

    # Validité
    valid_until = Column(DateTime, nullable=False)

    # Tracking
    sent_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)

    # Metadata
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    customer = relationship("Customer", back_populates="quotes")

    __table_args__ = (
        Index("ix_generated_quotes_status", "status"),
        Index("ix_generated_quotes_customer_id", "customer_id"),
    )
