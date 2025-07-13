# Инструкция по запуску приложения

## Проблема: Белый экран и 404 ошибки статических файлов

### Причина

Ошибка возникает из-за неправильной настройки путей к статическим файлам React после сборки.

### Решение

## Шаг 1: Установка зависимостей фронтенда

```bash
cd guscha_django_frontend
npm install
```

## Шаг 2: Сборка React приложения

```bash
cd guscha_django_frontend
npm run build
```

## Шаг 3: Развертывание (автоматически)

```bash
cd guscha_django
python deploy_frontend.py
```

## Шаг 4: Применение миграций

```bash
cd guscha_django
python manage.py makemigrations
python manage.py migrate
```

## Шаг 5: Сборка статических файлов Django

```bash
cd guscha_django
python manage.py collectstatic --noinput
```

## Шаг 6: Запуск сервера

```bash
cd guscha_django
python manage.py runserver
```

## Альтернативное ручное развертывание

Если автоматический скрипт не работает:

### 1. Сборка React

```bash
cd guscha_django_frontend
npm run build
```

### 2. Копирование файлов вручную

```bash
# Копируем index.html
cp guscha_django_frontend/build/index.html guscha_django/templates/

# Копируем статические файлы
cp -r guscha_django_frontend/build/static/* guscha_django/static_root/static/
```

### 3. Проверка структуры

После сборки должна быть следующая структура:

```
guscha_django/
├── templates/
│   └── index.html
├── static_root/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── media/
```

## Настройка Google Maps API

1. Получите API ключ в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте файл `.env` в `guscha_django_frontend/`:

```
REACT_APP_GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

## Проверка

После запуска сервера:

- Откройте http://localhost:8000
- Должен открыться React интерфейс
- Статические файлы должны загружаться без 404 ошибок

## Отладка

Если проблема сохраняется:

1. Проверьте логи Django:

```bash
python manage.py runserver --verbosity 2
```

2. Проверьте наличие файлов:

```bash
ls -la guscha_django/templates/
ls -la guscha_django/static_root/static/
```

3. Проверьте настройки в settings.py:

- STATIC_URL должен быть '/static/'
- STATIC_ROOT должен указывать на правильную директорию

## Примечание для Windows

На Windows используйте:

```cmd
# Вместо cp используйте copy
copy guscha_django_frontend\build\index.html guscha_django\templates\

# Для копирования директорий
xcopy /E /I guscha_django_frontend\build\static guscha_django\static_root\static
```
