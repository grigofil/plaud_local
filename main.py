import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Настройки авторизации
API_TOKENS = {t.strip() for t in os.getenv("API_AUTH_TOKEN", "").split(",") if t.strip()}

def require_auth(authorization: str = Header(default=None), x_api_key: str = Header(default=None)):
    """
    Функция авторизации - принимает либо Authorization: Bearer <token>, либо X-API-Key: <token>.
    Если переменная окружения API_AUTH_TOKEN не задана — авторизация выключена.
    """
    if not API_TOKENS:  # авторизация отключена
        return
    
    # Логируем попытку доступа
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 1) Authorization: Bearer ...
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token in API_TOKENS:
            logger.info(f"Successful Bearer auth for token: {token[:8]}...")
            return
        else:
            logger.warning(f"Invalid Bearer token: {token[:8]}...")
    
    # 2) X-API-Key header
    if x_api_key:
        if x_api_key in API_TOKENS:
            logger.info(f"Successful X-API-Key auth for token: {x_api_key[:8]}...")
            return
        else:
            logger.warning(f"Invalid X-API-Key token: {x_api_key[:8]}...")
    
    # Логируем неудачную попытку
    logger.error("Unauthorized access attempt")
    
    # иначе — 401 Unauthorized
    raise HTTPException(status_code=401, detail="Unauthorized")

app = FastAPI(title="Plaud Local - Main Application")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы
static_dir = Path(__file__).parent / "api" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def root(_auth=Depends(require_auth)):
    """Главная страница - требует авторизации"""
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
    """Проверка здоровья системы - требует авторизации"""
    return {
        "status": "healthy",
        "service": "plaud-local-main",
        "auth_required": bool(API_TOKENS)
    }

@app.get("/info")
async def info(_auth=Depends(require_auth)):
    """Информация о системе - требует авторизации"""
    return {
        "service": "Plaud Local",
        "version": "1.0.0",
        "auth_enabled": bool(API_TOKENS),
        "data_dir": os.getenv("DATA_DIR", "/data"),
        "redis_url": os.getenv("REDIS_URL", "redis://redis:6379")
    }

@app.get("/auth/check")
async def check_auth(_auth=Depends(require_auth)):
    """Проверка авторизации - возвращает информацию о текущем токене"""
    return {
        "status": "authenticated",
        "message": "Авторизация успешна",
        "auth_enabled": bool(API_TOKENS),
        "service": "plaud-local-main"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
