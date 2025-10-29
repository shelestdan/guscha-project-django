# 🔐 Руководство по настройке .env файла

## 📋 Содержание
1. [Быстрый старт](#быстрый-старт)
2. [Генерация секретных ключей](#генерация-секретных-ключей)
3. [Подробное описание переменных](#подробное-описание-переменных)
4. [Примеры для разных окружений](#примеры-для-разных-окружений)
5. [Безопасность](#безопасность)

---

## 🚀 Быстрый старт

### 1. Создайте .env файл
```bash
cd guscha_django
cp .env.example .env
```

### 2. Сгенерируйте секретные ключи
```bash
python ../generate-secrets.py
```

### 3. Скопируйте сгенерированные ключи в .env файл
```bash
nano .env  # или используйте любой редактор
```

### 4. Настройте остальные переменные
См. [Подробное описание переменных](#подробное-описание-переменных)

---

## 🔑 Генерация секретных ключей

### Автоматическая генерация (рекомендуется)
```bash
python generate-secrets.py
```

### Ручная генерация

#### Django SECRET_KEY
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Сильный пароль (для БД, email и т.д.)
```bash
python -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(32)))"
```

#### Случайный путь для админки
```bash
python -c "import secrets, string; print('admin-' + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for i in range(12)) + '/')"
```

---

## 📝 Подробное описание переменных

### 🔧 Django Settings

#### DEBUG
```env
DEBUG=False  # ВСЕГДА False в продакшене!
```
- `True` - режим разработки (показывает подробные ошибки)
- `False` - продакшн (скрывает ошибки от пользователей)

#### SECRET_KEY
```env
SECRET_KEY=ваш-уникальный-секретный-ключ-50-символов
```
- Используется для криптографических операций Django
- ОБЯЗАТЕЛЬНО уникальный для каждого проекта
- Минимум 50 символов
- НЕ используйте значение с "django-insecure"

#### ALLOWED_HOSTS
```env
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```
- Список доменов, с которых разрешены запросы
- Разделяются запятой без пробелов
- В продакшене НЕ используйте `*` или `localhost`

---

### 🗄️ Database Settings

#### POSTGRES_DB
```env
POSTGRES_DB=guscha_prod
```
- Имя базы данных
- Рекомендуется разные имена для dev/prod

#### POSTGRES_USER
```env
POSTGRES_USER=guscha_user
```
- Имя пользователя PostgreSQL
- НЕ используйте "postgres" в продакшене

#### POSTGRES_PASSWORD
```env
POSTGRES_PASSWORD=ваш-сильный-пароль-минимум-20-символов
```
- Пароль для PostgreSQL
- Минимум 20 символов
- Используйте буквы, цифры и спецсимволы
- Генерируйте случайно!

#### POSTGRES_HOST
```env
POSTGRES_HOST=db
```
- `db` - для Docker Compose (имя сервиса)
- `localhost` - для локальной разработки
- IP адрес - для внешней БД

#### POSTGRES_PORT
```env
POSTGRES_PORT=5432
```
- Стандартный порт PostgreSQL: 5432

---

### 📧 Email Settings

#### EMAIL_HOST
```env
EMAIL_HOST=smtp.gmail.com
```
Популярные провайдеры:
- Gmail: `smtp.gmail.com`
- Yandex: `smtp.yandex.ru`
- Mail.ru: `smtp.mail.ru`
- Beget: `smtp.beget.com`

#### EMAIL_PORT
```env
EMAIL_PORT=587
```
- `587` - TLS (рекомендуется)
- `465` - SSL
- `25` - без шифрования (не рекомендуется)

#### EMAIL_USE_TLS
```env
EMAIL_USE_TLS=True
```
- `True` - использовать TLS (рекомендуется)
- `False` - без TLS

#### EMAIL_HOST_USER
```env
EMAIL_HOST_USER=noreply@yourdomain.com
```
- Email адрес для отправки писем

#### EMAIL_HOST_PASSWORD
```env
EMAIL_HOST_PASSWORD=ваш-пароль-от-email
```
- Пароль от email
- Для Gmail используйте "App Password" (не основной пароль!)

#### DEFAULT_FROM_EMAIL
```env
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```
- Email отправителя по умолчанию

#### ADMINS
```env
ADMINS=Admin <admin@yourdomain.com>,Developer <dev@yourdomain.com>
```
- Список администраторов для уведомлений об ошибках
- Формат: `Name <email@domain.com>`
- Разделяются запятой

---

### 🔐 Security Settings

#### ADMIN_URL
```env
ADMIN_URL=secret-admin-path-x7k9m2p5/
```
- Секретный путь к админке (вместо `/admin/`)
- ОБЯЗАТЕЛЬНО заканчивается слешем `/`
- НЕ используйте очевидные значения: `admin/`, `panel/`, `control/`
- Генерируйте случайно!

#### ADMIN_IP_WHITELIST
```env
ADMIN_IP_WHITELIST=192.168.1.100,10.0.0.5
```
- IP адреса с доступом к админке
- Пусто = доступ для всех
- Разделяются запятой

#### JWT_SECRET_KEY
```env
JWT_SECRET_KEY=другой-секретный-ключ-для-jwt
```
- Отдельный ключ для JWT токенов
- ДОЛЖЕН отличаться от SECRET_KEY
- Минимум 50 символов

---

### 🤖 Telegram Bot Settings

#### TELEGRAM_BOT_TOKEN
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```
- Получите от @BotFather в Telegram
- Команда: `/newbot`

#### TELEGRAM_BOT_USERNAME
```env
TELEGRAM_BOT_USERNAME=YourBotName
```
- Имя бота без @
- Должно совпадать с именем в @BotFather

#### DJANGO_API_URL
```env
DJANGO_API_URL=http://django:8000
```
- `http://django:8000` - для Docker Compose
- `http://localhost:8000` - для локальной разработки

---

### 🌐 CORS and Frontend Settings

#### CORS_ALLOWED_ORIGINS
```env
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```
- Список доменов для CORS
- Разделяются запятой
- Используйте `https://` в продакшене

#### FRONTEND_URL
```env
FRONTEND_URL=https://yourdomain.com
```
- URL фронтенда
- Используется для генерации ссылок
- ОБЯЗАТЕЛЬНО `https://` в продакшене (для Telegram)

---

### 🔑 OAuth Settings

#### Google OAuth
```env
GOOGLE_CLIENT_ID=ваш-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=ваш-client-secret
```
Как получить:
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект
3. Включите Google+ API
4. Создайте OAuth 2.0 credentials
5. Добавьте Authorized redirect URIs: `https://yourdomain.com/accounts/google/login/callback/`

#### reCAPTCHA
```env
RECAPTCHA_PUBLIC_KEY=ваш-public-key
RECAPTCHA_PRIVATE_KEY=ваш-private-key
```
Как получить:
1. Перейдите на [reCAPTCHA Admin](https://www.google.com/recaptcha/admin)
2. Зарегистрируйте сайт
3. Выберите reCAPTCHA v2 или v3
4. Скопируйте ключи

---

### 🔄 Redis Settings

#### REDIS_URL
```env
REDIS_URL=redis://redis:6379/0
```
- `redis://redis:6379/0` - для Docker Compose
- `redis://localhost:6379/0` - для локальной разработки
- `/0` - номер базы данных Redis (0-15)

---

### 🌍 Domain and SSL Settings

#### DOMAIN_NAME
```env
DOMAIN_NAME=yourdomain.com
```
- Ваш основной домен
- Без `http://` или `https://`
- Без `www.`

#### LETS_ENCRYPT_EMAIL
```env
LETS_ENCRYPT_EMAIL=admin@yourdomain.com
```
- Email для уведомлений Let's Encrypt
- Используется при получении SSL сертификата

#### NGINX_HTTP_PORT
```env
NGINX_HTTP_PORT=80
```
- Порт для HTTP (обычно 80)

#### NGINX_HTTPS_PORT
```env
NGINX_HTTPS_PORT=443
```
- Порт для HTTPS (обычно 443)

---

### 🛡️ Django Axes (Brute Force Protection)

#### AXES_ENABLED
```env
AXES_ENABLED=True
```
- Включить защиту от брутфорса

#### AXES_FAILURE_LIMIT
```env
AXES_FAILURE_LIMIT=5
```
- Количество неудачных попыток входа

#### AXES_COOLOFF_TIME
```env
AXES_COOLOFF_TIME=1
```
- Время блокировки в часах

---

## 🌍 Примеры для разных окружений

### Development (локальная разработка)
```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
SECRET_KEY=django-insecure-dev-key-only
POSTGRES_DB=guscha_dev
POSTGRES_USER=guscha
POSTGRES_PASSWORD=guscha123
POSTGRES_HOST=localhost
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Staging (тестовый сервер)
```env
DEBUG=False
ALLOWED_HOSTS=staging.yourdomain.com
SECRET_KEY=уникальный-ключ-для-staging
POSTGRES_DB=guscha_staging
POSTGRES_USER=guscha_staging
POSTGRES_PASSWORD=сильный-пароль-staging
POSTGRES_HOST=db
FRONTEND_URL=https://staging.yourdomain.com
CORS_ALLOWED_ORIGINS=https://staging.yourdomain.com
```

### Production (продакшн)
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=уникальный-ключ-для-production
POSTGRES_DB=guscha_prod
POSTGRES_USER=guscha_prod
POSTGRES_PASSWORD=очень-сильный-пароль-production
POSTGRES_HOST=db
FRONTEND_URL=https://yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ADMIN_URL=secret-admin-x7k9m2p5/
```

---

## 🔒 Безопасность

### ✅ DO (Делайте):
1. **Генерируйте уникальные ключи** для каждого окружения
2. **Используйте сильные пароли** (минимум 20 символов)
3. **Храните .env в безопасном месте** (менеджер паролей)
4. **Добавьте .env в .gitignore** (уже добавлено)
5. **Регулярно меняйте пароли** (раз в 3-6 месяцев)
6. **Используйте разные ключи** для dev/staging/prod
7. **Включите DEBUG=False** в продакшене
8. **Используйте HTTPS** в продакшене

### ❌ DON'T (Не делайте):
1. **НЕ коммитьте .env в git**
2. **НЕ используйте одинаковые ключи** для разных окружений
3. **НЕ используйте слабые пароли** (типа "password123")
4. **НЕ используйте DEBUG=True** в продакшене
5. **НЕ используйте ALLOWED_HOSTS=***
6. **НЕ храните .env в публичных местах**
7. **НЕ отправляйте .env по email** или в мессенджерах
8. **НЕ используйте HTTP** в продакшене

---

## 🔍 Проверка .env файла

### Автоматическая проверка
```bash
./check-deployment.sh
```

### Ручная проверка
```bash
# Проверка что .env не в git
git status | grep .env

# Проверка DEBUG
grep "^DEBUG=" guscha_django/.env

# Проверка SECRET_KEY
grep "^SECRET_KEY=" guscha_django/.env | grep -v "django-insecure"

# Проверка ADMIN_URL
grep "^ADMIN_URL=" guscha_django/.env | grep -v "admin/"
```

---

## 📞 Troubleshooting

### Проблема: "SECRET_KEY environment variable is required"
**Решение:** Убедитесь что `SECRET_KEY` указан в .env файле

### Проблема: "ADMIN_URL should not use obvious values"
**Решение:** Измените `ADMIN_URL` на секретный путь (не "admin/")

### Проблема: База данных не подключается
**Решение:** Проверьте `POSTGRES_*` переменные в .env

### Проблема: Email не отправляются
**Решение:** 
1. Проверьте `EMAIL_*` переменные
2. Для Gmail используйте App Password
3. Проверьте что порт 587 открыт

### Проблема: Telegram бот не отвечает
**Решение:**
1. Проверьте `TELEGRAM_BOT_TOKEN`
2. Убедитесь что токен правильный (от @BotFather)
3. Проверьте логи: `docker compose logs telegram-bot`

---

## 📚 Дополнительные ресурсы

- [Django Settings Documentation](https://docs.djangoproject.com/en/5.2/ref/settings/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

**Готово! Ваш .env файл настроен правильно! 🎉**
