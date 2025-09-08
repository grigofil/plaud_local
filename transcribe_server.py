#!/usr/bin/env python3
"""
Файл для запуска сервера транскрипции Plaud Local
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.workers.transcribe_server import app
import uvicorn
from src.config.settings import TRANSCRIBE_SERVER_PORT

if __name__ == "__main__":
    print("🚀 Запуск сервера транскрипции Plaud Local...")
    print(f"📡 Сервер транскрибации будет доступен по адресу: http://localhost:{TRANSCRIBE_SERVER_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=TRANSCRIBE_SERVER_PORT)