# Управление пользователями в Plaud

В системе Plaud есть несколько способов добавить нового пользователя.

## Способ 1: Через веб-интерфейс (рекомендуется)

1. Откройте браузер и перейдите по адресу: `http://localhost:8000/register.html`
2. Заполните форму регистрации:
   - Имя пользователя (уникальное)
   - Email (уникальный)
   - Пароль (минимум 6 символов)
   - Подтверждение пароля
3. Нажмите "Зарегистрироваться"
4. После успешной регистрации вы можете войти в систему

## Способ 2: Через Python скрипт (API)

Используйте скрипт `add_user.py`:

```bash
python add_user.py
```

Скрипт запросит:
- Имя пользователя
- Email
- Пароль
- Подтверждение пароля

## Способ 3: Через Python скрипт (прямое обращение к БД)

Используйте скрипт `add_user_db.py`:

```bash
python add_user_db.py
```

Этот скрипт добавляет пользователя напрямую в базу данных.

## Способ 4: Через curl

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=новый_пользователь&email=user@example.com&password=пароль123"
```

## Способ 5: Через Postman

1. Создайте POST запрос на `http://localhost:8000/auth/register`
2. Установите Content-Type: `application/x-www-form-urlencoded`
3. Добавьте параметры в Body:
   - username: имя_пользователя
   - email: email@example.com
   - password: пароль

## Вход в систему

После регистрации используйте endpoint `/auth/login` для входа:

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=имя_пользователя&password=пароль"
```

## Структура пользователя

Каждый пользователь имеет следующие поля:
- `id` - уникальный идентификатор
- `username` - уникальное имя пользователя
- `email` - уникальный email
- `hashed_password` - хешированный пароль
- `is_active` - активен ли пользователь
- `created_at` - дата создания
- `updated_at` - дата последнего обновления

## Безопасность

- Пароли хешируются с использованием bcrypt
- JWT токены используются для аутентификации
- Токены действительны 30 минут
- Все API endpoints (кроме регистрации и входа) требуют аутентификации

## Устранение неполадок

### Ошибка "Пользователь уже существует"
- Проверьте, что имя пользователя и email уникальны
- Используйте другой username или email

### Ошибка соединения
- Убедитесь, что API сервер запущен
- Проверьте правильность URL (по умолчанию http://localhost:8000)

### Ошибка базы данных
- Проверьте, что база данных доступна
- Убедитесь, что таблица `users` создана

## Примеры использования

### Добавление пользователя через Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/auth/register",
    data={
        "username": "test_user",
        "email": "test@example.com",
        "password": "secure_password123"
    }
)

if response.status_code == 200:
    print("Пользователь успешно добавлен!")
    print(response.json())
else:
    print("Ошибка:", response.json()["detail"])
```

### Получение информации о пользователе

```python
import requests

# Сначала войдите в систему
login_response = requests.post(
    "http://localhost:8000/auth/login",
    data={
        "username": "test_user",
        "password": "secure_password123"
    }
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    
    # Получите информацию о пользователе
    user_info = requests.get(
        "http://localhost:8000/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if user_info.status_code == 200:
        print("Информация о пользователе:", user_info.json())
```
