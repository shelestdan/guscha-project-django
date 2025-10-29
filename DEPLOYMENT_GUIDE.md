# 🚀 Руководство по деплою Guscha Project

## 📋 Содержание
1. [Предварительные требования](#предварительные-требования)
2. [Подготовка к деплою](#подготовка-к-деплою)
3. [Настройка переменных окружения](#настройка-переменных-окружения)
4. [Запуск на новом сервере](#запуск-на-новом-сервере)
5. [SSL/HTTPS настройка](#sslhttps-настройка)
6. [Резервное копирование](#резервное-копирование)
7. [Мониторинг и логи](#мониторинг-и-логи)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Предварительные требования

На сервере должны быть установлены:
- **Docker** (версия 20.10+)
- **Docker Compose** (версия 2.0+)
- **Git** (для клонирования репозитория)

### Проверка установки:
```bash
docker --version
docker compose version
git --version
```

### Установка Docker (если не установлен):
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Перезайдите в систему после добавления в группу docker
```

---

## 📦 Подготовка к деплою

### 1. Клонирование репозитория
```bash
git clone <your-repository-url> guscha-project
cd guscha-project
```

### 2. Создание .env файла
```bash
cd guscha_django
cp .env.example .env
```

### 3. Редактирование .env файла
**ВАЖНО:** Откройте файл `.env` и измените ВСЕ значения на свои:

```bash
nano .env
# или
vim .env
```

---

## 🔐 Настройка переменных окружения

### Критически важные переменные (ОБЯЗАТЕЛЬНО изменить):

#### 1. Django Secret Key
```bash
# Сгенерируйте новый секретный ключ:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Вставьте результат в .env:
SECRET_KEY=ваш-сгенерированный-ключ
```

#### 2. База данных
```env
POSTGRES_DB=guscha_prod
POSTGRES_USER=guscha_user
POSTGRES_PASSWORD=ваш-сильный-пароль-минимум-20-символов
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

#### 3. Домен и безопасность
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DOMAIN_NAME=yourdomain.com
FRONTEND_URL=https://yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### 4. Админка (секретный путь)
```env
# Придумайте сложный путь, например:
ADMIN_URL=secret-admin-path-x7k9m2p5/
```

#### 5. Email настройки
```env
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=ваш-пароль-от-email
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
ADMINS=Admin <admin@yourdomain.com>
```

#### 6. Telegram Bot
```env
TELEGRAM_BOT_TOKEN=получите-от-@BotFather
TELEGRAM_BOT_USERNAME=YourBotName
```

#### 7. Google OAuth (если используется)
```env
GOOGLE_CLIENT_ID=ваш-client-id
GOOGLE_CLIENT_SECRET=ваш-client-secret
```

#### 8. JWT Secret
```env
# Сгенерируйте отдельный ключ для JWT:
JWT_SECRET_KEY=другой-секретный-ключ-для-jwt
```

---

## 🚀 Запуск на новом сервере

### Вариант 1: Production запуск (рекомендуется)

```bash
# 1. Перейдите в корень проекта
cd /path/to/guscha-project

# 2. Убедитесь что .env настроен
cat guscha_django/.env

# 3. Запустите production конфигурацию
docker compose -f docker-compose.prod.yml up -d --build

# 4. Проверьте статус контейнеров
docker compose -f docker-compose.prod.yml ps

# 5. Проверьте логи
docker compose -f docker-compose.prod.yml logs -f
```

### Вариант 2: Development запуск (для тестирования)

```bash
cd guscha_django
docker compose -f docker-compose.dev.yml up -d --build
```

### Первоначальная настройка Django

```bash
# Выполните миграции базы данных
docker compose -f docker-compose.prod.yml exec django python manage.py migrate

# Создайте суперпользователя
docker compose -f docker-compose.prod.yml exec django python manage.py createsuperuser

# Соберите статические файлы
docker compose -f docker-compose.prod.yml exec django python manage.py collectstatic --noinput
```

---

## 🔒 SSL/HTTPS настройка

### Вариант 1: Let's Encrypt (бесплатный SSL)

```bash
# 1. Установите certbot
sudo apt-get update
sudo apt-get install certbot

# 2. Получите сертификат
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 3. Создайте директорию для сертификатов
mkdir -p ssl

# 4. Скопируйте сертификаты
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
sudo chmod 644 ssl/*.pem
```

### Вариант 2: Свой SSL сертификат

```bash
# Поместите ваши сертификаты в директорию ssl/
mkdir -p ssl
cp your-certificate.crt ssl/fullchain.pem
cp your-private-key.key ssl/privkey.pem
chmod 644 ssl/*.pem
```

### Обновление nginx.conf для HTTPS

Добавьте в `guscha_django/config/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # ... остальная конфигурация
}

# Редирект с HTTP на HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 💾 Резервное копирование

### Автоматическое резервное копирование базы данных

```bash
# Создайте скрипт backup.sh
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U guscha guscha_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz guscha_django/media/

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh
```

### Настройка cron для автоматического бэкапа

```bash
# Добавьте в crontab (ежедневно в 2:00 ночи)
crontab -e

# Добавьте строку:
0 2 * * * /path/to/guscha-project/backup.sh >> /var/log/guscha-backup.log 2>&1
```

### Восстановление из бэкапа

```bash
# Восстановление базы данных
docker compose -f docker-compose.prod.yml exec -T db psql -U guscha guscha_prod < /backups/db_backup_YYYYMMDD_HHMMSS.sql

# Восстановление media файлов
tar -xzf /backups/media_backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## 📊 Мониторинг и логи

### Просмотр логов

```bash
# Все сервисы
docker compose -f docker-compose.prod.yml logs -f

# Конкретный сервис
docker compose -f docker-compose.prod.yml logs -f django
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f telegram-bot

# Последние 100 строк
docker compose -f docker-compose.prod.yml logs --tail=100 django
```

### Проверка статуса

```bash
# Статус всех контейнеров
docker compose -f docker-compose.prod.yml ps

# Использование ресурсов
docker stats

# Проверка здоровья
docker compose -f docker-compose.prod.yml exec django python manage.py check
```

### Логи Django

```bash
# Логи находятся в guscha_django/logs/
tail -f guscha_django/logs/django.log
tail -f guscha_django/logs/security.log
tail -f guscha_django/logs/errors.log
```

---

## 🔧 Troubleshooting

### Проблема: Контейнеры не запускаются

```bash
# Проверьте логи
docker compose -f docker-compose.prod.yml logs

# Пересоберите образы
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

### Проблема: База данных не подключается

```bash
# Проверьте что контейнер БД запущен
docker compose -f docker-compose.prod.yml ps db

# Проверьте логи БД
docker compose -f docker-compose.prod.yml logs db

# Проверьте подключение
docker compose -f docker-compose.prod.yml exec django python manage.py dbshell
```

### Проблема: Статические файлы не загружаются

```bash
# Пересоберите статику
docker compose -f docker-compose.prod.yml exec django python manage.py collectstatic --noinput --clear

# Проверьте права доступа
docker compose -f docker-compose.prod.yml exec django ls -la /app/static_root/
```

### Проблема: 502 Bad Gateway

```bash
# Проверьте что Django запущен
docker compose -f docker-compose.prod.yml ps django

# Проверьте логи nginx
docker compose -f docker-compose.prod.yml logs nginx

# Перезапустите nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Проблема: Telegram бот не отвечает

```bash
# Проверьте логи бота
docker compose -f docker-compose.prod.yml logs telegram-bot

# Проверьте токен в .env
grep TELEGRAM_BOT_TOKEN guscha_django/.env

# Перезапустите бота
docker compose -f docker-compose.prod.yml restart telegram-bot
```

---

## 🔄 Обновление приложения

```bash
# 1. Получите последние изменения
git pull origin main

# 2. Пересоберите и перезапустите
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

# 3. Выполните миграции
docker compose -f docker-compose.prod.yml exec django python manage.py migrate

# 4. Соберите статику
docker compose -f docker-compose.prod.yml exec django python manage.py collectstatic --noinput
```

---

## 🛡️ Безопасность

### Checklist перед запуском в продакшн:

- [ ] Изменен SECRET_KEY
- [ ] Изменен JWT_SECRET_KEY
- [ ] Изменен ADMIN_URL на секретный путь
- [ ] DEBUG=False
- [ ] Настроены сильные пароли для БД
- [ ] Настроен HTTPS/SSL
- [ ] Настроены CORS_ALLOWED_ORIGINS
- [ ] Настроены email уведомления
- [ ] Настроено резервное копирование
- [ ] Файл .env добавлен в .gitignore
- [ ] Настроен firewall на сервере
- [ ] Обновлены все зависимости

### Рекомендации:

1. **Никогда не коммитьте .env файл в git**
2. **Используйте сильные пароли** (минимум 20 символов)
3. **Регулярно обновляйте зависимости**
4. **Мониторьте логи безопасности**
5. **Настройте автоматические бэкапы**

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker compose logs`
2. Проверьте статус: `docker compose ps`
3. Проверьте документацию Django и Docker

---

**Готово! Ваше приложение должно работать на любом сервере с Docker! 🎉**
