from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from redis import Redis

from app.core import security
from app.core.config import get_settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.user import User
from app.schemas.auth import TokenPayload

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_str}/auth/login" if hasattr(settings, "api_v1_str") else "/api/v1/auth/login"
)

async def get_authenticated_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_token(token)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type")
        
        if user_id is None or jti is None:
            raise credentials_exception
            
        # Ensure it is an access token
        if token_type == "refresh":
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Access token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        token_data = TokenPayload(**payload)
    except jwt.PyJWTError:
        raise credentials_exception

    # Vérifier blacklist Redis
    if redis.exists(f"blacklist:{jti}"):
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user

async def get_current_user(
    current_user: User = Depends(get_authenticated_user),
) -> User:
    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required",
            headers={"X-Require-Password-Change": "true"}
        )
    return current_user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user

def require_role(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles and current_user.role != "SUPER_ADMIN":
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role} not authorized. Required: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
