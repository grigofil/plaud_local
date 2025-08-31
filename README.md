# Plaud Local

Система для транскрипции аудио и создания саммари с использованием Whisper и DeepSeek.

## Авторизация

Все API эндпоинты защищены авторизацией. Для доступа необходимо передать API токен одним из способов:

### 1. Authorization Header
```
Authorization: Bearer your_token_here
```

### 2. X-API-Key Header
```
X-API-Key: your_token_here
```

## Настройка

1. Скопируйте `env.example` в `.env`
2. Сгенерируйте API токен:
   ```bash
   python generate_token.py
   ```
3. Укажите API токены в переменной `API_AUTH_TOKEN`:
   ```
   API_AUTH_TOKEN=your_secret_token_here,another_token_if_needed
   ```
4. Если оставить `API_AUTH_TOKEN` пустым - авторизация будет отключена

## Запуск

### Быстрый запуск (рекомендуется)
```bash
python start.py
```

### Ручной запуск
```bash
docker-compose up -d
```

## Доступные сервисы

- **Main App**: http://localhost:8001 (основное приложение)
- **API**: http://localhost:8000 (API для загрузки и обработки)
- **Redis**: localhost:6379

## API Endpoints

Все эндпоинты требуют авторизации:

### Основное приложение (порт 8001)
- `GET /` - главная страница
- `GET /health` - проверка здоровья
- `GET /info` - информация о системе
- `GET /auth/check` - проверка авторизации

### API (порт 8000)
- `POST /upload` - загрузка аудио файла
- `GET /status/{job_id}` - статус обработки
- `GET /result/{job_id}` - результат обработки
- `GET /healthz` - проверка здоровья API
- `GET /auth/check` - проверка авторизации

## Веб-клиент

Веб-интерфейс доступен по адресу http://localhost:8000/app
Для работы необходимо ввести API ключ в поле "API key".

## Тестирование

Для проверки работы авторизации используйте тестовый скрипт:

```bash
python test_auth.py http://localhost:8001 your_token_here
```

Этот скрипт проверит авторизацию как в основном приложении, так и в API.