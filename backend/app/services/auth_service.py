from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import UserCreate, LoginRequest
from app.core import security
from app.core.config import get_settings
from datetime import datetime, timezone
import uuid

settings = get_settings()

class AuthService:
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate):
        # Vérifier si l'email est autorisé
        domain = user_in.email.split("@")[-1]
        allowed_domains = [d.strip() for d in settings.allowed_email_domains.split(",")]
        if domain not in allowed_domains:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Domaine email non autorisé. Domaines permis : {', '.join(allowed_domains)}"
            )

        if AuthService.get_user_by_email(db, user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà utilisé."
            )

        db_user = User(
            email=user_in.email,
            hashed_password=security.hash_password(user_in.password),
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            role=user_in.role or "VIEWER",  # Par défaut VIEWER si non spécifié
            is_active=False,  # Inactif par défaut
            must_change_password=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, login_data: LoginRequest):
        user = AuthService.get_user_by_email(db, login_data.email)
        if not user:
            return None
        if not security.verify_password(login_data.password, user.hashed_password):
            return None
        return user

    @staticmethod
    def update_last_login(db: Session, user_id: uuid.UUID):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            db.commit()
