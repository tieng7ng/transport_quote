"""
Modèle ImportJob - Converti depuis Prisma schema.

Prisma original:
    model ImportJob {
      id           String       @id @default(uuid())
      partnerId    String       @map("partner_id")
      filename     String
      fileType     String       @map("file_type")
      status       ImportStatus @default(PENDING)
      totalRows    Int          @default(0) @map("total_rows")
      successCount Int          @default(0) @map("success_count")
      errorCount   Int          @default(0) @map("error_count")
      errors       Json?
      createdAt    DateTime     @default(now()) @map("created_at")
      completedAt  DateTime?    @map("completed_at")
      partner      Partner      @relation(...)
      quotes       PartnerQuote[]
      @@map("import_jobs")
    }

    enum ImportStatus { PENDING, PROCESSING, COMPLETED, FAILED }
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class ImportStatus(str, PyEnum):
    """Statuts possibles d'un job d'import."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ImportJob(Base):
    """Job d'import de fichier."""

    __tablename__ = "import_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, ForeignKey("partners.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # CSV, EXCEL, PDF
    status = Column(Enum(ImportStatus), default=ImportStatus.PENDING)

    total_rows = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relations
    partner = relationship("Partner", back_populates="import_jobs")
    quotes = relationship("PartnerQuote", back_populates="import_job")
