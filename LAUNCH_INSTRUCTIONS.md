# Инструкция по запуску и пересборке проекта GusTest

## Обзор проекта

Проект состоит из:
- **Backend**: Django (Python) в папке `guscha_django/`
- **Frontend**: React (JavaScript) в папке `guscha_django_frontend/`
- **Развертывание**: Docker с nginx, redis, telegram-bot

---

## 🚀 Сценарии запуска

### 1. ЛОКАЛЬНАЯ РАЗРАБОТКА (отдельный запуск)

#### 1.1. Запуск только Backend (Django)
```powershell
# Переход в папку Django
cd guscha_django

# Активация виртуального окружения (если есть)
# .\venv\Scripts\Activate.ps1

# Установка зависимостей
pip install -r requirements.txt

# Миграции базы данных
python manage.py makemigrations
python manage.py migrate

# Создание суперпользователя (при первом запуске)
python manage.py createsuperuser

# Запуск сервера разработки
python manage.py runserver
# Доступен по адресу: http://127.0.0.1:8000/
```

#### 1.2. Запуск только Frontend (React)
```powershell
# Переход в папку React
cd guscha_django_frontend

# Установка зависимостей
npm install

# Запуск сервера разработки
npm start
# Доступен по адресу: http://localhost:3000/
```

### 2. ИНТЕГРИРОВАННАЯ СБОРКА (фронтенд в Django)

#### 2.1. Базовая сборка фронтенда
```powershell
# Из корневой папки проекта
.\build_frontend.ps1
```
**Что делает**: Собирает React-приложение и копирует файлы в `guscha_django/static/`

#### 2.2. Улучшенная сборка фронтенда
```powershell
# Из корневой папки проекта
.\build_frontend_improved.ps1
```
**Что делает**: Расширенная версия сборки с дополнительными проверками

#### 2.3. Сборка для Docker
```powershell
# Из корневой папки проекта
.\build_frontend_for_docker.ps1
```
**Что делает**: Специальная сборка, оптимизированная для Docker-контейнера

#### 2.4. Запуск Django с собранным фронтендом
```powershell
cd guscha_django
python manage.py collectstatic --noinput
python manage.py runserver
# Доступен по адресу: http://127.0.0.1:8000/
```

### 3. DOCKER-РАЗВЕРТЫВАНИЕ (полная сборка)

#### 3.1. Полная сборка и запуск в Docker
```powershell
cd guscha_django
.\docker-build-and-run.ps1
```
**Что делает**:
- Собирает фронтенд
- Создает Docker-образы для всех сервисов
- Запускает контейнеры: django, redis, telegram-bot, nginx
- Доступен по адресу: http://localhost/

#### 3.2. Ручное управление Docker
```powershell
cd guscha_django

# Сборка образов
docker-compose build

# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

---

## 🔄 Пересборка и обновление

### Пересборка только фронтенда
```powershell
# Быстрая пересборка
.\build_frontend.ps1

# Или улучшенная версия
.\build_frontend_improved.ps1
```

### Пересборка Docker-контейнеров
```powershell
cd guscha_django

# Остановка текущих контейнеров
docker-compose down

# Пересборка с принудительным обновлением
docker-compose build --no-cache

# Запуск обновленных контейнеров
docker-compose up -d
```

### Полная пересборка проекта
```powershell
cd guscha_django

# Остановка Docker (если запущен)
docker-compose down -v

# Очистка Docker-образов (опционально)
docker system prune -f

# Полная пересборка и запуск
.\docker-build-and-run.ps1
```

---

## 🛠️ Команды для разработки

### Django команды
```powershell
cd guscha_django

# Создание новых миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Сбор статических файлов
python manage.py collectstatic

# Запуск shell Django
python manage.py shell

# Запуск тестов
python manage.py test
```

### React команды
```powershell
cd guscha_django_frontend

# Установка новых зависимостей
npm install package-name

# Обновление зависимостей
npm update

# Запуск тестов
npm test

# Сборка для продакшена
npm run build

# Анализ размера bundle
npm run build -- --analyze
```

---

## 🔍 Отладка и устранение неполадок

### Проверка статуса Docker
```powershell
cd guscha_django

# Список запущенных контейнеров
docker-compose ps

# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker-compose logs django
docker-compose logs nginx
docker-compose logs redis
docker-compose logs telegram-bot
```

### Очистка и сброс
```powershell
# Очистка node_modules и переустановка
cd guscha_django_frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install

# Очистка Docker
cd guscha_django
docker-compose down -v
docker system prune -f
docker volume prune -f
```

### Проверка портов
```powershell
# Проверка занятых портов
netstat -an | findstr :80
netstat -an | findstr :8000
netstat -an | findstr :3000
```

---

## 📋 Быстрый справочник

| Задача | Команда |
|--------|--------|
| Локальная разработка Django | `cd guscha_django && python manage.py runserver` |
| Локальная разработка React | `cd guscha_django_frontend && npm start` |
| Сборка фронтенда | `.\build_frontend.ps1` |
| Полный Docker-запуск | `cd guscha_django && .\docker-build-and-run.ps1` |
| Остановка Docker | `cd guscha_django && docker-compose down` |
| Просмотр логов | `cd guscha_django && docker-compose logs -f` |
| Пересборка Docker | `docker-compose down && docker-compose build --no-cache && docker-compose up -d` |

---

## 🌐 URL-адреса

- **Локальная разработка Django**: http://127.0.0.1:8000/
- **Локальная разработка React**: http://localhost:3000/
- **Docker-развертывание**: http://localhost/
- **Админ-панель Django**: http://localhost/admin/ (или http://127.0.0.1:8000/admin/)

---

## ⚠️ Важные замечания

1. **Порты**: Убедитесь, что порты 80, 8000, 3000 не заняты другими приложениями
2. **Docker**: Для работы Docker требуется Docker Desktop на Windows
3. **Node.js**: Убедитесь, что установлена актуальная версия Node.js (рекомендуется LTS)
4. **Python**: Проект требует Python 3.8+ с pip
5. **Переменные окружения**: Проверьте файлы `.env` в соответствующих папках

---

*Последнее обновление: январь 2025*