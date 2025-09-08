import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from faster_whisper import WhisperModel
from redis import Redis
from rq import Queue

from src.config.settings import (
    DATA_DIR, WHISPER_MODEL, WHISPER_DEVICE, 
    WHISPER_COMPUTE_TYPE, WHISPER_FAST_MODE, REDIS_URL, TRANSCRIBE_SERVER_PORT
)

# Initialize model once on server startup
print(f"Инициализация Whisper модели: {WHISPER_MODEL} на {WHISPER_DEVICE}")
if WHISPER_FAST_MODE:
    if WHISPER_MODEL == "large" or WHISPER_MODEL == "large-v2":
        WHISPER_MODEL = "medium"
    elif WHISPER_MODEL == "medium":
        WHISPER_MODEL = "small"
    print(f"Быстрый режим: используем модель {WHISPER_MODEL}")

model = WhisperModel(
    WHISPER_MODEL,
    device=WHISPER_DEVICE,
    compute_type=WHISPER_COMPUTE_TYPE
)
print("Whisper модель инициализирована и готова к работе!")

# Create FastAPI app
app = FastAPI(title="Transcription Service", version="1.0.0")

class TranscriptionRequest(BaseModel):
    job_id: str
    language: str = "ru"

class TranscriptionResponse(BaseModel):
    job_id: str
    status: str
    message: str
    text: Optional[str] = None
    segments: Optional[list] = None

def _jdir(job_id: str) -> Path:
    d = DATA_DIR / "jobs" / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def convert_to_wav(input_path: Path, output_path: Path):
    """Convert audio file to WAV format for better Whisper compatibility"""
    try:
        print(f"Конвертация {input_path} в {output_path}")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            return False
            
        print(f"Конвертация успешна: {output_path}")
        return True
    except Exception as e:
        print(f"Conversion error: {e}")
        return False

def process_transcription(job_id: str, audio_path: Path, language: str = "ru"):
    """Process transcription in background"""
    try:
        jdir = _jdir(job_id)
        print(f"Начинаю транскрипцию job_id: {job_id}")
        print(f"Исходный аудиофайл: {audio_path}")
        
        # Convert to WAV if not WAV file
        wav_path = audio_path
        if audio_path.suffix.lower() != '.wav':
            wav_path = jdir / "input_converted.wav"
            if not convert_to_wav(audio_path, wav_path):
                wav_path = audio_path
                print(f"Using original file: {audio_path}")

        print(f"Обрабатываю аудиофайл: {wav_path}")
        
        # Optimized parameters for faster processing
        segments, info = model.transcribe(
            str(wav_path),
            language=language,
            vad_filter=True,
            beam_size=1,
            no_speech_threshold=0.6,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            temperature=0.0,
            condition_on_previous_text=False,
            initial_prompt=None,
            word_timestamps=False
        )
        
        print(f"Whisper вернул info: {info}")
        print(f"Начинаю обработку сегментов...")

        out = {"language": language, "text": "", "segments": []}
        parts = []
        segment_count = 0
        
        for i, seg in enumerate(segments):
            print(f"Обрабатываю сегмент {i}: {seg.start:.2f}s - {seg.end:.2f}s: '{seg.text}'")
            parts.append(seg.text)
            out["segments"].append({
                "id": i,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text
            })
            segment_count += 1
            
        out["text"] = " ".join(parts).strip()
        
        print(f"Результат транскрипции: {segment_count} сегментов, длина текста: {len(out['text'])}")

        # Save results
        (jdir / "transcript.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
        (jdir / "transcript.txt").write_text(out["text"], "utf-8")
        
        print("Файлы транскрипции сохранены")

        # Add to summarization queue
        r = Redis.from_url(REDIS_URL)
        q = Queue("sum", connection=r)
        q.enqueue("src.tasks.summarize.summarize_job", job_id)
        print("Задача добавлена в очередь суммаризации")
        
        # Update meta.json
        meta_file = jdir / "meta.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text())
            meta["transcription_status"] = "completed"
            meta["transcription_text"] = out["text"]
            meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
        
        print(f"Транскрипция job_id {job_id} завершена успешно")
        
    except Exception as e:
        print(f"Ошибка транскрипции job_id {job_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Create empty result in case of error
        jdir = _jdir(job_id)
        out = {"language": language, "text": "", "segments": [], "error": str(e)}
        (jdir / "transcript.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
        (jdir / "transcript.txt").write_text("", "utf-8")
        
        # Update meta.json with error
        meta_file = jdir / "meta.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text())
            meta["transcription_status"] = "error"
            meta["transcription_error"] = str(e)
            meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")

@app.get("/")
async def root():
    return {"message": "Transcription Service is running", "model": WHISPER_MODEL, "device": WHISPER_DEVICE}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": True}

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    job_id: str = Query(..., description="Job ID for transcription"),
    language: str = Query("ru", description="Language for transcription"),
    file: UploadFile = File(...)
):
    """Accept audio file and start transcription in background"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Audio file is required")
    
    try:
        # Create temporary file for uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            temp_path = Path(temp_file.name)
        
        # Start transcription in background
        background_tasks.add_task(process_transcription, job_id, temp_path, language)
        
        # Update meta.json
        jdir = _jdir(job_id)
        meta_file = jdir / "meta.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text())
        else:
            meta = {}
        
        meta["transcription_status"] = "processing"
        meta["transcription_started"] = True
        meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
        
        return TranscriptionResponse(
            job_id=job_id,
            status="accepted",
            message="Audio file received and transcription started"
        )
        
    except Exception as e:
        print(f"Error processing upload for job_id {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/status/{job_id}")
async def get_transcription_status(job_id: str):
    """Check transcription status for specific job_id"""
    try:
        jdir = _jdir(job_id)
        transcript_file = jdir / "transcript.json"
        meta_file = jdir / "meta.json"
        
        if not jdir.exists():
            return {"job_id": job_id, "status": "not_found"}
        
        if transcript_file.exists():
            transcript = json.loads(transcript_file.read_text())
            return {
                "job_id": job_id,
                "status": "completed",
                "text": transcript.get("text", ""),
                "segments": transcript.get("segments", [])
            }
        
        if meta_file.exists():
            meta = json.loads(meta_file.read_text())
            if meta.get("transcription_status") == "processing":
                return {"job_id": job_id, "status": "processing"}
            elif meta.get("transcription_status") == "error":
                return {"job_id": job_id, "status": "error", "error": meta.get("transcription_error")}
        
        return {"job_id": job_id, "status": "pending"}
        
    except Exception as e:
        print(f"Error checking status for job_id {job_id}: {e}")
        return {"job_id": job_id, "status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print(f"Запускаю сервер транскрибации на порту {TRANSCRIBE_SERVER_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=TRANSCRIBE_SERVER_PORT)