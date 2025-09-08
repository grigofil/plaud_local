import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.config.settings import API_AUTH_TOKENS
from src.api.dependencies import require_auth

app = FastAPI(title="Plaud Local - Main Application")

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
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def root(_auth=Depends(require_auth)):
    """Main page - requires authentication"""
    return {
        "message": "Добро пожаловать в Plaud Local!",
        "status": "authenticated",
        "endpoints": [
            "/api/upload - загрузка аудио",
            "/api/status/{job_id} - статус задачи",
            "/api/result/{job_id} - результат обработки"
        ]
    }

@app.get("/health")
async def health(_auth=Depends(require_auth)):
    """Health check - requires authentication"""
    return {
        "status": "healthy",
        "service": "plaud-local-main",
        "auth_required": bool(API_AUTH_TOKENS)
    }

@app.get("/info")
async def info(_auth=Depends(require_auth)):
    """System information - requires authentication"""
    return {
        "service": "Plaud Local",
        "version": "1.0.0",
        "auth_enabled": bool(API_AUTH_TOKENS),
        "data_dir": os.getenv("DATA_DIR", "/data"),
        "redis_url": os.getenv("REDIS_URL", "redis://redis:6379")
    }

@app.get("/auth/check")
async def check_auth(_auth=Depends(require_auth)):
    """Check authentication - returns information about current token"""
    return {
        "status": "authenticated",
        "message": "Авторизация успешна",
        "auth_enabled": bool(API_AUTH_TOKENS),
        "service": "plaud-local-main"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)