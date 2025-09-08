from typing import Optional
from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session

from src.config.settings import API_AUTH_TOKENS
from src.utils.auth import decode_access_token
from src.utils.database import get_db
from src.models.user import User
from src.services.user_service import get_user_by_username

def require_auth(
    authorization: Optional[str] = Header(default=None), 
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    Authentication dependency - accepts either Authorization: Bearer <token> or X-API-Key: <token>.
    If API_AUTH_TOKENS is empty - authentication is disabled.
    """
    if not API_AUTH_TOKENS:  # authentication disabled
        return
    
    # 1) Authorization: Bearer ... (JWT token)
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            username = payload.get("sub")
            user = get_user_by_username(db, username)
            if user and user.is_active:
                return user
    
    # 2) X-API-Key header (static token)
    if x_api_key and x_api_key in API_AUTH_TOKENS:
        return
    
    # Log failed attempt
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error("Unauthorized access attempt")
    
    raise HTTPException(status_code=401, detail="Unauthorized")

def require_admin(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    Admin authentication dependency - requires valid JWT token with admin privileges
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    
    if payload and "sub" in payload:
        username = payload.get("sub")
        user = get_user_by_username(db, username)
        if user and user.is_active and user.is_admin:
            return user
    
    raise HTTPException(status_code=403, detail="Admin access required")

def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    
    if payload and "sub" in payload:
        username = payload.get("sub")
        user = get_user_by_username(db, username)
        if user and user.is_active:
            return user
    
    raise HTTPException(status_code=401, detail="Invalid token")