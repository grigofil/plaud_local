#!/usr/bin/env python3
"""
Диагностический скрипт для проверки сервера
"""

import sys
import traceback

def test_imports():
    """Тестирует импорты"""
    try:
        print("1. Тестируем импорты...")
        
        from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends, Header, Form
        print("   ✅ FastAPI импортирован")
        
        from sqlalchemy.orm import Session
        print("   ✅ SQLAlchemy импортирован")
        
        from database import get_db, init_db
        print("   ✅ database модуль импортирован")
        
        from models import User
        print("   ✅ models модуль импортирован")
        
        from auth import verify_password, get_password_hash, create_access_token, decode_access_token
        print("   ✅ auth модуль импортирован")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка импорта: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Тестирует базу данных"""
    try:
        print("2. Тестируем базу данных...")
        
        from database import get_db, init_db
        from models import User
        
        init_db()
        print("   ✅ База данных инициализирована")
        
        db = next(get_db())
        users = db.query(User).all()
        print(f"   ✅ Подключение к БД работает, найдено пользователей: {len(users)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка базы данных: {e}")
        traceback.print_exc()
        return False

def test_auth():
    """Тестирует аутентификацию"""
    try:
        print("3. Тестируем аутентификацию...")
        
        from database import get_db
        from models import User
        from auth import verify_password, create_access_token
        
        db = next(get_db())
        user = db.query(User).filter(User.username == "qwe").first()
        
        if not user:
            print("   ❌ Пользователь qwe не найден")
            return False
        
        print(f"   ✅ Пользователь найден: {user.username}")
        
        password_correct = verify_password("qwe", user.hashed_password)
        if not password_correct:
            print("   ❌ Неверный пароль")
            return False
        
        print("   ✅ Пароль верный")
        
        token = create_access_token(data={"sub": user.username})
        print(f"   ✅ Токен создан: {token[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка аутентификации: {e}")
        traceback.print_exc()
        return False

def test_fastapi_app():
    """Тестирует создание FastAPI приложения"""
    try:
        print("4. Тестируем создание FastAPI приложения...")
        
        from fastapi import FastAPI
        from database import get_db, init_db
        from models import User
        from auth import verify_password, get_password_hash, create_access_token, decode_access_token
        from sqlalchemy.orm import Session
        
        app = FastAPI(title="Plaud API")
        print("   ✅ FastAPI приложение создано")
        
        # Инициализируем базу данных
        init_db()
        print("   ✅ База данных инициализирована в приложении")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка создания приложения: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Диагностика сервера Plaud ===\n")
    
    success = True
    
    success &= test_imports()
    print()
    
    success &= test_database()
    print()
    
    success &= test_auth()
    print()
    
    success &= test_fastapi_app()
    print()
    
    if success:
        print("🎉 Все тесты прошли успешно!")
        print("Сервер должен работать корректно.")
    else:
        print("💥 Обнаружены проблемы!")
        print("Необходимо исправить ошибки перед запуском сервера.")
