"""
Modèle Partner - Converti depuis Prisma schema.

Prisma original:
    model Partner {
      id          String   @id @default(uuid())
      code        String   @unique
      name        String
      email       String
      rating      Float    @default(0)
      isActive    Boolean  @default(true) @map("is_active")
      createdAt   DateTime @default(now()) @map("created_at")
      updatedAt   DateTime @updatedAt @map("updated_at")
      quotes      PartnerQuote[]
      importJobs  ImportJob[]
      @@map("partners")
    }
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Partner(Base):
    """Partenaire transporteur."""

    __tablename__ = "partners"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    rating = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    default_margin = Column(Float, default=20.0)  # Marge par défaut en %

    # Relations
    quotes = relationship("PartnerQuote", back_populates="partner", cascade="all, delete-orphan")
    import_jobs = relationship("ImportJob", back_populates="partner", cascade="all, delete-orphan")
