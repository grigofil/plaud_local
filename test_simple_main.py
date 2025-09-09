#!/usr/bin/env python3
"""
Простой тестовый main.py без Redis
"""

import os, uuid, shutil, json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends, Header, Form
from fastapi.responses import JSONResponse
import httpx
from typing import Optional

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import secrets
from sqlalchemy.orm import Session

# Import our modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "api"))

from database import get_db, init_db
from models import User
from auth import verify_password, get_password_hash, create_access_token, decode_access_token

DATA_DIR  = Path(os.getenv("DATA_DIR", "/data"))
LANG_DEFAULT = "ru"

app = FastAPI(title="Plaud API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

def require_auth(authorization: str = Header(default=None), db: Session = Depends(get_db)):
    """
    Проверяет JWT токен в заголовке Authorization: Bearer <token>.
    Токен должен быть валидным JWT токеном с информацией о пользователе.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.split(" ", 1)[1].strip()
    
    # Проверяем JWT токен
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if user and user.is_active:
            return
        else:
            pass
    
    # иначе — 401
    raise HTTPException(status_code=401, detail="Unauthorized")

def require_admin(authorization: str = Header(default=None), db: Session = Depends(get_db)):
    """
    Проверяет JWT токен в заголовке Authorization: Bearer <token>.
    Токен должен быть валидным JWT токеном с информацией о пользователе.
    Пользователь должен быть администратором.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.split(" ", 1)[1].strip()
    
    # Проверяем JWT токен
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if user and user.is_active and user.is_admin:
            return
        else:
            pass
    
    # иначе — 401
    raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/healthz")
def health_check(authorization: str = Header(default=None), db: Session = Depends(get_db)):
    """Health check endpoint"""
    require_auth(authorization, db)
    return {"status": "ok"}

@app.post("/auth/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Аутентификация пользователя"""
    try:
        print(f"Login attempt: username={username}")
        
        user = db.query(User).filter(User.username == username).first()
        print(f"User found: {user is not None}")
        
        if not user:
            print("User not found")
            raise HTTPException(
                status_code=401,
                detail="Неверное имя пользователя или пароль"
            )
        
        print(f"User active: {user.is_active}")
        print(f"User is_admin: {getattr(user, 'is_admin', 'NO FIELD')}")
        
        if not verify_password(password, user.hashed_password):
            print("Password verification failed")
            raise HTTPException(
                status_code=401,
                detail="Неверное имя пользователя или пароль"
            )
        
        if not user.is_active:
            print("User not active")
            raise HTTPException(
                status_code=400,
                detail="Пользователь заблокирован"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username})
        print(f"Token created: {access_token[:20]}...")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/auth/me")
def get_current_user(authorization: str = Header(default=None), db: Session = Depends(get_db)):
    """Получить информацию о текущем пользователе"""
    require_auth(authorization, db)
    
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_admin": user.is_admin
    }

# Mount static files
app.mount("/app", StaticFiles(directory="api/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
