#!/usr/bin/env python3
"""
Тестовый скрипт для проверки авторизации в Plaud Local
"""

import requests
import sys
import os

def test_auth(base_url, token):
    """Тестирует авторизацию с заданным токеном"""
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"Тестирую {base_url} с токеном: {token[:8]}...")
    
    # Тест основного приложения
    try:
        response = requests.get(f"{base_url}/", headers=headers)
        if response.status_code == 200:
            print("✅ Основное приложение: OK")
        else:
            print(f"❌ Основное приложение: {response.status_code}")
    except Exception as e:
        print(f"❌ Основное приложение: ошибка соединения - {e}")
    
    # Тест API
    try:
        response = requests.get(f"{base_url}/auth/check", headers=headers)
        if response.status_code == 200:
            print("✅ API авторизация: OK")
        else:
            print(f"❌ API авторизация: {response.status_code}")
    except Exception as e:
        print(f"❌ API авторизация: ошибка соединения - {e}")

def main():
    if len(sys.argv) < 3:
        print("Использование: python test_auth.py <base_url> <token>")
        print("Пример: python test_auth.py http://localhost:8001 my_token_here")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    token = sys.argv[2]
    
    print("=" * 50)
    print("Тест авторизации Plaud Local")
    print("=" * 50)
    
    # Тестируем основное приложение
    test_auth(base_url, token)
    
    # Тестируем API (если это не API)
    if not base_url.endswith(':8000'):
        api_url = base_url.replace(':8001', ':8000')
        print(f"\nТестирую API на {api_url}:")
        test_auth(api_url, token)
    
    print("\n" + "=" * 50)
    print("Тест завершен")

if __name__ == "__main__":
    main()

