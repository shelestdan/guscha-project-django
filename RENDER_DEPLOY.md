## Деплой Guscha на Render (почти без ручных шагов)

Проект уже подготовлен для Render:

- `guscha_django/Dockerfile` запускает Django через Gunicorn и учитывает переменную `PORT` (как на Render).
- `render.yaml` в корне описывает web‑сервис, PostgreSQL и Redis.

Ниже шаги, которые нужно сделать только в панели Render.

---

### 1. Выложите код в Git (GitHub / GitLab)

1. Инициализируйте репозиторий (если ещё нет) и **убедитесь, что `.env` НЕ в Git**:
   - в `.gitignore` должен быть `.env`.
2. Создайте приватный репозиторий и запушьте код.

> Все реальные секреты (ключи, пароли, токены) должны храниться в переменных окружения Render, а не в `.env` в репо.

---

### 2. Подготовка переменных окружения

Вы уже заполнили локальный `.env` в `guscha_django/.env`.  
На Render нужно просто перенести эти значения в переменные окружения:

- `DEBUG=False`
- `SECRET_KEY=...`
- `ALLOWED_HOSTS=your-render-subdomain.onrender.com,your-custom-domain.ru`
- `TELEGRAM_BOT_TOKEN=...`
- `GOOGLE_CLIENT_ID=...`
- `GOOGLE_CLIENT_SECRET=...`
- `JWT_SECRET_KEY=...`
- `FRONTEND_URL=https://your-custom-domain.ru`
- SMTP/Email:
  - `EMAIL_HOST`
  - `EMAIL_PORT`
  - `EMAIL_USE_TLS`
  - `EMAIL_HOST_USER`
  - `EMAIL_HOST_PASSWORD`
  - `DEFAULT_FROM_EMAIL`
- при необходимости: Redis и прочие.

Часть из этого уже описана в `render.yaml`, но значения секретов вы всё равно будете задавать в панели Render.

---

### 3. Создание Blueprint (render.yaml) на Render

1. Зайдите на `https://render.com`.
2. Создайте аккаунт (если ещё нет).
3. В меню выберите **Blueprints → New Blueprint**.
4. Укажите ваш репозиторий (где лежит этот проект с `render.yaml` в корне).
5. Render считает `render.yaml` и предложит создать:
   - web‑сервис `guscha-portfolio` (тип: Docker),
   - базу `guscha-db` (Postgres, free план),
   - Redis `guscha-redis` (free план).
6. Нажмите **Apply** / **Create Resources**.

Render:

- создаст Postgres и Redis;
- подставит для web‑сервиса `DATABASE_URL` и `REDIS_URL`;
- соберёт Docker‑образ из `guscha_django/Dockerfile`;
- запустит контейнер.

---

### 4. Проверка сервиса

Когда деплой завершится:

1. Откройте web‑сервис `guscha-portfolio` в Render.
2. Перейдите по сгенерированному URL вида:
   - `https://guscha-portfolio.onrender.com`
3. Убедитесь, что:
   - главная страница открывается,
   - API (`/api/...`) работает,
   - админка доступна по `https://.../<ADMIN_URL>`.

Если что-то упало — смотрите логи в разделе **Logs** у web‑сервиса.

---

### 5. Привязка собственного домена (для портфолио)

1. В настройках web‑сервиса на Render откройте раздел **Custom Domains**.
2. Добавьте ваш домен (например, `portfolio.guscha.ru`).
3. Следуйте инструкции Render по настройке DNS (обычно CNAME).
4. После валидации Render автоматически выдаст HTTPS‑сертификат.

Не забудьте обновить переменные окружения:

- `ALLOWED_HOSTS=your-render-subdomain.onrender.com,portfolio.guscha.ru`
- `FRONTEND_URL=https://portfolio.guscha.ru`

---

### 6. Что уже сделано за вас

- Обновлён `Dockerfile`:
  - применяет миграции `python manage.py migrate --noinput` при старте;
  - запускает Gunicorn на `0.0.0.0:$PORT` (как требует Render).
- Добавлен `render.yaml`:
  - описывает web‑сервис, Postgres и Redis;
  - связывает `DATABASE_URL` и `REDIS_URL` с сервисами Render.

Итого: с вашей стороны остаётся только:

1. Запушить репозиторий в Git.
2. Подключить его в Render Blueprint.
3. Перенести значения из локального `.env` в переменные окружения Render.
4. Один раз нажать Deploy / Apply. 

