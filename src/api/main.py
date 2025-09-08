import os
import uuid
import shutil
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from src.config.settings import DATA_DIR, LANG_DEFAULT
from src.utils.database import get_db, init_db
from src.utils.auth import create_access_token
from src.api.dependencies import require_auth, require_admin, get_current_user
from src.services.transcription_service import (
    jobs_dir, ensure_dirs, send_to_transcribe_server, 
    get_job_status, get_job_result, delete_job
)
from src.services.user_service import (
    create_user, authenticate_user, get_all_users,
    delete_user, deactivate_user, activate_user,
    make_admin, remove_admin
)
from src.models.user import User

app = FastAPI(title="Plaud Local API", version="1.0.0")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_dir = Path(__file__).parent.parent.parent / "api" / "static"
if static_dir.exists():
    app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="app")

# Health check endpoint
@app.get("/healthz")
async def health_check(_auth=Depends(require_auth)):
    return {"status": "ok"}

# Authentication endpoints
@app.post("/auth/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Register new user"""
    try:
        new_user = create_user(db, username, email, password)
        return {
            "message": "Пользователь успешно зарегистрирован",
            "user_id": new_user.id,
            "username": new_user.username
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/auth/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Authenticate user"""
    try:
        user = authenticate_user(db, username, password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Неверное имя пользователя или пароль"
            )
        
        access_token = create_access_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at
    }

@app.get("/auth/check")
async def check_auth(current_user: User = Depends(get_current_user)):
    """Check authentication"""
    return {
        "status": "authenticated",
        "message": "Авторизация успешна",
        "username": current_user.username,
        "auth_enabled": True
    }

# Transcription endpoints
@app.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    language: str = Query(LANG_DEFAULT),
    _auth=Depends(require_auth),
):
    """Upload audio file for transcription"""
    job_id = str(uuid.uuid4())
    jdir = jobs_dir(job_id)
    ensure_dirs(jdir)

    suffix = Path(file.filename).suffix or ".wav"
    audio_path = jdir / f"input{suffix}"

    with audio_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Save metadata
    meta = {"job_id": job_id, "filename": file.filename, "language": language}
    (jdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")

    # Send to transcription server
    success = await send_to_transcribe_server(job_id, str(audio_path), language)
    
    if success:
        return {"job_id": job_id, "status": "processing"}
    else:
        return JSONResponse(
            {"job_id": job_id, "status": "error", "error": "Failed to send to transcription server"}, 
            status_code=500
        )

@app.get("/status/{job_id}")
async def get_job_status_endpoint(job_id: str, _auth=Depends(require_auth)):
    """Get job status"""
    status = get_job_status(job_id)
    return {"job_id": job_id, **status}

@app.get("/result/{job_id}")
async def get_job_result_endpoint(job_id: str, _auth=Depends(require_auth)):
    """Get job result"""
    try:
        result = get_job_result(job_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")

@app.get("/history")
async def get_job_history(_auth=Depends(require_auth)):
    """Get job history"""
    jobs_dir_path = DATA_DIR / "jobs"
    if not jobs_dir_path.exists():
        return {"jobs": []}
    
    jobs = []
    for job_dir in jobs_dir_path.iterdir():
        if not job_dir.is_dir():
            continue
            
        job_id = job_dir.name
        meta_file = job_dir / "meta.json"
        transcript_file = job_dir / "transcript.json"
        summary_file = job_dir / "summary.json"
        
        job_info = {"job_id": job_id, "status": "unknown"}
        
        # Determine status
        if summary_file.exists():
            job_info["status"] = "done"
        elif transcript_file.exists():
            job_info["status"] = "transcribed_waiting_summary"
        else:
            job_info["status"] = "processing"
        
        # Load metadata
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text("utf-8"))
                job_info.update(meta)
            except:
                job_info["filename"] = "unknown"
                job_info["language"] = "unknown"
        
        jobs.append(job_info)
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x.get("created_at", 0) or 0, reverse=True)
    return {"jobs": jobs}

@app.delete("/history/{job_id}")
async def delete_job_endpoint(job_id: str, _auth=Depends(require_auth)):
    """Delete job"""
    success = delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}

# User management endpoints (admin only)
@app.get("/users")
async def list_users(admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """List all users (admin only)"""
    users = get_all_users(db)
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at
            }
            for user in users
        ]
    }

@app.delete("/users/{user_id}")
async def delete_user_endpoint(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Delete user (admin only)"""
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@app.patch("/users/{user_id}/deactivate")
async def deactivate_user_endpoint(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Deactivate user (admin only)"""
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    user = deactivate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deactivated", "user_id": user.id, "username": user.username}

@app.patch("/users/{user_id}/activate")
async def activate_user_endpoint(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Activate user (admin only)"""
    user = activate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User activated", "user_id": user.id, "username": user.username}

@app.patch("/users/{user_id}/make-admin")
async def make_admin_endpoint(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Make user admin (admin only)"""
    user = make_admin(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User made admin", "user_id": user.id, "username": user.username}

@app.patch("/users/{user_id}/remove-admin")
async def remove_admin_endpoint(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Remove admin privileges (admin only)"""
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove admin privileges from yourself")
    
    user = remove_admin(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Admin privileges removed", "user_id": user.id, "username": user.username}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)