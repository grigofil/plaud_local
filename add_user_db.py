#!/usr/bin/env python3
"""
Скрипт для добавления новых пользователей напрямую в базу данных Plaud
"""

import sys
import os
import getpass
from pathlib import Path

# Добавляем путь к API модулям
sys.path.append(str(Path(__file__).parent / "api"))

from database import get_db, init_db
from models import User
from auth import get_password_hash
from sqlalchemy.orm import Session

def add_user_directly(username: str, email: str, password: str):
    """Добавляет пользователя напрямую в базу данных"""
    try:
        # Инициализируем базу данных
        init_db()
        
        # Получаем сессию базы данных
        db = next(get_db())
        
        # Проверяем, существует ли пользователь
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"❌ Пользователь с именем '{username}' или email '{email}' уже существует")
            return False
        
        # Хешируем пароль
        hashed_password = get_password_hash(password)
        
        # Создаем нового пользователя
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True
        )
        
        # Добавляем в базу данных
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ Пользователь успешно добавлен в базу данных!")
        print(f"   ID: {new_user.id}")
        print(f"   Username: {new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Active: {new_user.is_active}")
        print(f"   Created: {new_user.created_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении пользователя: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    print("=== Добавление нового пользователя в базу данных Plaud ===\n")
    
    # Получаем данные пользователя
    username = input("Введите имя пользователя: ").strip()
    if not username:
        print("❌ Имя пользователя не может быть пустым")
        return
    
    email = input("Введите email: ").strip()
    if not email:
        print("❌ Email не может быть пустым")
        return
    
    password = getpass.getpass("Введите пароль: ")
    if not password:
        print("❌ Пароль не может быть пустым")
        return
    
    password_confirm = getpass.getpass("Подтвердите пароль: ")
    if password != password_confirm:
        print("❌ Пароли не совпадают")
        return
    
    print(f"\nДобавляю пользователя {username} в базу данных...")
    
    # Добавляем пользователя
    success = add_user_directly(username, email, password)
    
    if success:
        print("\n🎉 Пользователь успешно добавлен в базу данных!")
        print("Теперь вы можете войти в систему используя /auth/login endpoint")
    else:
        print("\n💥 Не удалось добавить пользователя")

if __name__ == "__main__":
    main()
