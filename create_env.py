#!/usr/bin/env python3
"""
Скрипт для создания файла .env с правильной кодировкой UTF-8
"""

env_content = """# Настройки авторизации
# Пустой токен отключает авторизацию
API_AUTH_TOKEN=

# Настройки Redis
REDIS_URL=redis://redis:6379

# Настройки данных
DATA_DIR=/data

# Настройки Whisper
WHISPER_MODEL=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

# Настройки DeepSeek
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
"""

try:
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✅ Файл .env создан успешно с кодировкой UTF-8")
    print("📝 Содержимое файла:")
    print("-" * 40)
    print(env_content)
    print("-" * 40)
except Exception as e:
    print(f"❌ Ошибка при создании файла .env: {e}")

