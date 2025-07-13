# Guscha Project

Веб-приложение на Django и React для электронной коммерции.

## Структура проекта

- `guscha_django/` - Бэкенд на Django
- `guscha_django_frontend/` - Фронтенд на React
- `guscha_project/` - Дополнительные файлы проекта

## Установка и запуск

### Бэкенд (Django)

1. Перейдите в директорию бэкенда:
   ```
   cd guscha_django
   ```

2. Создайте и активируйте виртуальное окружение:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

4. Выполните миграции:
   ```
   python manage.py migrate
   ```

5. Запустите сервер:
   ```
   python manage.py runserver
   ```

### Фронтенд (React)

1. Перейдите в директорию фронтенда:
   ```
   cd guscha_django_frontend
   ```

2. Установите зависимости:
   ```
   npm install
   ```

3. Запустите приложение в режиме разработки:
   ```
   npm start
   ```

## Скрипты автоматизации

- `build_frontend_improved.ps1` - Скрипт для сборки фронтенда
- `build_and_deploy.ps1` - Скрипт для сборки и деплоя проекта