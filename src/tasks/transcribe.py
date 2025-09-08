import os
import json
import subprocess
from pathlib import Path
from faster_whisper import WhisperModel
from redis import Redis
from rq import Queue

from src.config.settings import (
    DATA_DIR, WHISPER_MODEL, WHISPER_DEVICE, 
    WHISPER_COMPUTE_TYPE, WHISPER_FAST_MODE, REDIS_URL
)

# Initialize model once per worker
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
print("Whisper модель инициализирована")

def _jdir(job_id: str) -> Path:
    d = DATA_DIR / "jobs" / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def convert_to_wav(input_path: Path, output_path: Path) -> bool:
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

def transcribe_job(job_id: str, audio_path: str, language: str = "ru"):
    """Process transcription job"""
    jdir = _jdir(job_id)
    audio_path = Path(audio_path)
    
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
    
    try:
        print("Запускаю Whisper транскрипцию...")
        
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

        (jdir / "transcript.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
        (jdir / "transcript.txt").write_text(out["text"], "utf-8")
        
        print("Файлы транскрипции сохранены")

        # Add to summarization queue
        r = Redis.from_url(REDIS_URL)
        q = Queue("sum", connection=r)
        q.enqueue("src.tasks.summarize.summarize_job", job_id)
        print("Задача добавлена в очередь суммаризации")
        return {"ok": True}
        
    except Exception as e:
        print(f"Ошибка транскрипции: {e}")
        import traceback
        traceback.print_exc()
        # Create empty result in case of error
        out = {"language": language, "text": "", "segments": [], "error": str(e)}
        (jdir / "transcript.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
        (jdir / "transcript.txt").write_text("", "utf-8")
        return {"ok": False, "error": str(e)}