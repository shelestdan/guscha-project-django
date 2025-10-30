# 🍎 Guscha Project - macOS Setup Guide

## Быстрый старт на macOS

Этот гайд поможет запустить проект на macOS одной командой через Docker.

---

## 📋 Требования

### 1. Установить необходимые инструменты:

```bash
# Проверьте версии (должны быть установлены):
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
node --version            # Node.js 18+
npm --version             # npm 9+
git --version             # Git 2.0+
```

### 2. Установка (если не установлено):

**Docker Desktop для macOS:**
```bash
# Скачайте с официального сайта:
# https://www.docker.com/products/docker-desktop/

# Или через Homebrew:
brew install --cask docker
```

**Node.js и npm:**
```bash
# Через Homebrew:
brew install node

# Или через nvm (рекомендуется):
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20
```

---

## 🚀 Запуск проекта

### Шаг 1: Клонирование и переход в ветку macOS

```bash
git clone https://github.com/shelestdan/guscha-project-django.git
cd guscha-project-django
git checkout macOS
```

### Шаг 2: Настройка переменных окружения

```bash
# Создайте .env файл из примера
cd guscha_django
cp .env.example .env

# Откройте .env и заполните необходимые значения
nano .env  # или используйте любой редактор
```

**Минимально необходимые переменные:**
- `SECRET_KEY` - секретный ключ Django
- `POSTGRES_PASSWORD` - пароль для базы данных
- `ADMIN_URL` - кастомный URL админки

### Шаг 3: Сборка фронтенда и запуск Docker

```bash
# Вернитесь в корень проекта
cd ..

# Сделайте скрипт исполняемым (если нужно)
chmod +x build_frontend.sh

# Запустите полную сборку и развёртывание
./build_frontend.sh
```

**Что делает скрипт:**
1. ✅ Устанавливает npm зависимости
2. ✅ Собирает React приложение
3. ✅ Копирует статику в Django директории
4. ✅ Запускает Docker контейнеры
5. ✅ Выполняет миграции базы данных
6. ✅ Собирает статические файлы (collectstatic)
7. ✅ Создаёт суперпользователя (если не существует)

### Шаг 4: Проверка работоспособности

После успешного запуска откройте в браузере:

- **Основное приложение:** http://localhost
- **Django админка:** http://localhost/secure-admin-guscha-2024/
- **API:** http://localhost/api/
- **Healthcheck nginx:** http://localhost/nginx-health

---

## 🔧 Дополнительные команды

### Работа со скриптом сборки

```bash
# Стандартная сборка
./build_frontend.sh

# Только локальная сборка (без Docker)
./build_frontend.sh --dev-mode

# Пропустить npm build (использовать существующую сборку)
./build_frontend.sh --skip-build

# Полный перезапуск контейнеров
./build_frontend.sh --force-refresh

# Перезапуск контейнеров без пересборки
./build_frontend.sh --restart-containers

# Подробное логирование
./build_frontend.sh --verbose
```

### Управление Docker контейнерами

```bash
cd guscha_django

# Просмотр логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f django
docker-compose logs -f nginx

# Перезапуск сервиса
docker-compose restart django
docker-compose restart nginx

# Остановка всех контейнеров
docker-compose down

# Запуск контейнеров
docker-compose up -d

# Пересборка образов
docker-compose build --no-cache

# Просмотр статуса контейнеров
docker-compose ps
```

### Работа с базой данных

```bash
cd guscha_django

# Вход в контейнер Django
docker-compose exec django bash

# Внутри контейнера:
python manage.py migrate                    # Применить миграции
python manage.py makemigrations             # Создать миграции
python manage.py createsuperuser            # Создать суперпользователя
python manage.py shell                      # Django shell
python manage.py collectstatic --noinput    # Собрать статику

# Выход из контейнера
exit
```

### Подключение к базе данных PostgreSQL

```bash
cd guscha_django

# Вход в PostgreSQL контейнер
docker-compose exec db psql -U guscha -d guscha_dev

# SQL команды:
\l              # Список баз данных
\dt             # Список таблиц
\q              # Выход
```

### Работа с фронтендом

```bash
cd guscha_django_frontend

# Локальная разработка (без Docker)
npm start       # Запуск dev сервера на http://localhost:3000

# Сборка для продакшена
npm run build

# Тесты
npm test

# Линтинг
npm run lint
```

---

## 📁 Структура проекта

```
guscha-project-django/
├── build_frontend.sh              # Скрипт сборки для macOS/Linux
├── build_frontend_improved.ps1    # Скрипт сборки для Windows
├── README_MACOS.md                # Этот файл
│
├── guscha_django/                 # Django backend
│   ├── .env                       # Переменные окружения (НЕ коммитить!)
│   ├── .env.example               # Пример переменных окружения
│   ├── docker-compose.dev.yml     # Docker Compose конфигурация
│   ├── Dockerfile                 # Django Dockerfile
│   ├── Dockerfile.telegram        # Telegram bot Dockerfile
│   ├── requirements.txt           # Python зависимости (полные)
│   ├── requirements-telegram.txt  # Python зависимости (только для бота)
│   ├── manage.py                  # Django management script
│   ├── config/
│   │   └── nginx.conf             # Nginx конфигурация
│   ├── scripts/
│   │   └── start.sh               # Скрипт запуска Django
│   ├── apps/                      # Django приложения
│   ├── guscha_project/            # Django проект (settings, urls)
│   ├── telegram_bot/              # Telegram bot код
│   ├── templates/                 # Django templates
│   ├── static/                    # Статика для разработки
│   └── static_root/               # Статика для продакшена (создаётся)
│
└── guscha_django_frontend/        # React frontend
    ├── public/
    ├── src/
    ├── package.json
    └── build/                     # Сборка React (создаётся)
```

---

## 🐛 Решение проблем

### Проблема: Docker не запускается

```bash
# Убедитесь что Docker Desktop запущен
open -a Docker

# Или проверьте статус:
docker ps
```

### Проблема: Порты заняты

```bash
# Проверьте какие порты используются:
lsof -i :80     # nginx
lsof -i :8000   # django
lsof -i :5432   # postgres
lsof -i :6379   # redis

# Убейте процесс занимающий порт (замените PID):
kill -9 PID
```

### Проблема: Ошибки прав доступа

```bash
# Дайте права на выполнение скриптов:
chmod +x build_frontend.sh
chmod +x guscha_django/scripts/start.sh

# Если проблемы с volume правами:
cd guscha_django
sudo chown -R $(whoami):$(whoami) static_root/
sudo chown -R $(whoami):$(whoami) media/
sudo chown -R $(whoami):$(whoami) logs/
```

### Проблема: npm install не работает

```bash
# Очистите кэш npm:
npm cache clean --force

# Удалите node_modules и переустановите:
cd guscha_django_frontend
rm -rf node_modules package-lock.json
npm install
```

### Проблема: База данных не мигрируется

```bash
cd guscha_django

# Пересоздайте базу данных:
docker-compose down -v  # ВНИМАНИЕ: Удалит все данные!
docker-compose up -d

# Или вручную выполните миграции:
docker-compose exec django python manage.py migrate
```

### Проблема: Статика не обновляется

```bash
# Полная очистка и пересборка:
./build_frontend.sh --force-refresh

# Или вручную:
cd guscha_django
docker-compose exec django python manage.py collectstatic --noinput --clear
docker-compose restart nginx
```

### Проблема: Контейнер падает сразу после старта

```bash
# Проверьте логи:
cd guscha_django
docker-compose logs django
docker-compose logs nginx

# Проверьте конфигурацию:
docker-compose config
```

---

## 🔐 Безопасность

### Перед деплоем в продакшен:

1. **Измените SECRET_KEY** в `.env`
2. **Установите DEBUG=False**
3. **Настройте ALLOWED_HOSTS**
4. **Измените ADMIN_URL** на случайный
5. **Включите SSL:**
   ```
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```
6. **Настройте резервное копирование базы данных**
7. **Включите мониторинг (Sentry)**

---

## 📚 Дополнительная документация

- **Архитектура фронтенда:** `FRONTEND_BUILD_ARCHITECTURE.md`
- **Docker улучшения:** `DOCKER_IMPROVEMENTS.md`
- **Исправления:** `CORRECTIONS.md`

---

## 🆘 Получение помощи

Если возникли проблемы:

1. Проверьте логи: `docker-compose logs`
2. Проверьте документацию в репозитории
3. Создайте Issue на GitHub
4. Проверьте переменные окружения в `.env`

---

## ✅ Чеклист первого запуска

- [ ] Docker Desktop установлен и запущен
- [ ] Node.js 18+ установлен
- [ ] Клонирован репозиторий (ветка macOS)
- [ ] Создан `.env` файл из `.env.example`
- [ ] Заполнены обязательные переменные в `.env`
- [ ] Выполнен `chmod +x build_frontend.sh`
- [ ] Запущен `./build_frontend.sh`
- [ ] Открыт http://localhost в браузере
- [ ] Проверена админка
- [ ] Созданы тестовые данные

---

**Удачного запуска! 🚀**

*Последнее обновление: 30 октября 2024*
