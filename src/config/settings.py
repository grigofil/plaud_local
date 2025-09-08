import os
from pathlib import Path
from typing import Set

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

# API Configuration
API_AUTH_TOKENS: Set[str] = {t.strip() for t in os.getenv("API_AUTH_TOKEN", "").split(",") if t.strip()}

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./plaud.db")

# Redis Configuration  
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Whisper Configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_FAST_MODE = os.getenv("WHISPER_FAST_MODE", "false").lower() == "true"

# Transcription Configuration
TRANSCRIBE_TIMEOUT = int(os.getenv("TRANSCRIBE_TIMEOUT", "600"))
TRANSCRIBE_SERVER_URL = os.getenv("TRANSCRIBE_SERVER_URL", "http://worker_transcribe:8002")
TRANSCRIBE_SERVER_PORT = int(os.getenv("TRANSCRIBE_SERVER_PORT", "8002"))

# DeepSeek Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Language Configuration
LANG_DEFAULT = "ru"

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "jobs").mkdir(parents=True, exist_ok=True)