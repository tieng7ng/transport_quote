from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import UserResponse, UserUpdate, UserCreate
from app.services.auth_service import AuthService
from app.services.activity_service import log_activity
from app.core import security

router = APIRouter()

# Tous les endpoints nécessitent le rôle SUPER_ADMIN ou ADMIN
router.dependencies.append(Depends(require_role("SUPER_ADMIN", "ADMIN")))

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve users."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new user."""
    if user_in.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only SUPER_ADMIN can create another SUPER_ADMIN user"
        )
    user = AuthService.create_user(db, user_in)
    log_activity(db, "user.created", user=current_user, resource="user",
                 resource_id=user.id,
                 details={"login": user.login, "role": user.role.value},
                 request=request)
    db.commit()
    return user

@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """Get a specific user by id."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify a SUPER_ADMIN user")

    if hasattr(user_in, 'login') and user_in.login and user_in.login != user.login:
       raise HTTPException(status_code=400, detail="Login cannot be modified")

    if user_in.password:
        user.hashed_password = security.hash_password(user_in.password)
    if user_in.first_name:
        user.first_name = user_in.first_name
    if user_in.last_name:
        user.last_name = user_in.last_name

    if user_in.role:
        if user_id == current_user.id and user_in.role != UserRole.SUPER_ADMIN and current_user.role == UserRole.SUPER_ADMIN:
            pass
        if user_in.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Only SUPER_ADMIN can promote users to SUPER_ADMIN")
        user.role = user_in.role

    if user_in.is_active is not None:
        if user_id == current_user.id and user_in.is_active is False:
            raise HTTPException(status_code=403, detail="Cannot deactivate yourself.")
        user.is_active = user_in.is_active

    log_activity(db, "user.updated", user=current_user, resource="user",
                 resource_id=str(user_id),
                 details={"login": user.login},
                 request=request)
    db.commit()
    db.refresh(user)
    return user

@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: UUID,
    is_active: bool = Body(..., embed=True),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Activate/Deactivate a user (Soft Delete)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot change your own status")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify status of a SUPER_ADMIN user")

    action = "user.deactivated" if not is_active else "user.updated"
    user.is_active = is_active
    log_activity(db, action, user=current_user, resource="user",
                 resource_id=str(user_id),
                 details={"login": user.login, "is_active": is_active},
                 request=request)
    db.commit()
    db.refresh(user)
    return user

@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: UUID,
    role: UserRole = Body(..., embed=True),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Change user role."""
    if user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot change your own role")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify role of a SUPER_ADMIN user")

    if role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only SUPER_ADMIN can promote users to SUPER_ADMIN")

    old_role = user.role.value
    user.role = role
    log_activity(db, "user.updated", user=current_user, resource="user",
                 resource_id=str(user_id),
                 details={"login": user.login, "old_role": old_role, "new_role": role.value},
                 request=request)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Delete a user (Soft Delete)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete a SUPER_ADMIN user")

    log_activity(db, "user.deactivated", user=current_user, resource="user",
                 resource_id=str(user_id),
                 details={"login": user.login, "role": user.role.value},
                 request=request)
    # Soft delete
    user.is_active = False
    db.commit()

    return {"status": "success", "message": "User deactivated (soft delete)"}
