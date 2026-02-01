"""
Modèle Customer - Converti depuis Prisma schema.

Prisma original:
    model Customer {
      id          String   @id @default(uuid())
      email       String   @unique
      company     String?
      firstName   String?  @map("first_name")
      lastName    String?  @map("last_name")
      phone       String?
      createdAt   DateTime @default(now()) @map("created_at")
      updatedAt   DateTime @updatedAt @map("updated_at")
      quotes      GeneratedQuote[]
      @@map("customers")
    }
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Customer(Base):
    """Client destinataire des devis."""

    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    company = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    quotes = relationship("GeneratedQuote", back_populates="customer", cascade="all, delete-orphan")
