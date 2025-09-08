#!/usr/bin/env python3
"""
Файл для запуска API сервера Plaud Local
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.api.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Запуск API сервера Plaud Local...")
    print(f"📡 API будет доступен по адресу: http://localhost:8000")
    print(f"🌐 Веб-клиент: http://localhost:8000/app")
    uvicorn.run(app, host="0.0.0.0", port=8000)