#!/usr/bin/env python3
"""
Тестовый main.py для проверки
"""

import os, uuid, shutil, json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Header, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# Import our modules
from database import get_db, init_db
from models import User
from auth import verify_password, get_password_hash, create_access_token, decode_access_token

app = FastAPI(title="Test API")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test")
def test():
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
