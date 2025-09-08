# Plaud Local

Система для транскрипции аудио и создания саммари с использованием Whisper и DeepSeek.

## 🚀 Новая модульная архитектура

Проект был полностью рефакторирован с созданием модульной структуры, следующей принципам SOLID. Подробное описание архитектуры смотрите в [ARCHITECTURE.md](ARCHITECTURE.md).

### Ключевые улучшения:
- **Модульная структура** с четким разделением ответственности
- **Низкая связность** между компонентами  
- **Высокая связанность** внутри модулей
- **Улучшенная тестируемость** и поддерживаемость
- **Готовность к масштабированию**

## 📁 Структура проекта

```
plaud_local/
├── src/                    # Основной исходный код
│   ├── api/               # API слой (FastAPI endpoints)
│   ├── config/            # Конфигурация приложения
│   ├── core/              # Основное ядро приложения
│   ├── models/            # Модели данных (SQLAlchemy)
│   ├── services/          # Бизнес-логика и сервисы
│   ├── tasks/             # Фоновые задачи (RQ workers)
│   ├── utils/             # Вспомогательные утилиты
│   └── workers/           # HTTP воркеры
├── api/static/            # Веб-клиент (статичные файлы)
├── main.py               # Основное приложение (порт 8001)
├── api_main.py           # API сервер (порт 8000)
├── transcribe_server.py  # Сервер транскрипции (порт 8002)
├── start.py              # Скрипт быстрого запуска
└── docker-compose.yml    # Docker компоновка
```

## Авторизация

Все API эндпоинты защищены авторизацией. Для доступа необходимо передать API токен одним из способов:

### 1. Authorization Header (JWT)
```
Authorization: Bearer your_jwt_token_here
```

### 2. X-API-Key Header (статичный токен)
```
X-API-Key: your_static_token_here
```

## Настройка

1. Скопируйте `env.example` в `.env`
2. Укажите API токены в переменной `API_AUTH_TOKEN`:
   ```
   API_AUTH_TOKEN=your_secret_token_here,another_token_if_needed
   ```
3. Если оставить `API_AUTH_TOKEN` пустым - авторизация будет отключена

### Настройка производительности и таймаута

Для оптимизации производительности транскрипции можно настроить следующие параметры:

- **TRANSCRIBE_TIMEOUT** - таймаут для задач транскрипции в секундах (по умолчанию 600 = 10 минут)
- **WHISPER_FAST_MODE** - быстрый режим с использованием меньшей модели (true/false)
- **WHISPER_MODEL** - размер модели Whisper (tiny, base, small, medium, large, large-v2)
- **WHISPER_DEVICE** - устройство для обработки (cpu, cuda)
- **WHISPER_COMPUTE_TYPE** - тип вычислений (int8, float16, float32)

Пример настройки для быстрой обработки:
```
WHISPER_FAST_MODE=true
WHISPER_MODEL=small
TRANSCRIBE_TIMEOUT=300
```

## Локальный запуск

### Быстрый запуск (рекомендуется)
```bash
python start.py
```

### Ручной запуск
```bash
docker-compose up -d
```

### Настройка доступа с других устройств

По умолчанию сервисы доступны только с локального компьютера. Для доступа с других устройств в сети:

#### 1. Изменение IP адреса в docker-compose.yml

Отредактируйте файл `docker-compose.yml` и измените порты:

```yaml
services:
  main:
    ports:
      - "0.0.0.0:8001:8001"  # Доступно с любого IP
  api:
    ports:
      - "0.0.0.0:8000:8000"  # Доступно с любого IP
  worker_transcribe:
    ports:
      - "0.0.0.0:8002:8002"  # Доступно с любого IP
```

#### 2. Настройка переменных окружения

В файле `.env` добавьте или измените:

```env
# Для доступа с других устройств в сети
REDIS_URL=redis://YOUR_LOCAL_IP:6379
TRANSCRIBE_SERVER_URL=http://YOUR_LOCAL_IP:8002
```

Замените `YOUR_LOCAL_IP` на ваш локальный IP адрес (например, `192.168.1.100`).

#### 3. Определение локального IP адреса

**Windows:**
```cmd
ipconfig
```

**Linux/macOS:**
```bash
ip addr show
# или
ifconfig
```

#### 4. Доступ к сервисам

После настройки сервисы будут доступны по адресам:
- **Основное приложение**: `http://YOUR_LOCAL_IP:8001`
- **API**: `http://YOUR_LOCAL_IP:8000`
- **Веб-клиент**: `http://YOUR_LOCAL_IP:8000/app`
- **Сервер транскрибации**: `http://YOUR_LOCAL_IP:8002`

### Настройка файрвола

Убедитесь, что порты 8000, 8001, 8002 открыты в файрволе:

**Windows:**
```cmd
# Открыть порт 8000
netsh advfirewall firewall add rule name="Plaud API" dir=in action=allow protocol=TCP localport=8000

# Открыть порт 8001
netsh advfirewall firewall add rule name="Plaud Main" dir=in action=allow protocol=TCP localport=8001

# Открыть порт 8002
netsh advfirewall firewall add rule name="Plaud Transcribe" dir=in action=allow protocol=TCP localport=8002
```

**Linux (ufw):**
```bash
sudo ufw allow 8000
sudo ufw allow 8001
sudo ufw allow 8002
```

**Linux (iptables):**
```bash
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8002 -j ACCEPT
```

## Доступные сервисы

- **Main App**: http://localhost:8001 (основное приложение)
- **API**: http://localhost:8000 (API для загрузки и обработки)
- **Transcribe Server**: http://localhost:8002 (сервер транскрипции)
- **Redis**: localhost:6379
- **Web Client**: http://localhost:8000/app (веб-интерфейс)

## API Endpoints

Все эндпоинты требуют авторизации:

### Основное приложение (порт 8001)
- `GET /` - главная страница
- `GET /health` - проверка здоровья
- `GET /info` - информация о системе
- `GET /auth/check` - проверка авторизации

### API (порт 8000)
- `POST /auth/register` - регистрация пользователя
- `POST /auth/login` - аутентификация пользователя
- `GET /auth/me` - информация о текущем пользователе
- `GET /auth/check` - проверка авторизации
- `POST /upload` - загрузка аудио файла
- `GET /status/{job_id}` - статус обработки
- `GET /result/{job_id}` - результат обработки
- `GET /healthz` - проверка здоровья API
- `GET /history` - история задач
- `DELETE /history/{job_id}` - удаление задачи

### Управление пользователями (только для администраторов)
- `GET /users` - список всех пользователей
- `DELETE /users/{user_id}` - удаление пользователя
- `PATCH /users/{user_id}/deactivate` - деактивация пользователя
- `PATCH /users/{user_id}/activate` - активация пользователя
- `PATCH /users/{user_id}/make-admin` - назначение администратором
- `PATCH /users/{user_id}/remove-admin` - снятие прав администратора

## Веб-клиент

Веб-интерфейс доступен по адресу http://localhost:8000/app
Для работы необходимо ввести API ключ в поле "API key".

### Регистрация и авторизация

Система поддерживает регистрацию пользователей и JWT авторизацию:

1. **Регистрация**: `POST /auth/register` - создание нового пользователя
2. **Вход**: `POST /auth/login` - получение JWT токена
3. **Проверка**: `GET /auth/me` - информация о текущем пользователе

### Примеры использования

#### Регистрация пользователя
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&email=test@example.com&password=password123"
```

#### Вход в систему
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

#### Загрузка аудио файла
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@audio.wav" \
  -F "language=ru"
```

#### Проверка статуса задачи
```bash
curl -X GET "http://localhost:8000/status/JOB_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Получение результата
```bash
curl -X GET "http://localhost:8000/result/JOB_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Решение проблем

### Проблемы с доступом к сервисам

#### Сервисы недоступны с других устройств

**Проблема**: Сервисы работают только на localhost, недоступны с других устройств в сети.

**Решение**:
1. Убедитесь, что в `docker-compose.yml` порты настроены как `"0.0.0.0:PORT:PORT"`
2. Проверьте, что файрвол не блокирует порты 8000, 8001, 8002
3. Убедитесь, что устройства находятся в одной сети
4. Проверьте IP адрес командой `ipconfig` (Windows) или `ip addr show` (Linux)

#### Ошибка "Connection refused"

**Проблема**: При попытке доступа к сервисам получаете ошибку подключения.

**Решение**:
1. Проверьте, что Docker контейнеры запущены: `docker-compose ps`
2. Проверьте логи: `docker-compose logs`
3. Убедитесь, что порты не заняты другими приложениями
4. Перезапустите сервисы: `docker-compose restart`

#### Проблемы с авторизацией

**Проблема**: API возвращает ошибку 401 Unauthorized.

**Решение**:
1. Проверьте, что в `.env` файле указан `API_AUTH_TOKEN`
2. Убедитесь, что токен передается в заголовке `Authorization: Bearer <token>` или `X-API-Key: <token>`

### Ошибка таймаута транскрипции

Если вы получаете ошибку таймаута транскрипции, это означает, что аудиофайл слишком длинный для обработки.

**Решения:**
1. **Увеличить таймаут** - установите `TRANSCRIBE_TIMEOUT=1200` (20 минут) или больше
2. **Включить быстрый режим** - установите `WHISPER_FAST_MODE=true`
3. **Использовать меньшую модель** - установите `WHISPER_MODEL=small` или `WHISPER_MODEL=base`
4. **Разбить длинные файлы** - загружайте аудио частями по 10-15 минут

**Пример настройки для длинных файлов:**
```
TRANSCRIBE_TIMEOUT=1200
WHISPER_FAST_MODE=true
WHISPER_MODEL=small
```

### Медленная обработка

Для ускорения обработки:
- Используйте GPU: `WHISPER_DEVICE=cuda`
- Включите быстрый режим: `WHISPER_FAST_MODE=true`
- Выберите меньшую модель: `WHISPER_MODEL=base` или `WHISPER_MODEL=small`

## Дополнительные настройки

### Изменение портов

Если стандартные порты заняты, измените их в `docker-compose.yml`:

```yaml
services:
  main:
    ports:
      - "0.0.0.0:9001:8001"  # Изменить внешний порт на 9001
  api:
    ports:
      - "0.0.0.0:9000:8000"  # Изменить внешний порт на 9000
  worker_transcribe:
    ports:
      - "0.0.0.0:9002:8002"  # Изменить внешний порт на 9002
```

### Настройка для продакшена

Для продакшена рекомендуется:

1. **Изменить JWT секрет**:
   ```env
   JWT_SECRET_KEY=your-very-secure-secret-key-here
   ```

2. **Настроить базу данных PostgreSQL**:
   ```env
   DATABASE_URL=postgresql://user:password@postgres:5432/plaud
   ```

3. **Ограничить CORS**:
   В `src/api/main.py` измените:
   ```python
   allow_origins=["https://yourdomain.com"]  # Вместо ["*"]
   ```

4. **Настроить SSL/HTTPS** через reverse proxy (nginx, traefik)

### Мониторинг и логи

Для мониторинга работы системы:

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f api
docker-compose logs -f main
docker-compose logs -f worker_transcribe

# Статистика использования ресурсов
docker stats
```

### Резервное копирование

Для резервного копирования данных:

```bash
# Создание бэкапа базы данных
docker-compose exec api python -c "
import sqlite3
import shutil
shutil.copy('/data/plaud.db', '/data/plaud_backup_$(date +%Y%m%d).db')
"

# Создание архива всех данных
tar -czf plaud_backup_$(date +%Y%m%d).tar.gz data/
```

## 📚 Дополнительная документация

- [ARCHITECTURE.md](ARCHITECTURE.md) - подробное описание архитектуры проекта
- Исходный код с комментариями и документацией

## 🛠️ Разработка

Проект использует современную модульную архитектуру с четким разделением ответственности:

- **Модели** (`src/models/`) - данные и ORM
- **Сервисы** (`src/services/`) - бизнес-логика
- **API** (`src/api/`) - HTTP endpoints
- **Утилиты** (`src/utils/`) - вспомогательные функции
- **Задачи** (`src/tasks/`) - фоновые процессы

Для добавления нового функционала следуйте принципам SOLID и размещайте код в соответствующих модулях.