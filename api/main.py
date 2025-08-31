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
    q.enqueue("tasks.transcribe.transcribe_job", job_id, audio_path, language)

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
    summary    = jdir / "summary.json"
    if not transcript.exists():
        return JSONResponse({"error": "not_ready"}, status_code=202)
    out = {"job_id": job_id}
    out["transcript"] = json.loads(transcript.read_text("utf-8"))
    if summary.exists():
        out["summary"] = json.loads(summary.read_text("utf-8"))
    return out
