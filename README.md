# 🛍️ Guscha Project

Полнофункциональное веб-приложение для электронной коммерции на Django и React с Telegram ботом.

## 🚀 Быстрый старт

### Для нового сервера (Production)
```bash
git clone <your-repo-url> guscha-project
cd guscha-project
cd guscha_django && cp .env.example .env && nano .env
cd .. && chmod +x deploy.sh && ./deploy.sh production
```

📖 **Подробная инструкция:** [QUICK_START.md](QUICK_START.md)

### Для разработки (Development)
```bash
git clone <your-repo-url> guscha-project
cd guscha-project/guscha_django
cp .env.example .env
docker compose -f docker-compose.dev.yml up -d --build
```

---

## 📁 Структура проекта

```
guscha-project/
├── guscha_django/              # Django Backend
│   ├── apps/                   # Django приложения
│   ├── guscha_project/         # Настройки проекта
│   ├── telegram_bot/           # Telegram бот
│   ├── templates/              # HTML шаблоны
│   ├── static/                 # Статические файлы Django
│   ├── config/                 # Конфигурации (nginx, postgresql)
│   ├── Dockerfile              # Docker образ для Django
│   ├── Dockerfile.telegram     # Docker образ для Telegram бота
│   ├── docker-compose.dev.yml  # Development конфигурация
│   ├── requirements.txt        # Python зависимости
│   └── .env                    # Переменные окружения (НЕ в git!)
│
├── guscha_django_frontend/     # React Frontend
│   ├── src/                    # Исходный код React
│   ├── public/                 # Публичные файлы
│   ├── Dockerfile              # Docker образ для фронтенда
│   └── package.json            # Node.js зависимости
│
├── docker-compose.prod.yml     # Production конфигурация
├── deploy.sh                   # Скрипт автоматического деплоя
├── check-deployment.sh         # Скрипт проверки деплоя
├── generate-secrets.py         # Генератор секретных ключей
│
└── Документация:
    ├── QUICK_START.md          # Быстрый старт
    ├── DEPLOYMENT_GUIDE.md     # Полное руководство по деплою
    ├── ENV_SETUP_GUIDE.md      # Настройка .env файла
    └── PRE_DEPLOYMENT_CHECKLIST.md  # Checklist перед деплоем
```

---

## 🎯 Основные возможности

### Backend (Django)
- ✅ REST API на Django REST Framework
- ✅ PostgreSQL база данных
- ✅ Redis для кэширования
- ✅ JWT аутентификация
- ✅ Google OAuth
- ✅ Защита от брутфорса (Django Axes)
- ✅ Современная админка (Django Unfold)
- ✅ Система резервного копирования
- ✅ Мониторинг и логирование

### Frontend (React)
- ✅ React 19 с TypeScript
- ✅ Material-UI компоненты
- ✅ Zustand для state management
- ✅ React Router для навигации
- ✅ Адаптивный дизайн (Tailwind CSS)
- ✅ Интеграция с Google Maps

### Telegram Bot
- ✅ Интеграция с Django API
- ✅ Управление заказами
- ✅ Уведомления пользователей
- ✅ Поддержка команд

### DevOps
- ✅ Docker и Docker Compose
- ✅ Nginx reverse proxy
- ✅ SSL/HTTPS поддержка
- ✅ Автоматические healthchecks
- ✅ Логирование и мониторинг

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| [QUICK_START.md](QUICK_START.md) | Быстрый старт для новых пользователей |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Полное руководство по деплою |
| [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md) | Подробное описание .env переменных |
| [PRE_DEPLOYMENT_CHECKLIST.md](PRE_DEPLOYMENT_CHECKLIST.md) | Checklist перед деплоем |

---

## 🔧 Требования

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git**

Для локальной разработки без Docker:
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

---

## 🚀 Деплой

### Автоматический деплой (рекомендуется)
```bash
# Production
./deploy.sh production

# Development
./deploy.sh development
```

### Ручной деплой
```bash
# 1. Настройте .env
cd guscha_django
cp .env.example .env
nano .env

# 2. Запустите Docker Compose
cd ..
docker compose -f docker-compose.prod.yml up -d --build

# 3. Выполните миграции
docker compose -f docker-compose.prod.yml exec django python manage.py migrate

# 4. Создайте суперпользователя
docker compose -f docker-compose.prod.yml exec django python manage.py createsuperuser

# 5. Соберите статику
docker compose -f docker-compose.prod.yml exec django python manage.py collectstatic --noinput
```

---

## 🔐 Безопасность

### Перед деплоем в продакшн:

1. **Сгенерируйте секретные ключи:**
   ```bash
   python generate-secrets.py
   ```

2. **Проверьте .env файл:**
   - ✅ `DEBUG=False`
   - ✅ `SECRET_KEY` изменён
   - ✅ `ADMIN_URL` секретный путь
   - ✅ Сильные пароли для БД
   - ✅ HTTPS настроен

3. **Запустите проверку:**
   ```bash
   ./check-deployment.sh
   ```

4. **Используйте checklist:**
   См. [PRE_DEPLOYMENT_CHECKLIST.md](PRE_DEPLOYMENT_CHECKLIST.md)

---

## 🛠️ Полезные команды

### Docker Compose
```bash
# Просмотр логов
docker compose logs -f

# Статус контейнеров
docker compose ps

# Перезапуск сервиса
docker compose restart django

# Остановка всех сервисов
docker compose down

# Пересборка образов
docker compose build --no-cache
```

### Django Management
```bash
# Миграции
docker compose exec django python manage.py migrate

# Создание суперпользователя
docker compose exec django python manage.py createsuperuser

# Сбор статики
docker compose exec django python manage.py collectstatic

# Django shell
docker compose exec django python manage.py shell

# Проверка проекта
docker compose exec django python manage.py check
```

### База данных
```bash
# Подключение к PostgreSQL
docker compose exec db psql -U guscha -d guscha_prod

# Резервное копирование
docker compose exec db pg_dump -U guscha guscha_prod > backup.sql

# Восстановление
docker compose exec -T db psql -U guscha guscha_prod < backup.sql
```

---

## 📊 Мониторинг

### Логи
```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f django
docker compose logs -f nginx
docker compose logs -f telegram-bot

# Последние 100 строк
docker compose logs --tail=100 django
```

### Метрики
```bash
# Использование ресурсов
docker stats

# Статус контейнеров
docker compose ps

# Healthcheck
docker compose exec django python manage.py check
```

---

## 🔄 Обновление

```bash
# 1. Получите последние изменения
git pull origin main

# 2. Остановите контейнеры
docker compose down

# 3. Пересоберите и запустите
docker compose up -d --build

# 4. Выполните миграции
docker compose exec django python manage.py migrate

# 5. Соберите статику
docker compose exec django python manage.py collectstatic --noinput
```

---

## 🆘 Troubleshooting

### Контейнеры не запускаются
```bash
docker compose logs
docker compose down
docker compose up -d --build
```

### База данных не подключается
```bash
docker compose ps db
docker compose logs db
docker compose exec django python manage.py dbshell
```

### Статика не загружается
```bash
docker compose exec django python manage.py collectstatic --noinput --clear
docker compose exec django ls -la /app/static_root/
```

### 502 Bad Gateway
```bash
docker compose ps django
docker compose logs nginx
docker compose restart nginx
```

Больше решений: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting)

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Запустите `./check-deployment.sh`
3. Проверьте логи: `docker compose logs`

---

## 📄 Лицензия

Этот проект является частной разработкой.

---

## 🎉 Готово к работе!

Следуйте [QUICK_START.md](QUICK_START.md) для быстрого запуска или [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) для подробной настройки.