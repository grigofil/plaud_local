import os, uuid, shutil, json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends, Header, Form
from fastapi.responses import JSONResponse
from redis import Redis
from rq import Queue
import httpx
from typing import Optional

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import secrets
from sqlalchemy.orm import Session

# Import our modules
from database import get_db, init_db
from models import User
from auth import verify_password, get_password_hash, create_access_token, decode_access_token

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DATA_DIR  = Path(os.getenv("DATA_DIR", "/data"))
LANG_DEFAULT = "ru"
TRANSCRIBE_SERVER_URL = os.getenv("TRANSCRIBE_SERVER_URL", "http://worker_transcribe:8002")

def require_auth(authorization: str = Header(default=None), db: Session = Depends(get_db)):
    """
    Проверяет JWT токен в заголовке Authorization: Bearer <token>.
    Токен должен быть валидным JWT токеном с информацией о пользователе.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Логируем попытку доступа
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    token = authorization.split(" ", 1)[1].strip()
    
    # Проверяем JWT токен
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if user and user.is_active:
            logger.info(f"Successful JWT auth for user: {username}")
            return user
        else:
            logger.warning(f"Invalid JWT token for user: {username}")
    else:
        logger.warning(f"Invalid JWT token: {token[:8]}...")
    
    # Логируем неудачную попытку
    logger.error("Unauthorized access attempt")
    
    # иначе — 401
    raise HTTPException(status_code=401, detail="Unauthorized")

def require_admin(authorization: str = Header(default=None), db: Session = Depends(get_db)):
    """
    Проверяет JWT токен и права администратора.
    Возвращает объект пользователя-администратора.
    """
    # require_auth уже проверяет авторизацию и возвращает пользователя или выбрасывает исключение
    user = require_auth(authorization, db)
    
    # Если мы дошли до этой точки, значит пользователь авторизован
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user


app = FastAPI(title="Whisper+DeepSeek API (variant B)")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # при желании укажи свои origin’ы
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# раздаём статические файлы с веб-клиентом
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/app", StaticFiles(directory=static_dir, html=True), name="app")

def jobs_dir(job_id: str) -> Path:
    return DATA_DIR / "jobs" / job_id

def ensure_dirs(p: Path):
    p.mkdir(parents=True, exist_ok=True)

async def send_to_transcribe_server(job_id: str, audio_path: str, language: str):
    """Отправляет аудиофайл в сервер транскрибации через HTTP"""
    try:
        # Открываем файл для отправки
        with open(audio_path, "rb") as audio_file:
            files = {"file": audio_file}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{TRANSCRIBE_SERVER_URL}/transcribe?job_id={job_id}&language={language}",
                    files=files,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    print(f"Файл успешно отправлен в сервер транскрибации для job_id: {job_id}")
                    return True
                else:
                    print(f"Ошибка отправки в сервер транскрибации: {response.status_code} - {response.text}")
                    return False
                    
    except Exception as e:
        print(f"Ошибка при отправке в сервер транскрибации: {e}")
        return False

def enqueue_asr(job_id: str, audio_path: str, language: str):
    """Устаревшая функция - теперь используем HTTP сервер"""
    print(f"enqueue_asr устарел, используем HTTP сервер для job_id: {job_id}")
    # Оставляем для совместимости, но не используем
    pass

@app.get("/healthz")
def healthz(_auth=Depends(require_auth)):
    return {"status": "ok"}

# New authentication endpoints
@app.post("/auth/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Регистрация нового пользователя"""
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
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "Пользователь успешно зарегистрирован",
        "user_id": new_user.id,
        "username": new_user.username
    }

@app.post("/auth/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Аутентификация пользователя"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Пользователь заблокирован"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }

@app.post("/auth/refresh")
async def refresh_token(
    username: str = Form(...),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Обновление JWT токена"""
    # Проверяем текущий токен
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Проверяем, что username совпадает с токеном
    token_username = payload.get("sub")
    if token_username != username:
        raise HTTPException(status_code=401, detail="Username mismatch")
    
    # Проверяем существование пользователя
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Создаем новый токен
    new_access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }

@app.get("/auth/me")
async def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Получение информации о текущем пользователе"""
    # Проверяем JWT токен
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if user and user.is_active:
            return {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at
            }
    
    raise HTTPException(status_code=401, detail="Не удалось получить информацию о пользователе")

@app.get("/auth/check")
def check_auth(authorization: str = Header(...)):
    """Проверка авторизации - возвращает информацию о текущем токене"""
    # Проверяем JWT токен
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        username = payload.get("sub")
        return {
            "status": "authenticated",
            "message": "Авторизация успешна",
            "username": username,
            "auth_enabled": True
        }
    
    raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/stats")
def get_stats(_auth=Depends(require_auth)):
    """Получение статистики обработки"""
    import os
    from pathlib import Path
    
    jobs_dir = DATA_DIR / "jobs"
    if not jobs_dir.exists():
        return {"total_jobs": 0, "completed_jobs": 0, "processing_jobs": 0}
    
    total_jobs = 0
    completed_jobs = 0
    processing_jobs = 0
    
    for job_dir in jobs_dir.iterdir():
        if job_dir.is_dir():
            total_jobs += 1
            if (job_dir / "summary.json").exists():
                completed_jobs += 1
            elif (job_dir / "transcript.json").exists():
                processing_jobs += 1
    
    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "processing_jobs": processing_jobs,
        "queued_jobs": total_jobs - completed_jobs - processing_jobs
    }

@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    language: str = Query(LANG_DEFAULT),
    _auth=Depends(require_auth),                   # 🔐 защита
):
    job_id = str(uuid.uuid4())
    jdir = jobs_dir(job_id)
    ensure_dirs(jdir)

    suffix = Path(file.filename).suffix or ".wav"
    audio_path = jdir / f"input{suffix}"

    with audio_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Помечаем метаданные
    meta = {"job_id": job_id, "filename": file.filename, "language": language}
    (jdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")

    # Отправляем файл в сервер транскрибации
    success = await send_to_transcribe_server(job_id, str(audio_path), language)
    
    if success:
        return {"job_id": job_id, "status": "processing"}
    else:
        # Если не удалось отправить в сервер транскрибации, возвращаем ошибку
        return JSONResponse(
            {"job_id": job_id, "status": "error", "error": "Failed to send to transcription server"}, 
            status_code=500
        )

@app.get("/status/{job_id}")
async def status(job_id: str, _auth=Depends(require_auth)): 
    jdir = jobs_dir(job_id)
    if not jdir.exists():
        raise HTTPException(404, "job not found")

    transcript = jdir / "transcript.json"
    summary    = jdir / "summary.json"
    
    # Если есть готовый результат, возвращаем его
    if summary.exists():
        return {"job_id": job_id, "status": "done"}
    if transcript.exists():
        return {"job_id": job_id, "status": "transcribed_waiting_summary"}
    
    # Если нет готового результата, проверяем статус в сервере транскрибации
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TRANSCRIBE_SERVER_URL}/status/{job_id}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                server_status = response.json()
                return {
                    "job_id": job_id,
                    "status": server_status.get("status", "processing"),
                    "server_status": server_status
                }
    except Exception as e:
        print(f"Ошибка при проверке статуса в сервере транскрибации: {e}")
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/result/{job_id}")
def result(job_id: str, _auth=Depends(require_auth)): 
    jdir = jobs_dir(job_id)
    if not jdir.exists():
        raise HTTPException(404, "job not found")
    
    transcript = jdir / "transcript.json"
    summary = jdir / "summary.json"
    
    # Проверяем, что транскрипт готов
    if not transcript.exists():
        return JSONResponse({"error": "transcript_not_ready"}, status_code=202)
    
    out = {"job_id": job_id}
    
    # Загружаем транскрипт
    try:
        out["transcript"] = json.loads(transcript.read_text("utf-8"))
    except Exception as e:
        return JSONResponse({"error": f"transcript_read_error: {str(e)}"}, status_code=500)
    
    # Загружаем саммари, если оно готово
    if summary.exists():
        try:
            summary_data = json.loads(summary.read_text("utf-8"))
            out["summary"] = summary_data
        except Exception as e:
            # Если саммари повреждено, возвращаем только транскрипт
            out["summary_error"] = f"summary_read_error: {str(e)}"
    
    return out

@app.get("/history")
def get_history(_auth=Depends(require_auth)):
    """Получение истории всех задач с их статусами и результатами"""
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
        
        job_info = {
            "job_id": job_id,
            "status": "unknown"
        }
        
        # Определяем статус
        if summary_file.exists():
            job_info["status"] = "done"
        elif transcript_file.exists():
            job_info["status"] = "transcribed_waiting_summary"
        else:
            job_info["status"] = "processing"
        
        # Загружаем метаданные
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text("utf-8"))
                job_info.update(meta)
            except:
                job_info["filename"] = "unknown"
                job_info["language"] = "unknown"
        
        # Добавляем информацию о файлах
        job_info["has_transcript"] = transcript_file.exists()
        job_info["has_summary"] = summary_file.exists()
        
        # Добавляем размеры файлов
        if transcript_file.exists():
            job_info["transcript_size"] = transcript_file.stat().st_size
        if summary_file.exists():
            job_info["summary_size"] = summary_file.stat().st_size
        
        # Добавляем время создания (из имени папки или метаданных)
        try:
            # Пытаемся извлечь время из UUID
            import time
            timestamp = int(job_id.split('-')[0], 16) / 10000000 - 11644473600
            job_info["created_at"] = timestamp
        except:
            job_info["created_at"] = None
        
        jobs.append(job_info)
    
    # Сортируем по времени создания (новые сначала)
    jobs.sort(key=lambda x: x.get("created_at", 0) or 0, reverse=True)
    
    return {"jobs": jobs}

@app.get("/history/{job_id}")
def get_job_history(job_id: str, _auth=Depends(require_auth)):
    """Получение детальной информации о конкретной задаче"""
    jdir = jobs_dir(job_id)
    if not jdir.exists():
        raise HTTPException(404, "job not found")
    
    job_info = {"job_id": job_id}
    
    # Загружаем метаданные
    meta_file = jdir / "meta.json"
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text("utf-8"))
            job_info.update(meta)
        except:
            pass
    
    # Загружаем транскрипт
    transcript_file = jdir / "transcript.json"
    if transcript_file.exists():
        try:
            transcript = json.loads(transcript_file.read_text("utf-8"))
            job_info["transcript"] = transcript
        except:
            job_info["transcript_error"] = "Failed to read transcript"
    
    # Загружаем саммари
    summary_file = jdir / "summary.json"
    if summary_file.exists():
        try:
            summary = json.loads(summary_file.read_text("utf-8"))
            job_info["summary"] = summary
        except:
            job_info["summary_error"] = "Failed to read summary"
    
    # Определяем статус
    if summary_file.exists():
        job_info["status"] = "done"
    elif transcript_file.exists():
        job_info["status"] = "transcribed_waiting_summary"
    else:
        job_info["status"] = "processing"
    
    return job_info

@app.delete("/history/{job_id}")
def delete_job(job_id: str, _auth=Depends(require_auth)):
    """Удаление задачи и всех связанных файлов"""
    jdir = jobs_dir(job_id)
    if not jdir.exists():
        raise HTTPException(404, "job not found")
    
    try:
        import shutil
        shutil.rmtree(jdir)
        return {"message": "Job deleted successfully"}
    except Exception as e:
        raise HTTPException(500, f"Failed to delete job: {str(e)}")

# User management endpoints (только для администраторов)
@app.get("/users")
def list_users(admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Получение списка всех пользователей (только для администраторов)"""
    try:
        users = db.query(User).all()
        return {
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at
                    # Временно убираем updated_at, так как поле может отсутствовать в базе данных
                    # "updated_at": user.updated_at
                }
                for user in users
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/users/{user_id}")
def delete_user(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Удаление пользователя по ID (только для администраторов)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Нельзя удалить самого себя
    if user.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    
    try:
        db.delete(user)
        db.commit()
        return {
            "message": "Пользователь успешно удален",
            "deleted_user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении пользователя: {str(e)}")

@app.delete("/users/by-username/{username}")
def delete_user_by_username(username: str, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Удаление пользователя по имени пользователя (только для администраторов)"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Нельзя удалить самого себя
    if user.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    
    try:
        db.delete(user)
        db.commit()
        return {
            "message": "Пользователь успешно удален",
            "deleted_user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении пользователя: {str(e)}")

@app.patch("/users/{user_id}/deactivate")
def deactivate_user(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Деактивация пользователя (мягкое удаление) (только для администраторов)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Нельзя деактивировать самого себя
    if user.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Нельзя деактивировать самого себя")
    
    try:
        user.is_active = False
        db.commit()
        return {
            "message": "Пользователь деактивирован",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при деактивации пользователя: {str(e)}")

@app.patch("/users/{user_id}/activate")
def activate_user(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Активация пользователя (только для администраторов)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    try:
        user.is_active = True
        db.commit()
        return {
            "message": "Пользователь активирован",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при активации пользователя: {str(e)}")

@app.patch("/users/{user_id}/make-admin")
def make_admin(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Назначение пользователя администратором (только для администраторов)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    try:
        user.is_admin = True
        db.commit()
        return {
            "message": "Пользователь назначен администратором",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при назначении администратора: {str(e)}")

@app.patch("/users/{user_id}/remove-admin")
def remove_admin(user_id: int, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    """Снятие прав администратора (только для администраторов)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Нельзя снять права администратора у самого себя
    if user.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Нельзя снять права администратора у самого себя")
    
    try:
        user.is_admin = False
        db.commit()
        return {
            "message": "Права администратора сняты",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при снятии прав администратора: {str(e)}")