# Инструкция по сборке Android-приложения Plaud Local

## ✅ Проверка готовности

Все необходимые файлы созданы и настроены:

### 📁 Структура проекта:
```
android-app/
├── build.gradle                    # Корневой файл конфигурации Gradle
├── settings.gradle                 # Настройки проекта
├── gradle.properties              # Свойства Gradle
├── gradlew                        # Gradle Wrapper (Unix)
├── gradlew.bat                    # Gradle Wrapper (Windows)
├── AndroidManifest.xml            # Манифест приложения
├── gradle/wrapper/
│   ├── gradle-wrapper.jar         # Gradle Wrapper JAR
│   └── gradle-wrapper.properties  # Свойства Wrapper
└── app/
    ├── build.gradle               # Конфигурация модуля приложения
    ├── proguard-rules.pro         # Правила обфускации
    └── src/main/
        ├── java/com/example/plaudlocal/
        │   └── MainActivity.kt     # Основной код приложения
        └── res/                    # Ресурсы приложения
            ├── drawable/
            ├── layout/
            ├── mipmap-*/
            ├── values/
            └── xml/
```

## 🔧 Требования

### Обязательные:
- **Java Development Kit (JDK) 8 или выше**
- **Android SDK** (через Android Studio или отдельно)
- **Android Build Tools 33.0.0+**

### Рекомендуемые:
- **Android Studio** (для удобной разработки)
- **Git** (для версионного контроля)

## 🚀 Способы сборки

### 1. Через Android Studio (Рекомендуется)

1. **Откройте Android Studio**
2. **File → Open** → выберите папку `android-app`
3. **Дождитесь синхронизации Gradle** (может занять несколько минут)
4. **Build → Build Bundle(s) / APK(s) → Build APK(s)**
5. **APK будет создан в:** `app/build/outputs/apk/debug/app-debug.apk`

### 2. Через командную строку

#### Windows (PowerShell/CMD):
```powershell
cd android-app
.\gradlew.bat assembleDebug
```

#### Linux/macOS:
```bash
cd android-app
./gradlew assembleDebug
```

### 3. Установка на устройство

#### Через Android Studio:
1. Подключите Android-устройство или запустите эмулятор
2. **Run → Run 'app'** или нажмите зеленую кнопку ▶️

#### Через командную строку:
```powershell
# Windows
.\gradlew.bat installDebug

# Linux/macOS
./gradlew installDebug
```

## 📱 Настройка приложения

### 1. Настройка API сервера:
- По умолчанию: `http://10.0.2.2:8000` (для эмулятора)
- Для реального устройства: `http://IP_АДРЕС_КОМПЬЮТЕРА:8000`

### 2. Авторизация:
Приложение теперь поддерживает авторизацию по логину и паролю:
- **Логин/пароль** - как на веб-сайте
- **JWT токены** - автоматически сохраняются
- **Автоматический вход** - при перезапуске приложения

Для создания пользователя используйте веб-интерфейс или API:
```bash
# Создание пользователя через API
curl -X POST "http://localhost:8000/auth/register" \
  -F "username=testuser" \
  -F "email=test@example.com" \
  -F "password=testpass"
```

### 3. Разрешения:
Приложение запрашивает следующие разрешения:
- `INTERNET` - для сетевых запросов
- `ACCESS_NETWORK_STATE` - для проверки состояния сети
- `READ_EXTERNAL_STORAGE` - для чтения аудиофайлов
- `RECORD_AUDIO` - для записи звука с микрофона
- `WRITE_EXTERNAL_STORAGE` - для сохранения записанных файлов

## 🔍 Проверка сборки

### Проверка APK:
```powershell
# Проверить содержимое APK
.\gradlew.bat assembleDebug --info

# APK будет в:
# app/build/outputs/apk/debug/app-debug.apk
```

### Проверка установки:
```powershell
# Установить на подключенное устройство
.\gradlew.bat installDebug

# Проверить установленные приложения
adb shell pm list packages | findstr plaud
```

## 🐛 Решение проблем

### Проблема: "Gradle sync failed"
**Решение:**
1. Проверьте подключение к интернету
2. Убедитесь, что Java установлена: `java -version`
3. Очистите кэш: `.\gradlew.bat clean`

### Проблема: "SDK location not found"
**Решение:**
1. Установите Android SDK
2. Создайте файл `local.properties` в корне проекта:
```properties
sdk.dir=C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk
```

### Проблема: "Build failed"
**Решение:**
1. Проверьте версию Java (нужна 8+)
2. Обновите Android Build Tools
3. Очистите проект: `.\gradlew.bat clean build`

## 📊 Результат сборки

После успешной сборки вы получите:
- **APK файл:** `app/build/outputs/apk/debug/app-debug.apk`
- **Размер:** ~15-20 MB
- **Минимальная версия Android:** 8.0 (API 24)
- **Целевая версия:** Android 13 (API 33)

## 🎯 Функциональность

Приложение поддерживает:
- ✅ **Авторизация по логину/паролю** (как на веб-сайте!)
- ✅ **Запись звука с микрофона** (новая функция!)
- ✅ Загрузку готовых аудиофайлов
- ✅ JWT токены с автоматическим сохранением
- ✅ Отслеживание статуса обработки
- ✅ Просмотр результатов транскрипции и саммари
- ✅ Настройку URL API сервера
- ✅ Material Design 3 интерфейс
- ✅ Таймер записи в реальном времени
- ✅ Автоматическую отправку записанного аудио
- ✅ Проверку авторизации перед операциями

---

**Готово к сборке!** 🎉
