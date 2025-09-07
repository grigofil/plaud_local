#!/usr/bin/env python3
"""
Прямой тест аутентификации
"""

import sys
from pathlib import Path

# Добавляем путь к API модулям
sys.path.append(str(Path(__file__).parent / "api"))

from database import get_db, init_db
from models import User
from auth import verify_password, create_access_token

def test_auth():
    """Тестирует аутентификацию напрямую"""
    try:
        print("🔐 Тестируем аутентификацию напрямую...")
        
        # Инициализируем базу данных
        init_db()
        
        # Получаем сессию базы данных
        db = next(get_db())
        
        # Ищем пользователя qwe
        user = db.query(User).filter(User.username == "qwe").first()
        
        if not user:
            print("❌ Пользователь qwe не найден")
            return False
        
        print(f"✅ Пользователь найден: {user.username}")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Is Active: {user.is_active}")
        print(f"   Is Admin: {getattr(user, 'is_admin', 'NO FIELD')}")
        
        # Проверяем пароль
        password_correct = verify_password("qwe", user.hashed_password)
        print(f"   Password correct: {password_correct}")
        
        if not password_correct:
            print("❌ Неверный пароль")
            return False
        
        # Создаем токен
        token = create_access_token(data={"sub": user.username})
        print(f"✅ Токен создан: {token[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("=== Прямой тест аутентификации ===\n")
    success = test_auth()
    
    if success:
        print("\n🎉 Тест прошел успешно!")
    else:
        print("\n💥 Тест не прошел")
