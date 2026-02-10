
from sqlalchemy.orm import Session
from app.models.user import User
from app.core import security
import uuid

def create_test_user(db: Session, email: str, role: str = "VIEWER") -> User:
    password = "Password123!"
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    
    user = User(
        email=email,
        hashed_password=security.hash_password(password),
        first_name="Test",
        last_name="User",
        role=role,
        is_active=True,
        must_change_password=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
