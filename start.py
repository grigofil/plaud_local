#!/usr/bin/env python3
"""
Скрипт для быстрого запуска Plaud Local с проверкой настроек
"""

import os
import subprocess
import sys
from pathlib import Path

def check_env():
    """Проверяет настройки окружения"""
    print("🔍 Проверка настроек окружения...")
    
    # Проверяем .env файл
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ Файл .env не найден!")
        print("   Скопируйте env.example в .env и настройте API_AUTH_TOKEN")
        return False
    
    # Проверяем API_AUTH_TOKEN
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'API_AUTH_TOKEN=' in content:
            print("✅ API_AUTH_TOKEN найден в .env")
        else:
            print("⚠️  API_AUTH_TOKEN не найден в .env")
            print("   Авторизация будет отключена")
    
    return True

def check_docker():
    """Проверяет доступность Docker"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker доступен")
            return True
        else:
            print("❌ Docker недоступен")
            return False
    except FileNotFoundError:
        print("❌ Docker не установлен")
        return False

def check_docker_compose():
    """Проверяет доступность docker-compose"""
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose доступен")
            return True
        else:
            print("❌ Docker Compose недоступен")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose не установлен")
        return False

def start_services():
    """Запускает сервисы"""
    print("\n🚀 Запуск сервисов...")
    try:
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        print("✅ Сервисы запущены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска сервисов: {e}")
        return False

def show_status():
    """Показывает статус сервисов"""
    print("\n📊 Статус сервисов:")
    try:
        subprocess.run(['docker-compose', 'ps'], check=True)
    except subprocess.CalledProcessError:
        print("Не удалось получить статус сервисов")

def main():
    print("=" * 50)
    print("🚀 Plaud Local - Быстрый запуск")
    print("=" * 50)
    
    # Проверяем окружение
    if not check_env():
        print("\n❌ Настройка не завершена. Создайте .env файл.")
        sys.exit(1)
    
    # Проверяем Docker
    if not check_docker():
        print("\n❌ Docker недоступен. Установите Docker.")
        sys.exit(1)
    
    if not check_docker_compose():
        print("\n❌ Docker Compose недоступен. Установите Docker Compose.")
        sys.exit(1)
    
    # Запускаем сервисы
    if start_services():
        show_status()
        print("\n🎉 Plaud Local запущен!")
        print("\n📱 Доступные сервисы:")
        print("   • Основное приложение: http://localhost:8001")
        print("   • API: http://localhost:8000")
        print("   • Веб-клиент: http://localhost:8000/app")
        print("\n🔑 Для тестирования авторизации:")
        print("   python test_auth.py http://localhost:8001 your_token_here")
    else:
        print("\n❌ Не удалось запустить сервисы")
        sys.exit(1)

if __name__ == "__main__":
    main()

