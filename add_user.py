#!/usr/bin/env python3
"""
Скрипт для добавления новых пользователей в систему Plaud
"""

import requests
import sys
import getpass

def add_user(api_url, username, email, password):
    """Добавляет нового пользователя через API"""
    try:
        response = requests.post(
            f"{api_url}/auth/register",
            data={
                "username": username,
                "email": email,
                "password": password
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Пользователь успешно добавлен!")
            print(f"   ID: {result['user_id']}")
            print(f"   Username: {result['username']}")
            return True
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            print(f"❌ Ошибка при добавлении пользователя: {error_detail}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def main():
    # Настройки API
    API_URL = "http://localhost:8000"  # Измените на ваш URL API
    
    print("=== Добавление нового пользователя в Plaud ===\n")
    
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
    
    print(f"\nДобавляю пользователя {username}...")
    
    # Добавляем пользователя
    success = add_user(API_URL, username, email, password)
    
    if success:
        print("\n🎉 Пользователь успешно добавлен в систему!")
        print("Теперь вы можете войти в систему используя /auth/login endpoint")
    else:
        print("\n💥 Не удалось добавить пользователя")

if __name__ == "__main__":
    main()
