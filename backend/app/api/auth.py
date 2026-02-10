from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_redis, oauth2_scheme
from app.schemas.auth import LoginRequest, Token, UserResponse, UserCreate, RefreshRequest
from app.services.auth_service import AuthService
from app.models.user import User
from redis import Redis

settings = get_settings()
router = APIRouter()

from app.core.rate_limit import limiter

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login_access_token(
    request: Request,
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = AuthService.authenticate_user(
        db, LoginRequest(email=form_data.username, password=form_data.password)
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    
    # Update last login
    AuthService.update_last_login(db, user.id)

    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "refresh_token": security.create_refresh_token(user.id),
    }

@router.post("/refresh", response_model=Token)
def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Any:
    """
    Refresh access token
    """
    refresh_token = request.refresh_token
    try:
        payload = security.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        if redis.exists(f"blacklist:{jti}"):
            raise HTTPException(status_code=401, detail="Token revoked")
            
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        
        return {
            "access_token": security.create_access_token(
                user.id, expires_delta=access_token_expires
            ),
            "token_type": "bearer",
            "refresh_token": refresh_token, # Reuse same refresh token or rotate? Simple reuse for now.
        }
    except Exception:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis)
) -> Any:
    """
    Logout (blacklist token)
    """
    payload = security.decode_token(token)
    jti = payload.get("jti")
    exp = payload.get("exp") # Expiration timestamp
    
    # Calculate TTL
    ttl = exp - datetime.utcnow().timestamp()
    if ttl > 0:
        redis.setex(f"blacklist:{jti}", int(ttl), "revoked")
        
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user (Viewer by default).
    """
    # Force Viewer role for self-registration
    user_in.role = "VIEWER" 
    user = AuthService.create_user(db, user_in)
    return user

from app.schemas.auth import PasswordChangeRequest
from app.core.deps import get_authenticated_user

@router.post("/change-password")
def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Change password. Required if must_change_password is True.
    """
    if not security.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    current_user.hashed_password = security.hash_password(password_data.new_password)
    current_user.must_change_password = False
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Password updated successfully"}
