import os, json
from pathlib import Path
from faster_whisper import WhisperModel
from redis import Redis
from rq import Queue

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Инициализируем модель один раз на воркер
model = WhisperModel(
    WHISPER_MODEL,
    device=WHISPER_DEVICE,          # "cpu"
    compute_type=WHISPER_COMPUTE_TYPE  # "int8" (на CPU)
)

def _jdir(job_id: str) -> Path:
    d = DATA_DIR / "jobs" / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def transcribe_job(job_id: str, audio_path: str, language: str = "ru"):
    jdir = _jdir(job_id)
    audio_path = Path(audio_path)

    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=True,
        beam_size=5
    )

    out = {"language": language, "text": "", "segments": []}
    parts = []
    for i, seg in enumerate(segments):
        parts.append(seg.text)
        out["segments"].append({
            "id": i,
            "start": seg.start,
            "end": seg.end,
            "text": seg.text
        })
    out["text"] = " ".join(parts).strip()

    (jdir / "transcript.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    (jdir / "transcript.txt").write_text(out["text"], "utf-8")

    # очередь на суммаризацию
    r = Redis.from_url(REDIS_URL)
    q = Queue("sum", connection=r)
    q.enqueue("tasks.summarize.summarize_job", job_id)
    return {"ok": True}
