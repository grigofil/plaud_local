#!/usr/bin/env python3
"""
Скрипт для получения токена авторизации
"""

import requests
import sys

def get_token(api_url, username, password):
    """Получает токен авторизации"""
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
            print(f"✅ Токен получен успешно!")
            print(f"Username: {result['username']}")
            print(f"Token: {result['access_token']}")
            print(f"Type: {result['token_type']}")
            return result['access_token']
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            print(f"❌ Ошибка получения токена: {error_detail}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return None

def test_token(api_url, token):
    """Тестирует токен"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{api_url}/auth/me", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Токен работает!")
            print(f"User ID: {result['user_id']}")
            print(f"Username: {result['username']}")
            print(f"Email: {result['email']}")
            return True
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            print(f"❌ Токен не работает: {error_detail}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Использование: python get_token.py <username> <password>")
        print("Пример: python get_token.py gg gg")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    API_URL = "http://localhost:8000"
    
    print("=== Получение токена авторизации ===\n")
    
    # Получаем токен
    token = get_token(API_URL, username, password)
    
    if token:
        print("\n=== Тестирование токена ===\n")
        test_token(API_URL, token)
    else:
        print("\n💥 Не удалось получить токен")

if __name__ == "__main__":
    main()

