#!/usr/bin/env python3
"""
Скрипт для быстрой настройки оптимальных параметров производительности
"""

import os
from pathlib import Path

def create_optimized_env():
    """Создает .env файл с оптимизированными настройками"""
    
    # Проверяем существование .env
    env_file = Path('.env')
    if env_file.exists():
        print("⚠️  Файл .env уже существует")
        overwrite = input("Перезаписать? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Операция отменена")
            return
    
    # Оптимизированные настройки
    optimized_settings = {
        'API_AUTH_TOKEN': 'your_secret_token_here',
        'REDIS_URL': 'redis://redis:6379',
        'DATA_DIR': '/data',
        'WHISPER_MODEL': 'small',
        'WHISPER_DEVICE': 'cpu',
        'WHISPER_COMPUTE_TYPE': 'int8',
        'WHISPER_FAST_MODE': 'true',
        'TRANSCRIBE_TIMEOUT': '600',
        'DEEPSEEK_API_KEY': 'your_deepseek_api_key_here',
        'DEEPSEEK_MODEL': 'deepseek-chat'
    }
    
    # Создаем .env файл
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# Оптимизированные настройки для быстрой обработки\n")
        f.write("# Создано автоматически скриптом optimize_settings.py\n\n")
        
        for key, value in optimized_settings.items():
            f.write(f"{key}={value}\n")
    
    print("✅ Файл .env создан с оптимизированными настройками")
    print("\n📋 Рекомендуемые настройки:")
    print(f"  WHISPER_MODEL: {optimized_settings['WHISPER_MODEL']} (быстрая модель)")
    print(f"  WHISPER_FAST_MODE: {optimized_settings['WHISPER_FAST_MODE']} (включен)")
    print(f"  TRANSCRIBE_TIMEOUT: {optimized_settings['TRANSCRIBE_TIMEOUT']} (10 минут)")
    
    print("\n⚠️  Не забудьте:")
    print("  1. Установить API_AUTH_TOKEN")
    print("  2. Установить DEEPSEEK_API_KEY (если нужен)")

def show_current_settings():
    """Показывает текущие настройки"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ Файл .env не найден")
        return
    
    print("📋 Текущие настройки (.env):")
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                print(f"  {line}")

def show_performance_tips():
    """Показывает советы по производительности"""
    print("\n🚀 Советы по производительности:")
    print("\n1. Для максимальной скорости:")
    print("   WHISPER_MODEL=tiny")
    print("   WHISPER_FAST_MODE=true")
    print("   TRANSCRIBE_TIMEOUT=300")
    
    print("\n2. Для баланса скорости и качества:")
    print("   WHISPER_MODEL=small")
    print("   WHISPER_FAST_MODE=true")
    print("   TRANSCRIBE_TIMEOUT=600")
    
    print("\n3. Для максимального качества:")
    print("   WHISPER_MODEL=medium")
    print("   WHISPER_FAST_MODE=false")
    print("   TRANSCRIBE_TIMEOUT=1200")
    
    print("\n4. Для GPU ускорения:")
    print("   WHISPER_DEVICE=cuda")
    print("   WHISPER_COMPUTE_TYPE=float16")

def main():
    """Главная функция"""
    print("=" * 50)
    print("⚡ Оптимизация настроек Plaud Local")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. Создать оптимизированный .env")
        print("2. Показать текущие настройки")
        print("3. Советы по производительности")
        print("0. Выход")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == "1":
            create_optimized_env()
        elif choice == "2":
            show_current_settings()
        elif choice == "3":
            show_performance_tips()
        elif choice == "0":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
