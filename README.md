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

## Тестирование

Для проверки работы авторизации используйте тестовый скрипт:

```bash
python test_auth.py http://localhost:8001 your_token_here
```

Этот скрипт проверит авторизацию как в основном приложении, так и в API.

### Управление задачами

Для мониторинга и управления задачами транскрипции используйте скрипт:

```bash
python manage_jobs.py
```

Этот скрипт позволяет:
- Просматривать статистику очередей
- Анализировать детали задач
- Повторять неудачные задачи
- Очищать неудачные задачи
- Просматривать файлы задач

### Оптимизация настроек

Для быстрой настройки оптимальных параметров производительности:

```bash
python optimize_settings.py
```

Этот скрипт поможет:
- Создать оптимизированный .env файл
- Просмотреть текущие настройки
- Получить советы по производительности

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
2. Убедитесь, что токен передается в заголовке `Authorization: Bearer <token>`
3. Для тестирования используйте: `python test_auth.py http://localhost:8001 your_token`

### Ошибка таймаута транскрипции

Если вы получаете ошибку "Task exceeded maximum timeout value (180 seconds)", это означает, что аудиофайл слишком длинный для обработки в стандартном таймауте.

**🚨 Для быстрого решения (5 минут) смотрите [QUICK_FIX_TIMEOUT.md](QUICK_FIX_TIMEOUT.md)**

**Решения:**

1. **Увеличить таймаут** - установите `TRANSCRIBE_TIMEOUT=600` (10 минут) или больше
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
   В `api/main.py` измените:
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