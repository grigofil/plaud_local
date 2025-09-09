
#!/usr/bin/env python3
"""
Скрипт для миграции базы данных - добавление поля is_admin
"""

import sys
import os
from pathlib import Path

# Добавляем путь к API модулям
sys.path.append(str(Path(__file__).parent / "api"))

from database import engine, init_db
from models import User
from sqlalchemy import text
from sqlalchemy.orm import Session

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Проверяет, существует ли колонка в таблице"""
    try:
        with engine.connect() as conn:
            # Для SQLite проверяем структуру таблицы
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]
            return column_name in columns
    except Exception as e:
        print(f"❌ Ошибка при проверке колонки: {e}")
        return False

def add_is_admin_column():
    """Добавляет колонку is_admin в таблицу users"""
    try:
        with engine.connect() as conn:
            # Добавляем колонку is_admin с значением по умолчанию False
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            conn.commit()
            print("✅ Колонка is_admin успешно добавлена в таблицу users")
            return True
    except Exception as e:
        print(f"❌ Ошибка при добавлении колонки: {e}")
        return False

def migrate_database():
    """Выполняет миграцию базы данных"""
    print("=== Миграция базы данных ===")
    
    # Проверяем, существует ли колонка is_admin
    if check_column_exists('users', 'is_admin'):
        print("✅ Колонка is_admin уже существует в таблице users")
        return True
    
    print("📝 Колонка is_admin не найдена, добавляем...")
    
    # Добавляем колонку
    success = add_is_admin_column()
    
    if success:
        print("🎉 Миграция базы данных завершена успешно!")
        print("Теперь можно использовать функции управления пользователями")
        return True
    else:
        print("💥 Ошибка при миграции базы данных")
        return False

def verify_migration():
    """Проверяет, что миграция прошла успешно"""
    try:
        # Инициализируем базу данных
        init_db()
        
        # Получаем сессию базы данных
        db = Session(engine)
        
        # Пытаемся получить пользователей с полем is_admin
        users = db.query(User).all()
        
        print(f"\n✅ Миграция успешна! Найдено пользователей: {len(users)}")
        
        if users:
            print("\nСписок пользователей:")
            print("-" * 60)
            print(f"{'ID':<5} {'Username':<15} {'Email':<25} {'Admin':<8}")
            print("-" * 60)
            
            for user in users:
                admin_status = "Да" if getattr(user, 'is_admin', False) else "Нет"
                print(f"{user.id:<5} {user.username:<15} {user.email:<25} {admin_status:<8}")
            
            print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке миграции: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    print("=== Миграция базы данных Plaud ===\n")
    
    # Выполняем миграцию
    if migrate_database():
        # Проверяем результат
        verify_migration()
        
        print("\n🎉 Миграция завершена!")
        print("Теперь вы можете:")
        print("1. Назначить администратора: python make_admin.py")
        print("2. Использовать веб-интерфейс управления пользователями")
    else:
        print("\n💥 Миграция не удалась")
        print("Проверьте права доступа к базе данных")

if __name__ == "__main__":
    main()
