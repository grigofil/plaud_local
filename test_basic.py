#!/usr/bin/env python3
"""
Базовый тест для проверки работы новой структуры проекта
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("🧪 Тестирование импортов модулей...")
    
    try:
        from src.config.settings import API_AUTH_TOKENS, DATA_DIR
        print("✅ src.config.settings - OK")
        
        from src.models.user import User
        print("✅ src.models.user - OK")
        
        from src.utils.database import get_db, init_db
        print("✅ src.utils.database - OK")
        
        from src.utils.auth import verify_password, get_password_hash
        print("✅ src.utils.auth - OK")
        
        from src.services.user_service import create_user, authenticate_user
        print("✅ src.services.user_service - OK")
        
        from src.services.transcription_service import jobs_dir, get_job_status
        print("✅ src.services.transcription_service - OK")
        
        from src.api.dependencies import require_auth, require_admin
        print("✅ src.api.dependencies - OK")
        
        from src.tasks.transcribe import transcribe_job
        print("✅ src.tasks.transcribe - OK")
        
        from src.tasks.summarize import summarize_job
        print("✅ src.tasks.summarize - OK")
        
        print("🎉 Все модули успешно импортируются!")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🧪 Тестирование конфигурации...")
    
    try:
        from src.config.settings import API_AUTH_TOKENS, DATA_DIR
        
        print(f"✅ API_AUTH_TOKENS: {API_AUTH_TOKENS}")
        print(f"✅ DATA_DIR: {DATA_DIR}")
        
        # Check that data directory exists or can be created
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ DATA_DIR доступен для записи: {DATA_DIR.exists()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def test_database():
    """Test database connection"""
    print("\n🧪 Тестирование базы данных...")
    
    try:
        from src.utils.database import init_db, get_db
        from src.models.user import User
        
        # Initialize database
        init_db()
        print("✅ База данных инициализирована")
        
        # Test session creation
        from sqlalchemy.orm import Session
        db = next(get_db())
        print("✅ Сессия базы данных создана")
        
        # Test basic query
        users = db.query(User).all()
        print(f"✅ Запрос к базе данных выполнен: {len(users)} пользователей")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 Plaud Local - Тестирование новой структуры проекта")
    print("=" * 60)
    
    success = True
    
    # Run tests
    success &= test_imports()
    success &= test_config()
    success &= test_database()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Все тесты пройдены успешно!")
        print("✅ Новая структура проекта работает корректно")
    else:
        print("❌ Некоторые тесты не пройдены")
        print("⚠️  Проверьте настройки и зависимости")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)