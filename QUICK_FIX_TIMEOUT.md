# 🚨 Быстрое решение проблемы с таймаутом

## Проблема
```
Task exceeded maximum timeout value (180 seconds)
```

## 🚀 Быстрое решение (5 минут)

### 1. Остановите сервисы
```bash
docker-compose down
```

### 2. Создайте оптимизированный .env
```bash
python optimize_settings.py
```
Выберите опцию 1 - "Создать оптимизированный .env"

### 3. Настройте API токен
Отредактируйте `.env` файл:
```bash
# Замените на ваш токен
API_AUTH_TOKEN=your_actual_token_here
```

### 4. Запустите сервисы
```bash
docker-compose up -d
```

## ⚡ Что изменилось

- **Таймаут увеличен**: с 180 секунд до 600 секунд (10 минут)
- **Быстрый режим включен**: `WHISPER_FAST_MODE=true`
- **Модель оптимизирована**: `WHISPER_MODEL=small`

## 🔧 Дополнительные настройки

### Для очень длинных файлов (>30 минут)
```bash
TRANSCRIBE_TIMEOUT=1800  # 30 минут
```

### Для максимальной скорости
```bash
WHISPER_MODEL=tiny
TRANSCRIBE_TIMEOUT=300   # 5 минут
```

### Для GPU ускорения
```bash
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```

## 📊 Мониторинг

Проверьте статус задач:
```bash
python manage_jobs.py
```

## ❓ Если проблема остается

1. **Разбейте длинные файлы** на части по 10-15 минут
2. **Используйте меньшую модель**: `WHISPER_MODEL=base`
3. **Проверьте логи**: `docker-compose logs worker_transcribe`

## 📞 Поддержка

Если ничего не помогает, создайте issue с:
- Размером аудиофайла
- Длительностью аудио
- Логами ошибок
- Версией Docker
