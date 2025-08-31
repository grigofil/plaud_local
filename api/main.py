import os, uuid, shutil, json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from redis import Redis
from rq import Queue

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from fastapi import Depends, Header
import secrets

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DATA_DIR  = Path(os.getenv("DATA_DIR", "/data"))
LANG_DEFAULT = "ru"
API_TOKENS = {t.strip() for t in os.getenv("API_AUTH_TOKEN", "").split(",") if t.strip()}

def require_auth(authorization: str = Header(default=None), x_api_key: str = Header(default=None)):
    """
    Принимаем либо Authorization: Bearer <token>, либо X-API-Key: <token>.
    Если переменная окружения API_AUTH_TOKEN не задана — auth выключен.
    """
    if not API_TOKENS:  # auth disabled
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
    
    # иначе — 401
    from fastapi import HTTPException
    raise HTTPException(status_code=401, detail="Unauthorized")


app = FastAPI(title="Whisper+DeepSeek API (variant B)")

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

def enqueue_asr(job_id: str, audio_path: str, language: str):
    r = Redis.from_url(REDIS_URL)
    q = Queue("asr", connection=r)
    
    # Получаем таймаут из переменных окружения или используем значение по умолчанию
    timeout = int(os.getenv("TRANSCRIBE_TIMEOUT", "6000"))  # 10 минут по умолчанию
    
    q.enqueue(
        "tasks.transcribe.transcribe_job", 
        job_id, 
        audio_path, 
        language,
        job_timeout=timeout,
        result_ttl=timeout * 2  # Результат хранится в 2 раза дольше таймаута
    )

@app.get("/healthz")
def healthz(_auth=Depends(require_auth)):
    return {"status": "ok"}

@app.get("/auth/check")
def check_auth(_auth=Depends(require_auth)):
    """Проверка авторизации - возвращает информацию о текущем токене"""
    return {
        "status": "authenticated",
        "message": "Авторизация успешна",
        "auth_enabled": bool(API_TOKENS)
    }

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

    enqueue_asr(job_id, str(audio_path), language)
    return {"job_id": job_id, "status": "queued"}

@app.get("/status/{job_id}")
def status(job_id: str, _auth=Depends(require_auth)): 
    jdir = jobs_dir(job_id)
    if not jdir.exists():
        raise HTTPException(404, "job not found")

    transcript = jdir / "transcript.json"
    summary    = jdir / "summary.json"
    if summary.exists():
        return {"job_id": job_id, "status": "done"}
    if transcript.exists():
        return {"job_id": job_id, "status": "transcribed_waiting_summary"}
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
