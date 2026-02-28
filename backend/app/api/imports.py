from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.import_job import ImportJobResponse
from app.services.import_service import ImportService
from app.services.partner_service import PartnerService
from app.services.activity_service import log_activity

router = APIRouter()

@router.post("/", response_model=ImportJobResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    background_tasks: BackgroundTasks,
    request: Request,
    partner_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN"))
):
    """
    Uploader un fichier de tarifs pour un partenaire (SUPER_ADMIN).
    Crée un Job d'import en statut PENDING.
    """
    partner = PartnerService.get_by_id(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")

    filename = file.filename or ""
    ext = filename.split(".")[-1].lower()
    allowed_exts = ["xlsx", "xls", "csv"]
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Extension non supportée. Allowed: {allowed_exts}")

    allowed_mimes = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
        "application/csv"
    ]
    if file.content_type not in allowed_mimes and "excel" not in file.content_type and "csv" not in file.content_type:
         print(f"Warning: Unusual MIME type {file.content_type} for {filename}")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    max_size = 50 * 1024 * 1024
    if size > max_size:
        raise HTTPException(status_code=413, detail=f"Fichier trop volumineux. Max {max_size//(1024*1024)}MB")

    job = ImportService.create_import_job(db, partner_id, file)

    log_activity(db, "import.started", user=current_user, resource="import_job",
                 resource_id=job.id,
                 details={"filename": filename, "partner": partner.name, "size_bytes": size},
                 request=request)
    db.commit()

    background_tasks.add_task(ImportService.process_import, db, job.id)

    return job

@router.get("/{job_id}", response_model=ImportJobResponse)
def get_import_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN"))
):
    """Récupérer le statut d'un job d'import (ADMIN, OPERATOR)."""
    job = ImportService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return job
