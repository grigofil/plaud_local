#!/usr/bin/env python3
"""
Скрипт для добавления пользователя через API в Docker контейнере
"""

import requests
import sys
import getpass

def add_user(api_url, username, email, password):
    """Добавляет нового пользователя через API"""
    try:
        # Сначала проверяем, есть ли эндпоинт регистрации
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
            print(f"   Статус: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def test_login(api_url, username, password):
    """Тестирует вход в систему"""
    try:
        response = requests.post(
            f"{api_url}/auth/login",
            data={
                "username": username,
                "password": password
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Вход успешен!")
            print(f"   Token: {result['access_token'][:20]}...")
            print(f"   Username: {result['username']}")
            return result['access_token']
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            print(f"❌ Ошибка входа: {error_detail}")
            print(f"   Статус: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return None

def main():
    # Настройки API
    API_URL = "http://localhost:8000"  # URL API в Docker
    
    print("=== Добавление нового пользователя в Plaud (Docker) ===\n")
    
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
        print("Тестирую вход в систему...")
        
        # Тестируем вход
        token = test_login(API_URL, username, password)
        if token:
            print("\n🎉 Авторизация работает корректно!")
            print(f"Используйте токен: {token[:20]}...")
        else:
            print("\n⚠️  Пользователь создан, но вход не работает")
    else:
        print("\n💥 Не удалось добавить пользователя")

if __name__ == "__main__":
    main()

