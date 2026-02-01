"""
Modèle PartnerQuote - Converti depuis Prisma schema.

Prisma original:
    model PartnerQuote {
      id              String   @id @default(uuid())
      partnerId       String   @map("partner_id")
      transportMode   TransportMode @map("transport_mode")
      originPostalCode  String?  @map("origin_postal_code")
      originCity        String   @map("origin_city")
      originCountry     String   @map("origin_country")
      destPostalCode    String?  @map("dest_postal_code")
      destCity          String   @map("dest_city")
      destCountry       String   @map("dest_country")
      weightMin       Float?   @map("weight_min")
      weightMax       Float?   @map("weight_max")
      volumeMin       Float?   @map("volume_min")
      volumeMax       Float?   @map("volume_max")
      cost            Decimal  @db.Decimal(10, 2)
      currency        String   @default("EUR")
      deliveryTime    String?  @map("delivery_time")
      validFrom       DateTime @default(now()) @map("valid_from")
      validUntil      DateTime? @map("valid_until")
      isActive        Boolean  @default(true) @map("is_active")
      importJobId     String?  @map("import_job_id")
      metadata        Json?
      createdAt       DateTime @default(now()) @map("created_at")
      updatedAt       DateTime @updatedAt @map("updated_at")
      partner         Partner  @relation(...)
      importJob       ImportJob? @relation(...)
      @@index([originCountry, destCountry])
      @@index([transportMode])
      @@index([isActive, validUntil])
      @@map("partner_quotes")
    }

    enum TransportMode { ROAD, RAIL, SEA, AIR, MULTIMODAL }
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Float, Boolean, DateTime, Numeric, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class TransportMode(str, PyEnum):
    """Modes de transport disponibles."""
    ROAD = "ROAD"
    RAIL = "RAIL"
    SEA = "SEA"
    AIR = "AIR"
    MULTIMODAL = "MULTIMODAL"


class PartnerQuote(Base):
    """Tarif partenaire importé."""

    __tablename__ = "partner_quotes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, ForeignKey("partners.id"), nullable=False)
    transport_mode = Column(Enum(TransportMode), nullable=False)

    # Origine
    origin_postal_code = Column(String(2), nullable=True)
    origin_city = Column(String, nullable=False)
    origin_country = Column(String, nullable=False)

    # Destination
    dest_postal_code = Column(String, nullable=True)
    dest_city = Column(String, nullable=False)
    dest_country = Column(String, nullable=False)

    # Critères
    weight_min = Column(Float, nullable=True)
    weight_max = Column(Float, nullable=True)
    volume_min = Column(Float, nullable=True)
    volume_max = Column(Float, nullable=True)

    # Tarif
    cost = Column(Numeric(10, 2), nullable=False)
    pricing_type = Column(String, default="PER_100KG")  # PER_100KG, LUMPSUM, PER_KG, PER_PALLET
    currency = Column(String, default="EUR")
    delivery_time = Column(String, nullable=True)

    # Validité & Admin
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    import_job_id = Column(String, ForeignKey("import_jobs.id"), nullable=True)

    # Metadata
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    partner = relationship("Partner", back_populates="quotes")
    import_job = relationship("ImportJob", back_populates="quotes")

    __table_args__ = (
        Index("ix_partner_quotes_origin_dest", "origin_country", "dest_country"),
        Index("ix_partner_quotes_transport_mode", "transport_mode"),
        Index("ix_partner_quotes_active_valid", "is_active", "valid_until"),
    )
