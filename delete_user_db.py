#!/usr/bin/env python3
"""
Скрипт для удаления пользователей напрямую из базы данных Plaud
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
                return True
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        return False

def list_users_directly():
    """Получает список всех пользователей из базы данных"""
    try:
        # Проверяем и выполняем миграцию при необходимости
        if not check_and_migrate_database():
            return []
        
        # Инициализируем базу данных
        init_db()
        
        # Получаем сессию базы данных
        db = next(get_db())
        
        # Получаем всех пользователей
        users = db.query(User).all()
        
        return users
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка пользователей: {e}")
        return []
    finally:
        if 'db' in locals():
            db.close()

def delete_user_by_id_directly(user_id: int):
    """Удаляет пользователя по ID напрямую из базы данных"""
    try:
        # Проверяем и выполняем миграцию при необходимости
        if not check_and_migrate_database():
            return False
        
        # Инициализируем базу данных
        init_db()
        
        # Получаем сессию базы данных
        db = next(get_db())
        
        # Находим пользователя
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"❌ Пользователь с ID {user_id} не найден")
            return False
        
        # Сохраняем информацию о пользователе для вывода
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        
        # Удаляем пользователя
        db.delete(user)
        db.commit()
        
        print(f"✅ Пользователь успешно удален из базы данных!")
        print(f"   ID: {user_info['id']}")
        print(f"   Username: {user_info['username']}")
        print(f"   Email: {user_info['email']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении пользователя: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

def delete_user_by_username_directly(username: str):
    """Удаляет пользователя по имени напрямую из базы данных"""
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
        
        # Сохраняем информацию о пользователе для вывода
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        
        # Удаляем пользователя
        db.delete(user)
        db.commit()
        
        print(f"✅ Пользователь успешно удален из базы данных!")
        print(f"   ID: {user_info['id']}")
        print(f"   Username: {user_info['username']}")
        print(f"   Email: {user_info['email']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении пользователя: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

def deactivate_user_directly(user_id: int):
    """Деактивирует пользователя (мягкое удаление) напрямую в базе данных"""
    try:
        # Проверяем и выполняем миграцию при необходимости
        if not check_and_migrate_database():
            return False
        
        # Инициализируем базу данных
        init_db()
        
        # Получаем сессию базы данных
        db = next(get_db())
        
        # Находим пользователя
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"❌ Пользователь с ID {user_id} не найден")
            return False
        
        if not user.is_active:
            print(f"❌ Пользователь с ID {user_id} уже деактивирован")
            return False
        
        # Деактивируем пользователя
        user.is_active = False
        db.commit()
        
        print(f"✅ Пользователь успешно деактивирован в базе данных!")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Active: {user.is_active}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при деактивации пользователя: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    print("=== Удаление пользователя из базы данных Plaud ===\n")
    
    # Получаем список пользователей
    print("Получаю список пользователей из базы данных...")
    users = list_users_directly()
    
    if not users:
        print("❌ Пользователи не найдены в базе данных")
        return
    
    print(f"\nНайдено пользователей: {len(users)}")
    print("\nСписок пользователей:")
    print("-" * 80)
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Status':<10}")
    print("-" * 80)
    
    for user in users:
        status = "Активен" if user.is_active else "Заблокирован"
        print(f"{user.id:<5} {user.username:<20} {user.email:<30} {status:<10}")
    
    print("-" * 80)
    
    # Выбор действия
    print("\nВыберите действие:")
    print("1. Удалить пользователя по ID")
    print("2. Удалить пользователя по имени")
    print("3. Деактивировать пользователя (мягкое удаление)")
    print("4. Выход")
    
    choice = input("\nВведите номер действия (1-4): ").strip()
    
    if choice == "1":
        try:
            user_id = int(input("Введите ID пользователя для удаления: ").strip())
            user = next((u for u in users if u.id == user_id), None)
            if not user:
                print("❌ Пользователь с таким ID не найден")
                return
            
            print(f"\nВы собираетесь удалить пользователя:")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            
            confirm = input("\nВы уверены? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y', 'да', 'д']:
                success = delete_user_by_id_directly(user_id)
                if success:
                    print("\n🎉 Пользователь успешно удален из базы данных!")
                else:
                    print("\n💥 Не удалось удалить пользователя")
            else:
                print("❌ Операция отменена")
                
        except ValueError:
            print("❌ Неверный формат ID")
    
    elif choice == "2":
        username = input("Введите имя пользователя для удаления: ").strip()
        if not username:
            print("❌ Имя пользователя не может быть пустым")
            return
        
        user = next((u for u in users if u.username == username), None)
        if not user:
            print("❌ Пользователь с таким именем не найден")
            return
        
        print(f"\nВы собираетесь удалить пользователя:")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        
        confirm = input("\nВы уверены? (yes/no): ").strip().lower()
        if confirm in ['yes', 'y', 'да', 'д']:
            success = delete_user_by_username_directly(username)
            if success:
                print("\n🎉 Пользователь успешно удален из базы данных!")
            else:
                print("\n💥 Не удалось удалить пользователя")
        else:
            print("❌ Операция отменена")
    
    elif choice == "3":
        try:
            user_id = int(input("Введите ID пользователя для деактивации: ").strip())
            user = next((u for u in users if u.id == user_id), None)
            if not user:
                print("❌ Пользователь с таким ID не найден")
                return
            
            if not user.is_active:
                print("❌ Пользователь уже деактивирован")
                return
            
            print(f"\nВы собираетесь деактивировать пользователя:")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            
            confirm = input("\nВы уверены? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y', 'да', 'д']:
                success = deactivate_user_directly(user_id)
                if success:
                    print("\n🎉 Пользователь успешно деактивирован в базе данных!")
                else:
                    print("\n💥 Не удалось деактивировать пользователя")
            else:
                print("❌ Операция отменена")
                
        except ValueError:
            print("❌ Неверный формат ID")
    
    elif choice == "4":
        print("👋 До свидания!")
    
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
