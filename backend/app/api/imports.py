from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.import_job import ImportJobResponse
from app.services.import_service import ImportService
from app.services.partner_service import PartnerService

router = APIRouter()

@router.post("/", response_model=ImportJobResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    background_tasks: BackgroundTasks,
    partner_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploader un fichier de tarifs pour un partenaire.
    Crée un Job d'import en statut PENDING.
    """
    # Vérifier que le partenaire existe
    partner = PartnerService.get_by_id(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")
        
    job = ImportService.create_import_job(db, partner_id, file)
    
    # Lancer le traitement asynchrone (MVP: via BackgroundTasks)
    background_tasks.add_task(ImportService.process_import, db, job.id)
    
    return job

@router.get("/{job_id}", response_model=ImportJobResponse)
def get_import_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Récupérer le statut d'un job d'import."""
    job = ImportService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return job
