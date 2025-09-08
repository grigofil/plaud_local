#!/usr/bin/env python3
"""
Упрощенный тест для проверки структуры проекта без зависимостей
"""

import os
import sys
from pathlib import Path

def check_file_structure():
    """Проверяет структуру файлов проекта"""
    print("📁 Проверка структуры файлов проекта...")
    
    required_files = [
        "main.py",
        "api_main.py", 
        "transcribe_server.py",
        "start.py",
        "docker-compose.yml",
        "requirements.txt",
        "README.md",
        "Dockerfile",
        "src/__init__.py",
        "src/api/__init__.py",
        "src/api/main.py",
        "src/api/dependencies.py",
        "src/config/__init__.py",
        "src/config/settings.py",
        "src/core/__init__.py",
        "src/core/main.py",
        "src/models/__init__.py",
        "src/models/user.py",
        "src/services/__init__.py",
        "src/services/transcription_service.py",
        "src/services/user_service.py",
        "src/utils/__init__.py",
        "src/utils/auth.py",
        "src/utils/database.py",
        "src/tasks/__init__.py",
        "src/tasks/transcribe.py",
        "src/tasks/summarize.py",
        "src/workers/__init__.py",
        "src/workers/transcribe_server.py"
    ]
    
    success = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - не найден")
            success = False
    
    return success

def check_directory_structure():
    """Проверяет структуру директорий"""
    print("\n📂 Проверка структуры директорий...")
    
    required_dirs = [
        "src",
        "src/api",
        "src/config", 
        "src/core",
        "src/models",
        "src/services",
        "src/utils",
        "src/tasks",
        "src/workers",
        "api/static"
    ]
    
    success = True
    for dir_path in required_dirs:
        if Path(dir_path).exists() and Path(dir_path).is_dir():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - не найдена")
            success = False
    
    return success

def check_python_syntax():
    """Проверяет синтаксис Python файлов"""
    print("\n🐍 Проверка синтаксиса Python файлов...")
    
    python_files = []
    for root, _, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    success = True
    for py_file in python_files:
        try:
            # Try to compile the file to check syntax
            with open(py_file, "r", encoding="utf-8") as f:
                compile(f.read(), str(py_file), "exec")
            print(f"✅ {py_file} - синтаксис OK")
        except SyntaxError as e:
            print(f"❌ {py_file} - ошибка синтаксиса: {e}")
            success = False
        except Exception as e:
            print(f"⚠️  {py_file} - предупреждение: {e}")
    
    return success

def check_import_paths():
    """Проверяет пути импортов в основных файлах"""
    print("\n🔗 Проверка путей импортов...")
    
    # Check that main files can resolve src imports
    main_files = ["main.py", "api_main.py", "transcribe_server.py"]
    
    success = True
    for main_file in main_files:
        try:
            with open(main_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "sys.path.insert(0, str(src_dir))" in content:
                    print(f"✅ {main_file} - пути импортов настроены правильно")
                else:
                    print(f"❌ {main_file} - не настроены пути импортов")
                    success = False
        except Exception as e:
            print(f"⚠️  {main_file} - ошибка чтения: {e}")
    
    return success

def main():
    print("=" * 60)
    print("🧪 Plaud Local - Тестирование структуры проекта")
    print("=" * 60)
    
    success = True
    
    # Run tests
    success &= check_file_structure()
    success &= check_directory_structure() 
    success &= check_python_syntax()
    success &= check_import_paths()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Структура проекта проверена успешно!")
        print("✅ Все файлы и директории на месте")
        print("✅ Синтаксис Python файлов корректен")
        print("✅ Пути импортов настроены правильно")
    else:
        print("❌ Обнаружены проблемы в структуре проекта")
        print("⚠️  Проверьте отсутствующие файлы или ошибки синтаксиса")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)