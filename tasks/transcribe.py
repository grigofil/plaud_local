import os, json, subprocess
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
# Для ускорения можно использовать меньшую модель
if os.getenv("WHISPER_FAST_MODE", "false").lower() == "true":
    if WHISPER_MODEL == "large" or WHISPER_MODEL == "large-v2":
        WHISPER_MODEL = "medium"
    elif WHISPER_MODEL == "medium":
        WHISPER_MODEL = "small"
    print(f"Быстрый режим: используем модель {WHISPER_MODEL}")

print(f"Инициализация Whisper модели: {WHISPER_MODEL} на {WHISPER_DEVICE}")
model = WhisperModel(
    WHISPER_MODEL,
    device=WHISPER_DEVICE,          # "cpu"
    compute_type=WHISPER_COMPUTE_TYPE  # "int8" (на CPU)
)
print("Whisper модель инициализирована")

def _jdir(job_id: str) -> Path:
    d = DATA_DIR / "jobs" / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def convert_to_wav(input_path: Path, output_path: Path):
    """Конвертирует аудиофайл в WAV формат для лучшей совместимости с Whisper"""
    try:
        print(f"Конвертация {input_path} в {output_path}")
        cmd = [
            "ffmpeg", "-y",  # -y для перезаписи существующего файла
            "-i", str(input_path),
            "-acodec", "pcm_s16le",  # 16-bit PCM
            "-ar", "16000",  # 16kHz sample rate
            "-ac", "1",  # mono
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
    jdir = _jdir(job_id)
    audio_path = Path(audio_path)
    
    print(f"Начинаю транскрипцию job_id: {job_id}")
    print(f"Исходный аудиофайл: {audio_path}")
    
    # Конвертируем в WAV если это не WAV файл
    wav_path = audio_path
    if audio_path.suffix.lower() != '.wav':
        wav_path = jdir / "input_converted.wav"
        if not convert_to_wav(audio_path, wav_path):
            # Если конвертация не удалась, пробуем оригинальный файл
            wav_path = audio_path
            print(f"Using original file: {audio_path}")

    print(f"Обрабатываю аудиофайл: {wav_path}")
    
    try:
        print("Запускаю Whisper транскрипцию...")
        
        # Оптимизированные параметры для ускорения обработки
        segments, info = model.transcribe(
            str(wav_path),
            language=language,
            vad_filter=True,  # Включаем VAD фильтр для ускорения
            beam_size=1,  # Уменьшаем beam size для ускорения
            no_speech_threshold=0.6,  # Увеличиваем порог для определения речи
            compression_ratio_threshold=2.4,  # Стандартный порог сжатия
            log_prob_threshold=-1.0,  # Стандартный порог вероятности
            temperature=0.0,  # Детерминированный режим
            condition_on_previous_text=False,  # Отключаем зависимость от предыдущего текста
            initial_prompt=None,  # Без начального промпта
            word_timestamps=False  # Отключаем временные метки слов для ускорения
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
        print(f"Полный текст: '{out['text']}'")

        (jdir / "transcript.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
        (jdir / "transcript.txt").write_text(out["text"], "utf-8")
        
        print("Файлы транскрипции сохранены")

        # очередь на суммаризацию
        r = Redis.from_url(REDIS_URL)
        q = Queue("sum", connection=r)
        # Use string path to avoid circular import issues
        q.enqueue("tasks.summarize.summarize_job", job_id)
        print("Задача добавлена в очередь суммаризации")
        return {"ok": True}
        
    except Exception as e:
        print(f"Ошибка транскрипции: {e}")
        import traceback
        traceback.print_exc()
        # Создаем пустой результат в случае ошибки
        out = {"language": language, "text": "", "segments": [], "error": str(e)}
        (jdir / "transcript.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
        (jdir / "transcript.txt").write_text("", "utf-8")
        return {"ok": False, "error": str(e)}
