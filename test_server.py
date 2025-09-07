#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы сервера
"""

import sys
import os
from pathlib import Path

# Добавляем путь к API модулям
sys.path.append(str(Path(__file__).parent / "api"))

try:
    print("1. Импортируем модули...")
    from database import get_db, init_db, engine
    from models import User
    from auth import verify_password, get_password_hash, create_access_token, decode_access_token
    print("✅ Все модули импортированы успешно")
    
    print("2. Инициализируем базу данных...")
    init_db()
    print("✅ База данных инициализирована")
    
    print("3. Проверяем подключение к базе данных...")
    db = next(get_db())
    users = db.query(User).all()
    print(f"✅ Подключение к БД работает, найдено пользователей: {len(users)}")
    
    print("4. Проверяем аутентификацию...")
    if users:
        user = users[0]
        print(f"   Тестируем пользователя: {user.username}")
        
        # Проверяем, есть ли поле is_admin
        if hasattr(user, 'is_admin'):
            print(f"   is_admin: {user.is_admin}")
        else:
            print("   ❌ Поле is_admin отсутствует!")
            
        # Проверяем создание токена
        token = create_access_token(data={"sub": user.username})
        print(f"   ✅ Токен создан: {token[:20]}...")
        
        # Проверяем декодирование токена
        payload = decode_access_token(token)
        print(f"   ✅ Токен декодирован: {payload}")
    
    print("\n🎉 Все тесты прошли успешно!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
