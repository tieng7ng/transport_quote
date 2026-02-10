from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.auth import UserResponse, UserUpdate
from app.core import security

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
) -> Any:
    """
    Retrieve users.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: UUID,  # Changed to UUID type
    current_user: User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID, # Changed to UUID type
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
) -> Any:
    """
    Update a user.
    """
    if str(user_id) == str(current_user.id) and user_in.role and user_in.role != current_user.role:
        raise HTTPException(status_code=403, detail="Cannot change your own role")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Prevent privilege escalation
    if current_user.role != "SUPER_ADMIN":
        if user_in.role == "SUPER_ADMIN":
            raise HTTPException(status_code=403, detail="Cannot assign SUPER_ADMIN role")
        if user.role == "ADMIN" or user.role == "SUPER_ADMIN":
             # Non-SuperAdmin trying to modify Admin/SuperAdmin
             if user.id != current_user.id: # Allow modifying self (except role, checked above)
                 raise HTTPException(status_code=403, detail="Cannot modify other admins")
    
    if user_in.password:
        user.hashed_password = security.hash_password(user_in.password)
    if user_in.first_name:
        user.first_name = user_in.first_name
    if user_in.last_name:
        user.last_name = user_in.last_name
    if user_in.role:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
        
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
) -> Any:
    """
    Delete a user.
    """
    if str(user_id) == str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot delete yourself")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if current_user.role != "SUPER_ADMIN" and (user.role == "ADMIN" or user.role == "SUPER_ADMIN"):
         raise HTTPException(status_code=403, detail="Cannot delete other admins")
         
    db.delete(user)
    db.commit()
    return {"status": "success"}
