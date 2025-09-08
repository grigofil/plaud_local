from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.models.user import User
from src.utils.auth import verify_password, get_password_hash

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_all_users(db: Session) -> List[User]:
    """Get all users"""
    return db.query(User).all()

def create_user(
    db: Session, 
    username: str, 
    email: str, 
    password: str,
    is_active: bool = True,
    is_admin: bool = False
) -> User:
    """Create new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким именем или email уже существует"
        )
    
    # Hash password
    hashed_password = get_password_hash(password)
    
    # Create new user
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=is_active,
        is_admin=is_admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    return user

def update_user(
    db: Session, 
    user_id: int, 
    **kwargs
) -> Optional[User]:
    """Update user"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    """Delete user"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True

def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    """Deactivate user"""
    return update_user(db, user_id, is_active=False)

def activate_user(db: Session, user_id: int) -> Optional[User]:
    """Activate user"""
    return update_user(db, user_id, is_active=True)

def make_admin(db: Session, user_id: int) -> Optional[User]:
    """Make user admin"""
    return update_user(db, user_id, is_admin=True)

def remove_admin(db: Session, user_id: int) -> Optional[User]:
    """Remove admin privileges"""
    return update_user(db, user_id, is_admin=False)