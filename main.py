#!/usr/bin/env python3
"""
Основной файл приложения Plaud Local
Запускает основной сервер приложения
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.core.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Запуск основного приложения Plaud Local...")
    print(f"📡 Сервер будет доступен по адресу: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
