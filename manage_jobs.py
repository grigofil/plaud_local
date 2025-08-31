#!/usr/bin/env python3
"""
Скрипт для мониторинга и управления задачами транскрипции
"""

import os
import json
import time
from pathlib import Path
from redis import Redis
from rq import Queue, Worker, Connection
from rq.job import Job

# Настройки
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))

def get_redis_connection():
    """Получает соединение с Redis"""
    return Redis.from_url(REDIS_URL)

def get_queue_stats():
    """Получает статистику очередей"""
    r = get_redis_connection()
    
    # Статистика по задачам
    asr_queue = Queue("asr", connection=r)
    sum_queue = Queue("sum", connection=r)
    
    print("📊 Статистика очередей:")
    print(f"  ASR (транскрипция): {len(asr_queue)} задач")
    print(f"  SUM (суммаризация): {len(sum_queue)} задач")
    
    # Активные воркеры
    workers = Worker.all(connection=r)
    print(f"  Активных воркеров: {len(workers)}")
    
    for worker in workers:
        if worker.state == 'busy':
            current_job = worker.get_current_job()
            if current_job:
                print(f"    {worker.name}: {current_job.func_name} (ID: {current_job.id})")
        else:
            print(f"    {worker.name}: {worker.state}")

def show_job_details(job_id):
    """Показывает детали конкретной задачи"""
    r = get_redis_connection()
    job = Job.fetch(job_id, connection=r)
    
    print(f"\n🔍 Детали задачи {job_id}:")
    print(f"  Статус: {job.get_status()}")
    print(f"  Функция: {job.func_name}")
    print(f"  Аргументы: {job.args}")
    print(f"  Создана: {job.created_at}")
    print(f"  Начата: {job.started_at}")
    print(f"  Завершена: {job.ended_at}")
    
    if job.is_failed:
        print(f"  Ошибка: {job.exc_info}")
    
    if job.result:
        print(f"  Результат: {job.result}")

def show_failed_jobs():
    """Показывает неудачные задачи"""
    r = get_redis_connection()
    failed_jobs = Job.fetch_many(
        r.smembers('rq:queue:failed'), 
        connection=r
    )
    
    if not failed_jobs:
        print("✅ Нет неудачных задач")
        return
    
    print(f"\n❌ Неудачные задачи ({len(failed_jobs)}):")
    for job in failed_jobs:
        if job:
            print(f"  {job.id}: {job.func_name} - {job.exc_info}")

def retry_failed_job(job_id):
    """Повторяет неудачную задачу"""
    r = get_redis_connection()
    job = Job.fetch(job_id, connection=r)
    
    if not job.is_failed:
        print(f"❌ Задача {job_id} не является неудачной")
        return
    
    print(f"🔄 Повторяю задачу {job_id}...")
    job.requeue()
    print(f"✅ Задача {job_id} добавлена в очередь повторно")

def clear_failed_jobs():
    """Очищает все неудачные задачи"""
    r = get_redis_connection()
    failed_jobs = r.smembers('rq:queue:failed')
    
    if not failed_jobs:
        print("✅ Нет неудачных задач для очистки")
        return
    
    print(f"🗑️  Очищаю {len(failed_jobs)} неудачных задач...")
    for job_id in failed_jobs:
        job = Job.fetch(job_id.decode(), connection=r)
        job.delete()
    
    print("✅ Все неудачные задачи очищены")

def show_job_files(job_id):
    """Показывает файлы задачи"""
    job_dir = DATA_DIR / "jobs" / job_id
    
    if not job_dir.exists():
        print(f"❌ Директория задачи {job_id} не найдена")
        return
    
    print(f"\n📁 Файлы задачи {job_id}:")
    for file_path in job_dir.rglob("*"):
        if file_path.is_file():
            size = file_path.stat().st_size
            print(f"  {file_path.name}: {size} байт")

def main():
    """Главная функция"""
    print("=" * 50)
    print("🔧 Управление задачами Plaud Local")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. Показать статистику очередей")
        print("2. Показать детали задачи")
        print("3. Показать неудачные задачи")
        print("4. Повторить неудачную задачу")
        print("5. Очистить неудачные задачи")
        print("6. Показать файлы задачи")
        print("0. Выход")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == "1":
            get_queue_stats()
        elif choice == "2":
            job_id = input("Введите ID задачи: ").strip()
            if job_id:
                show_job_details(job_id)
        elif choice == "3":
            show_failed_jobs()
        elif choice == "4":
            job_id = input("Введите ID задачи для повтора: ").strip()
            if job_id:
                retry_failed_job(job_id)
        elif choice == "5":
            confirm = input("Вы уверены? (y/N): ").strip().lower()
            if confirm == 'y':
                clear_failed_jobs()
        elif choice == "6":
            job_id = input("Введите ID задачи: ").strip()
            if job_id:
                show_job_files(job_id)
        elif choice == "0":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
