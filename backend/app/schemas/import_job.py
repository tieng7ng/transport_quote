from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel
from app.models.import_job import ImportStatus

class ImportJobBase(BaseModel):
    partner_id: str
    filename: str
    file_type: str

class ImportJobCreate(ImportJobBase):
    pass

class ImportJobResponse(ImportJobBase):
    id: str
    status: ImportStatus
    total_rows: int
    success_count: int
    error_count: int
    errors: Optional[Any] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
