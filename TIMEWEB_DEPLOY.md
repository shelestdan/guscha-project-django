## Деплой проекта Guscha на Timeweb Cloud (Docker)

Этот файл описывает, что нужно сделать, чтобы выкатить текущий проект на Timeweb Cloud с использованием **Cloud Apps + Dockerfile**.  
Проект уже подготовлен к продакшну (Django + React + Gunicorn), поэтому основная задача — правильно собрать фронтенд и настроить окружение.

---

### 1. Что у вас уже есть в проекте

- **Backend**: `guscha_django/` (Django 5.2, Gunicorn, Postgres, Redis, Telegram bot).
- **Frontend**: `guscha_django_frontend/` (React, сборка через `react-scripts build`).
- **Docker**: `guscha_django/Dockerfile` — собирает Python-зависимости, запускает Gunicorn и выполняет `collectstatic`.
- **Статика**:
  - Django использует `STATIC_ROOT=static_root` и `ManifestStaticFilesStorage`.
  - README в `guscha_django/README.md` уже описывает, как копировать сборку фронтенда в `static_root`.

Для деплоя на Timeweb Cloud мы используем **один контейнер** с Django, который отдаёт API и уже собранный React (как статические файлы).

---

### 2. Подготовка переменных окружения (.env для Django)

1. Перейдите в папку `guscha_django`:

   ```bash
   cd guscha_django
   ```

2. Скопируйте файл примера под Timeweb:

   ```bash
   cp .env.timeweb.example .env
   ```

3. Заполните `.env` реальными значениями:

   - **Базовые параметры**
     - `DEBUG=False`
     - `SECRET_KEY=` — сгенерируйте уникальную случайную строку.
     - `ALLOWED_HOSTS=your-domain.ru,www.your-domain.ru`
   - **База данных (Postgres)** — возьмите параметры из панели Timeweb (Managed PostgreSQL или база на сервере):
     - `POSTGRES_DB`
     - `POSTGRES_USER`
     - `POSTGRES_PASSWORD`
     - `POSTGRES_HOST`
     - `POSTGRES_PORT=5432`
   - **Redis** (если используете Managed Redis на Timeweb):
     - `REDIS_URL=redis://user:password@redis-host:6379/1`
   - **Админка и безопасность**
     - `ADMIN_URL` — неочевидный путь к админке (например, `secure-admin-guscha-9c3f4e7b`).
     - `ADMIN_IP_WHITELIST` — при желании ограничьте доступ по IP.
   - **Почта (SMTP Timeweb)**:
     - `EMAIL_HOST=smtp.timeweb.ru`
     - `EMAIL_PORT=25` (без шифрования) или используйте свои значения по документации Timeweb.
     - `EMAIL_USE_TLS=False` (или настройте по своему варианту).
     - `EMAIL_HOST_USER=your_mailbox@your-domain.ru`
     - `EMAIL_HOST_PASSWORD=your-mailbox-password`
     - `DEFAULT_FROM_EMAIL=noreply@your-domain.ru`
   - **Прочее (по необходимости)**:
     - `TELEGRAM_BOT_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, AWS/backup, Celery.

> **Важно:** `.env` НЕ коммитится в репозиторий. На Timeweb значения переменных вы будете переносить в панель Cloud Apps.

---

### 3. Подготовка фронтенда (React)

1. Перейдите в папку фронтенда:

   ```bash
   cd ../guscha_django_frontend
   ```

2. В файле `.env.production` пропишите реальный URL API:

   ```env
   REACT_APP_API_URL=https://your-domain.ru/api
   REACT_APP_ENV=production
   REACT_APP_DEBUG=false
   ```

3. Установите зависимости и соберите фронтенд:

   ```bash
   npm install
   npm run build
   ```

Сборка появится в папке `guscha_django_frontend/build`.

---

### 4. Копирование фронтенда в Django (static_root)

1. Вернитесь в папку `guscha_django`:

   ```bash
   cd ../guscha_django
   ```

2. Скопируйте содержимое `build` во `static_root` (как описано в `README.md`):

   Пример для Unix-подобной системы:

   ```bash
   cp -r ../guscha_django_frontend/build/* ./static_root/
   cp -r ../guscha_django_frontend/build/static/* ./static_root/
   ```

   На Windows можно сделать то же самое через PowerShell (`Copy-Item -Recurse`) или любым другим удобным способом.

3. Выполните сбор Django-статических файлов:

   ```bash
   python manage.py collectstatic --noinput
   ```

> Идея: React собирается в статические файлы, которые кладутся в `static_root`, а Django / Gunicorn / Nginx отдают их как обычную статику.

---

### 5. Локальная проверка в прод-режиме

Перед деплоем на Timeweb имеет смысл прогнать приложение локально как можно ближе к прод-настройкам.

1. Убедитесь, что `.env` в `guscha_django` содержит `DEBUG=False` и корректные значения.
2. Запустите:

   ```bash
   cd guscha_django
   python manage.py runserver 0.0.0.0:8000
   ```

3. Проверьте:
   - что главная страница открывается;
   - что API-эндпоинты (`/api/...`) работают;
   - что статика и медиа отдаются корректно.

---

### 6. Деплой на Timeweb Cloud через Dockerfile

#### 6.1. Подготовка репозитория

1. Убедитесь, что все изменения закоммичены (кроме `.env`).
2. Репозиторий должен быть доступен Timeweb (GitHub, GitLab, Bitbucket или собственный Git).

#### 6.2. Создание приложения в панели Timeweb Cloud

1. Войдите в панель Timeweb Cloud.
2. Перейдите в раздел **Приложения (Cloud Apps)** → **Создать приложение**.
3. Выберите тип деплоя **из Dockerfile / контейнер**.
4. Укажите:
   - Репозиторий с проектом.
   - Путь к Dockerfile: `guscha_django/Dockerfile`.
   - Рабочую ветку (обычно `main` или `master`).

Timeweb автоматически:

- соберёт образ из `python:3.11-slim`,
- установит зависимости из `requirements.txt`,
- выполнит `collectstatic`,
- запустит Gunicorn командой:

```bash
gunicorn --bind 0.0.0.0:8000 --workers 3 guscha_project.wsgi:application
```

#### 6.3. Настройка переменных окружения в Timeweb

В разделе **Переменные окружения** в Cloud Apps:

1. Создайте переменные по аналогии с вашим локальным `.env` (из `.env.timeweb.example`):
   - `DEBUG=False`
   - `SECRET_KEY=...`
   - `ALLOWED_HOSTS=your-domain.ru,www.your-domain.ru`
   - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
   - `REDIS_URL` (если используете Redis)
   - `ADMIN_URL`, `ADMIN_IP_WHITELIST`
   - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`
   - остальные по необходимости.

2. Сохраните конфигурацию и перезапустите приложение.

#### 6.4. Домен и HTTPS

1. В панели Timeweb привяжите домен к созданному приложению.
2. Включите **SSL / HTTPS** (обычно Let’s Encrypt в пару кликов).
3. Убедитесь, что:
   - сайт открывается по `https://your-domain.ru`;
   - запросы к API (`/api/...`) работают;
   - админка доступна по вашему `ADMIN_URL`.

---

### 7. Что нужно сделать вам по сути

- **Заполнить `.env` из `.env.timeweb.example` реальными значениями (секреты, БД, SMTP, домен).**
- **Собрать фронтенд (`npm run build`) и скопировать его в `static_root`, затем выполнить `collectstatic`.**
- **Создать Cloud App на Timeweb по Dockerfile `guscha_django/Dockerfile` и перенести переменные окружения в панель.**
- **Привязать домен и включить HTTPS.**

После этого проект будет готов к полноценному запуску на Timeweb Cloud.  
Дальнейшая автоматизация (CI/CD, авто-сборка фронтенда и т.п.) может быть настроена дополнительно, при необходимости.

