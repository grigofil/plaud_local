#!/usr/bin/env python3
"""
Тестовый скрипт для проверки входа в систему
"""

import requests
import json

def test_login():
    """Тестирует вход в систему"""
    try:
        print("🔐 Тестируем вход в систему...")
        
        # Данные для входа
        login_data = {
            "username": "qwe",
            "password": "qwe"
        }
        
        # Отправляем запрос на вход
        response = requests.post(
            "http://localhost:8000/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"📊 Статус ответа: {response.status_code}")
        print(f"📋 Заголовки: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Вход успешен!")
            print(f"   Токен: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   Пользователь: {data.get('username', 'N/A')}")
            print(f"   ID: {data.get('user_id', 'N/A')}")
            
            # Тестируем получение информации о пользователе
            token = data.get('access_token')
            if token:
                print("\n👤 Получаем информацию о пользователе...")
                user_info_response = requests.get(
                    "http://localhost:8000/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if user_info_response.status_code == 200:
                    user_info = user_info_response.json()
                    print("✅ Информация о пользователе получена!")
                    print(f"   Username: {user_info.get('username')}")
                    print(f"   Email: {user_info.get('email')}")
                    print(f"   Is Active: {user_info.get('is_active')}")
                    print(f"   Is Admin: {user_info.get('is_admin')}")
                else:
                    print(f"❌ Ошибка получения информации о пользователе: {user_info_response.status_code}")
                    print(f"   Ответ: {user_info_response.text}")
            
            return True
        else:
            print(f"❌ Ошибка входа: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при тестировании: {e}")
        return False

def test_users_endpoint():
    """Тестирует endpoint управления пользователями"""
    try:
        print("\n👥 Тестируем endpoint управления пользователями...")
        
        # Сначала получаем токен
        login_data = {"username": "qwe", "password": "qwe"}
        login_response = requests.post(
            "http://localhost:8000/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print("❌ Не удалось войти в систему для тестирования")
            return False
        
        token = login_response.json().get('access_token')
        
        # Тестируем endpoint пользователей
        users_response = requests.get(
            "http://localhost:8000/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"📊 Статус ответа /users: {users_response.status_code}")
        
        if users_response.status_code == 200:
            users_data = users_response.json()
            print("✅ Список пользователей получен!")
            print(f"   Найдено пользователей: {len(users_data.get('users', []))}")
            
            for user in users_data.get('users', []):
                print(f"   - {user.get('username')} (ID: {user.get('id')}, Admin: {user.get('is_admin')})")
            
            return True
        else:
            print(f"❌ Ошибка получения списка пользователей: {users_response.status_code}")
            print(f"   Ответ: {users_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при тестировании пользователей: {e}")
        return False

if __name__ == "__main__":
    print("=== Тестирование API Plaud ===\n")
    
    # Тестируем вход
    login_success = test_login()
    
    if login_success:
        # Тестируем endpoint пользователей
        test_users_endpoint()
    
    print("\n🎉 Тестирование завершено!")
