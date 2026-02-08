import os
import shutil
import math
from datetime import datetime
from typing import Optional, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.import_job import ImportJob, ImportStatus
from app.schemas.import_job import ImportJobCreate
from app.services.parsers.csv_parser import CsvParser
from app.services.parsers.excel_parser import ExcelParser
from app.services.parsers.pdf_parser import PdfParser

from app.services.import_logic.column_mapper import ColumnMapper
from app.services.import_logic.data_normalizer import DataNormalizer
from app.services.import_logic.row_validator import RowValidator
from app.services.quote_service import QuoteService
from app.schemas.partner_quote import PartnerQuoteCreate
from app.models.partner_quote import TransportMode
from app.services.partner_service import PartnerService

UPLOAD_DIR = "uploads"


def sanitize_for_json(obj: Any) -> Any:
    """
    Nettoie un objet pour le rendre compatible JSON.
    Convertit NaN, Infinity en None.
    """
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    return obj

class ImportService:
    @staticmethod
    def create_import_job(db: Session, partner_id: str, file: UploadFile) -> ImportJob:
        # 1. Créer le dossier d'upload si inexistant
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # 2. Sauvegarder le fichier
        timestamp = int(datetime.utcnow().timestamp())
        # Sanitize filename (remove path) and validate extension
        original_fname = os.path.basename(file.filename or "upload")
        _, file_ext = os.path.splitext(original_fname)
        file_ext = file_ext.lower()
        
        allowed_extensions = [".xlsx", ".xls", ".csv", ".pdf"]
        if file_ext not in allowed_extensions:
             raise ValueError(f"Extension {file_ext} not allowed.")

        safe_filename = f"{partner_id}_{timestamp}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 3. Créer le Job en base
        db_job = ImportJob(
            partner_id=partner_id,
            filename=safe_filename,
            file_type=file_ext.replace(".", "").upper(),
            status=ImportStatus.PENDING
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        return db_job

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[ImportJob]:
        """Récupérer un job d'import par ID."""
        return db.query(ImportJob).filter(ImportJob.id == job_id).first()

    @staticmethod
    def process_import(db: Session, job_id: str):
        """Traitement asynchrone (simulé ici en synchrone pour MVP)."""
        job = ImportService.get_job(db, job_id)
        if not job:
            return

        try:
            # Update status
            job.status = ImportStatus.PROCESSING
            db.commit()
            
            # Récupérer le code partenaire pour le mapping spécifique
            partner = PartnerService.get_by_id(db, job.partner_id)
            partner_code = partner.code if partner else None

            file_path = os.path.join(UPLOAD_DIR, job.filename)
            
            # Sélection parser
            parser = None
            if job.file_type in [".CSV", "CSV"]:
                parser = CsvParser()
            elif job.file_type in [".XLSX", "XLSX", ".XLS", "XLS"]:
                parser = ExcelParser()
            elif job.file_type in [".PDF", "PDF"]:
                parser = PdfParser()
            
            if not parser:
                raise ValueError(f"Format non supporté: {job.file_type}")

            # Instanciation des services logiques
            mapper = ColumnMapper()
            normalizer = DataNormalizer()
            validator = RowValidator()

            success_count = 0
            error_count = 0
            errors_list = []
            total_rows = 0

            print(f"[{datetime.utcnow()}] START Processing Job {job_id}")
            print(f"[{datetime.utcnow()}] Deleting old quotes...")

            # Suppression des anciens tarifs du partenaire avant import
            QuoteService.delete_all_by_partner(db, job.partner_id)

            print(f"[{datetime.utcnow()}] Old quotes deleted. Parsing file...")

            # --- VÉRIFICATION LAYOUT MULTI_SHEET ---
            if mapper.is_multi_sheet(partner_code):
                # Layout multi_sheet : traiter plusieurs feuilles
                sheets_config = mapper.get_sheets_config(partner_code)
                print(f"[{datetime.utcnow()}] Multi-sheet layout detected. Processing {len(sheets_config)} sheets...")

                for sheet_conf in sheets_config:
                    sheet_name = sheet_conf.get("sheet_name")
                    header_row = sheet_conf.get("header_row")
                    conf_name = sheet_conf.get("name", sheet_name)

                    print(f"[{datetime.utcnow()}] Processing sheet '{sheet_name}' (config: {conf_name})...")

                    # Parser cette feuille spécifique
                    sheet_parser_config = {
                        "sheet_name": sheet_name,
                        "header_row": header_row
                    }
                    raw_data = parser.parse(file_path, **sheet_parser_config)

                    print(f"[{datetime.utcnow()}] Sheet '{sheet_name}': {len(raw_data) if raw_data else 0} rows parsed.")

                    if not raw_data:
                        continue

                    total_rows += len(raw_data)

                    prev_weight_max = 0.0
                    for i, row in enumerate(raw_data):
                        row_num = i + 1
                        try:
                            # Mapping avec la config spécifique de la feuille, avec prev_weight_max
                            mapped_rows_list = mapper.map_row_with_sheet_config(row, sheet_conf, prev_weight_max)
                            
                            # Mise à jour du prev_weight_max pour la prochaine itération
                            # On cherche le weight_max le plus grand de la ligne courante
                            current_max = 0.0
                            for m_row in mapped_rows_list:
                                if "weight_max" in m_row and m_row["weight_max"] is not None:
                                    if m_row["weight_max"] > current_max:
                                        current_max = m_row["weight_max"]
                            
                            # Si on a trouvé un max valide, on met à jour.
                            # Attention : si la ligne ne contient pas de poids (ex: ligne vide ignorée), on garde l'ancien.
                            if current_max > 0:
                                prev_weight_max = current_max

                            for mapped_row in mapped_rows_list:
                                try:
                                    normalized_row = normalizer.normalize_row(mapped_row)
                                    validation = validator.validate(normalized_row)

                                    if validation.is_valid:
                                        quote_in = PartnerQuoteCreate(
                                            partner_id=job.partner_id,
                                            **validation.data
                                        )
                                        QuoteService.create_quote(db, quote_in)
                                        success_count += 1
                                    else:
                                        error_count += 1
                                        errors_list.append({
                                            "sheet": sheet_name,
                                            "row": row_num,
                                            "errors": [e.model_dump() for e in validation.errors],
                                            "raw": sanitize_for_json(row)
                                        })
                                except Exception as e_inner:
                                    error_count += 1
                                    errors_list.append({
                                        "sheet": sheet_name,
                                        "row": row_num,
                                        "error": f"Error processing sub-row: {str(e_inner)}",
                                        "raw": sanitize_for_json(row)
                                    })

                        except Exception as e:
                            error_count += 1
                            errors_list.append({
                                "sheet": sheet_name,
                                "row": row_num,
                                "error": str(e),
                                "raw": sanitize_for_json(row)
                            })

                    print(f"[{datetime.utcnow()}] Sheet '{sheet_name}' completed.")

            else:
                # --- PIPELINE STANDARD (une seule feuille) ---
                parser_config = mapper.get_parser_config(partner_code)
                raw_data = parser.parse(file_path, **parser_config)

                print(f"[{datetime.utcnow()}] Parsed {len(raw_data) if raw_data else 0} rows.")

                total_rows = len(raw_data) if raw_data else 0

                for i, row in enumerate(raw_data):
                    row_num = i + 1
                    try:
                        # 1. Mapping (peut retourner plusieurs lignes si matrice)
                        mapped_rows_list = mapper.map_row(row, partner_code)

                        for mapped_row in mapped_rows_list:
                            try:
                                # 2. Normalisation
                                normalized_row = normalizer.normalize_row(mapped_row)

                                # 3. Validation
                                validation = validator.validate(normalized_row)

                                if validation.is_valid:
                                    # 4. Sauvegarde (Via QuoteService pour réutiliser la logique)
                                    quote_in = PartnerQuoteCreate(
                                        partner_id=job.partner_id,
                                        **validation.data
                                    )
                                    QuoteService.create_quote(db, quote_in)
                                    success_count += 1
                                else:
                                    # Gestion Erreur Validation
                                    error_count += 1
                                    errors_list.append({
                                        "row": row_num,
                                        "errors": [e.model_dump() for e in validation.errors],
                                        "raw": sanitize_for_json(row)
                                    })
                            except Exception as e_inner:
                                 error_count += 1
                                 errors_list.append({
                                    "row": row_num,
                                    "error": f"Error processing sub-row: {str(e_inner)}",
                                    "raw": sanitize_for_json(row)
                                })

                    except Exception as e:
                        # Gestion Erreur Inattendue (System)
                        error_count += 1
                        errors_list.append({
                            "row": row_num,
                            "error": str(e),
                            "raw": sanitize_for_json(row)
                        })

            # Mise à jour du Job
            job.total_rows = total_rows
            job.success_count = success_count
            job.error_count = error_count
            job.errors = errors_list
            
            if error_count == 0:
                job.status = ImportStatus.COMPLETED
            elif success_count > 0:
                job.status = ImportStatus.COMPLETED # Ou PARTIAL si on veut distinguer
            else:
                job.status = ImportStatus.FAILED
            
        except Exception as e:
            job.status = ImportStatus.FAILED
            job.errors = {"error": str(e)}
            
        db.commit()
