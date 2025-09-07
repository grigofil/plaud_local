#!/usr/bin/env python3
"""
Скрипт для назначения пользователя администратором
"""

import sys
import os
from pathlib import Path

# Добавляем путь к API модулям
sys.path.append(str(Path(__file__).parent / "api"))

from database import get_db, init_db, engine
from models import User
from sqlalchemy.orm import Session
from sqlalchemy import text

def check_and_migrate_database():
    """Проверяет и выполняет миграцию базы данных при необходимости"""
    try:
        with engine.connect() as conn:
            # Проверяем, существует ли колонка is_admin
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'is_admin' not in columns:
                print("📝 Колонка is_admin не найдена, выполняем миграцию...")
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                conn.commit()
                print("✅ Миграция выполнена успешно!")
                return True
            else:
                print("✅ Колонка is_admin уже существует")
                return True
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        return False

def make_user_admin(username: str):
    """Назначает пользователя администратором"""
    try:
        # Проверяем и выполняем миграцию при необходимости
        if not check_and_migrate_database():
            return False
        
        # Инициализируем базу данных
        init_db()
        
        # Получаем сессию базы данных
        db = next(get_db())
        
        # Находим пользователя
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            print(f"❌ Пользователь с именем '{username}' не найден")
            return False
        
        if user.is_admin:
            print(f"❌ Пользователь '{username}' уже является администратором")
            return False
        
        # Назначаем администратором
        user.is_admin = True
        db.commit()
        
        print(f"✅ Пользователь '{username}' назначен администратором!")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Is Admin: {user.is_admin}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при назначении администратора: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

def list_users():
    """Показывает список всех пользователей"""
    try:
        # Проверяем и выполняем миграцию при необходимости
        if not check_and_migrate_database():
            return
        
        # Инициализируем базу данных
        init_db()
        
        # Получаем сессию базы данных
        db = next(get_db())
        
        # Получаем всех пользователей
        users = db.query(User).all()
        
        if not users:
            print("❌ Пользователи не найдены в базе данных")
            return
        
        print(f"\nНайдено пользователей: {len(users)}")
        print("\nСписок пользователей:")
        print("-" * 80)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<8} {'Active':<8}")
        print("-" * 80)
        
        for user in users:
            admin_status = "Да" if user.is_admin else "Нет"
            active_status = "Да" if user.is_active else "Нет"
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {admin_status:<8} {active_status:<8}")
        
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка пользователей: {e}")
    finally:
        if 'db' in locals():
            db.close()

def main():
    print("=== Назначение пользователя администратором ===\n")
    
    # Показываем список пользователей
    list_users()
    
    # Получаем имя пользователя
    username = input("\nВведите имя пользователя для назначения администратором: ").strip()
    if not username:
        print("❌ Имя пользователя не может быть пустым")
        return
    
    print(f"\nНазначаю пользователя {username} администратором...")
    
    # Назначаем администратором
    success = make_user_admin(username)
    
    if success:
        print("\n🎉 Пользователь успешно назначен администратором!")
        print("Теперь он может управлять другими пользователями через веб-интерфейс")
    else:
        print("\n💥 Не удалось назначить пользователя администратором")

if __name__ == "__main__":
    main()
