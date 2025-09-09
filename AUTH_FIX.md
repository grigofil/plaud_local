# Решение проблемы с авторизацией в Plaud Local

## Проблема
Не удавалось авторизоваться под пользователем в системе Plaud Local.

## Причина
Основная проблема была в несовместимости пакета `jose` версии 1.0.0 с Python 3.10. Этот пакет содержал устаревший синтаксис Python 2, который не поддерживается в Python 3.10+.

## Решение

### 1. Удаление несовместимого пакета
```bash
pip uninstall jose -y
```

### 2. Установка правильного пакета
```bash
pip install python-jose[cryptography]
```

### 3. Создание пользователя через API
Вместо прямого добавления в базу данных, используйте API эндпоинт `/auth/register`:

```bash
python add_user_docker.py
```

## Как работает авторизация

### Эндпоинты API
- **POST /auth/register** - Регистрация нового пользователя
- **POST /auth/login** - Вход в систему (получение JWT токена)
- **GET /auth/me** - Получение информации о текущем пользователе
- **GET /auth/check** - Проверка авторизации

### Процесс авторизации
1. **Регистрация**: Создание пользователя с хешированным паролем
2. **Вход**: Проверка учетных данных и получение JWT токена
3. **Использование**: Передача токена в заголовке `Authorization: Bearer <token>`

### Пример использования
```bash
# Регистрация
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=myuser&email=myuser@example.com&password=mypassword"

# Вход
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=myuser&password=mypassword"

# Использование защищенного API
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer <your_jwt_token>"
```

## Тестирование

### Веб-интерфейс
Откройте файл `test_auth.html` в браузере для интерактивного тестирования:
```bash
start test_auth.html
```

### Командная строка
Используйте скрипт `get_token.py` для получения токена:
```bash
python get_token.py <username> <password>
```

## Структура базы данных

### Таблица users
- `id` - Уникальный идентификатор
- `username` - Имя пользователя (уникальное)
- `email` - Email (уникальный)
- `hashed_password` - Хешированный пароль
- `is_active` - Статус активности
- `created_at` - Дата создания
- `updated_at` - Дата обновления

## Безопасность

### JWT токены
- Алгоритм: HS256
- Время жизни: 30 минут
- Секретный ключ: настраивается через переменную окружения `JWT_SECRET_KEY`

### Хеширование паролей
- Алгоритм: bcrypt
- Автоматическое хеширование при создании пользователя
- Безопасная проверка при входе

## Устранение неполадок

### Проверка сервисов
```bash
docker-compose ps
```

### Проверка логов API
```bash
docker logs plaud_local-api-1
```

### Проверка базы данных
```bash
docker exec plaud_local-api-1 ls -la plaud.db
```

## Заключение
После исправления проблемы с пакетом `jose` и использования правильного API для создания пользователей, система авторизации работает корректно. Все эндпоинты авторизации функционируют как ожидается, JWT токены генерируются и проверяются правильно.

