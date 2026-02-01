from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.partner import Partner
from app.schemas.partner import PartnerCreate, PartnerUpdate

class PartnerService:
    @staticmethod
    def get_by_id(db: Session, partner_id: str) -> Optional[Partner]:
        return db.query(Partner).filter(Partner.id == partner_id).first()

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Partner]:
        return db.query(Partner).filter(Partner.code == code).first()

    @staticmethod
    def list_partners(db: Session, skip: int = 0, limit: int = 100) -> List[Partner]:
        return db.query(Partner).offset(skip).limit(limit).all()

    @staticmethod
    def create_partner(db: Session, partner_in: PartnerCreate) -> Partner:
        db_partner = Partner(
            code=partner_in.code,
            name=partner_in.name,
            email=partner_in.email
        )
        db.add(db_partner)
        db.commit()
        db.refresh(db_partner)
        return db_partner

    @staticmethod
    def update_partner(db: Session, partner_id: str, partner_in: PartnerUpdate) -> Optional[Partner]:
        db_partner = PartnerService.get_by_id(db, partner_id)
        if not db_partner:
            return None
        
        update_data = partner_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_partner, field, value)
            
        db.add(db_partner)
        db.commit()
        db.refresh(db_partner)
        return db_partner

    @staticmethod
    def delete_partner(db: Session, partner_id: str) -> bool:
        db_partner = PartnerService.get_by_id(db, partner_id)
        if not db_partner:
            return False
            
        db.delete(db_partner)
        db.commit()
        return True
