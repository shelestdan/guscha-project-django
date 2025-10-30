# ✅ macOS Setup Checklist

## Перед первым запуском

### 1. Установка необходимых инструментов

```bash
# Проверьте установленные инструменты:
docker --version          # Требуется: 20.10+
docker-compose --version  # Требуется: 2.0+
node --version            # Требуется: 18+
npm --version             # Требуется: 9+
git --version             # Требуется: 2.0+
```

**Если что-то не установлено:**

```bash
# Docker Desktop
brew install --cask docker

# Node.js (через nvm - рекомендуется)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20

# Или напрямую
brew install node
```

---

### 2. Настройка проекта

```bash
# 1. Клонирование репозитория
git clone https://github.com/shelestdan/guscha-project-django.git
cd guscha-project-django

# 2. Переключение на ветку macOS
git checkout macOS

# 3. Создание .env файла
cd guscha_django
cp .env.example .env

# 4. Редактирование .env (ОБЯЗАТЕЛЬНО!)
nano .env  # или используйте VS Code, TextEdit и т.д.
```

**Минимальные настройки в .env:**
```bash
SECRET_KEY=ваш-секретный-ключ-измените-это
POSTGRES_PASSWORD=надёжный-пароль
ADMIN_URL=ваш-секретный-путь-админки
```

---

### 3. Права доступа на скрипты

```bash
# Вернитесь в корень проекта
cd ..

# Дайте права на выполнение
chmod +x build_frontend.sh
chmod +x guscha_django/scripts/start.sh
```

---

### 4. Создание необходимых директорий

```bash
cd guscha_django

# Создайте директории для данных
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p logs
mkdir -p media
mkdir -p static_root
mkdir -p backups

# Проверьте структуру
ls -la
```

---

### 5. Запуск Docker Desktop

```bash
# Откройте Docker Desktop
open -a Docker

# Подождите пока Docker запустится (иконка в menu bar станет активной)

# Проверьте что Docker работает
docker ps
```

---

## Первый запуск

### Опция 1: Автоматический запуск (рекомендуется)

```bash
# Из корня проекта
./build_frontend.sh
```

**Что произойдёт:**
1. ✅ Установка npm зависимостей
2. ✅ Сборка React приложения (`npm run build`)
3. ✅ Копирование файлов в Django директории
4. ✅ Запуск Docker контейнеров
5. ✅ Создание базы данных и миграции
6. ✅ Сбор статических файлов (collectstatic)
7. ✅ Создание суперпользователя

**Время выполнения:** 5-10 минут при первом запуске

---

### Опция 2: Пошаговый запуск (если нужен контроль)

```bash
# 1. Сборка фронтенда
cd guscha_django_frontend
npm install
npm run build
cd ..

# 2. Запуск Docker
cd guscha_django
docker-compose -f docker-compose.dev.yml up -d --build

# 3. Ожидание запуска (30-60 секунд)
sleep 30

# 4. Проверка логов
docker-compose logs -f
```

---

## Проверка работоспособности

### 1. Проверьте статус контейнеров

```bash
cd guscha_django
docker-compose ps
```

**Должны быть запущены:**
- ✅ guscha-nginx-dev (nginx)
- ✅ guscha-django-dev (django)
- ✅ guscha-db-dev (postgres)
- ✅ guscha-redis-dev (redis)
- ✅ guscha-telegram-bot-dev (telegram-bot)
- ✅ guscha-postgres-exporter (metrics)

### 2. Откройте в браузере

- **Главная страница:** http://localhost
- **Django админка:** http://localhost/secure-admin-guscha-2024/
- **API endpoints:** http://localhost/api/
- **Nginx health:** http://localhost/nginx-health

### 3. Проверьте логи

```bash
# Все логи
docker-compose logs

# Только Django
docker-compose logs django

# Только nginx
docker-compose logs nginx

# В реальном времени
docker-compose logs -f
```

---

## Создание суперпользователя

```bash
cd guscha_django

# Войдите в контейнер Django
docker-compose exec django bash

# Создайте суперпользователя
python manage.py createsuperuser

# Следуйте инструкциям:
# Email: admin@example.com
# Password: ваш_пароль
# Password (again): ваш_пароль

# Выход из контейнера
exit
```

---

## Частые проблемы и решения

### ❌ Проблема: "Cannot connect to Docker daemon"

**Решение:**
```bash
# Откройте Docker Desktop
open -a Docker

# Подождите 30 секунд
sleep 30

# Попробуйте снова
docker ps
```

---

### ❌ Проблема: "Port 80 is already in use"

**Решение:**
```bash
# Найдите процесс занимающий порт 80
sudo lsof -i :80

# Убейте процесс (замените PID на реальный)
sudo kill -9 PID

# Или измените порт в docker-compose.dev.yml:
# ports:
#   - "8080:80"  # вместо "80:80"
```

---

### ❌ Проблема: "Permission denied: './build_frontend.sh'"

**Решение:**
```bash
# Дайте права на выполнение
chmod +x build_frontend.sh

# Попробуйте снова
./build_frontend.sh
```

---

### ❌ Проблема: "Module not found" при npm install

**Решение:**
```bash
cd guscha_django_frontend

# Удалите node_modules и package-lock.json
rm -rf node_modules package-lock.json

# Очистите npm кэш
npm cache clean --force

# Переустановите зависимости
npm install
```

---

### ❌ Проблема: База данных не создаётся

**Решение:**
```bash
cd guscha_django

# Остановите и удалите все контейнеры и volumes
docker-compose down -v

# ВНИМАНИЕ: Это удалит все данные!

# Запустите заново
docker-compose up -d

# Подождите 30 секунд
sleep 30

# Выполните миграции вручную
docker-compose exec django python manage.py migrate
```

---

### ❌ Проблема: Статика не загружается (404)

**Решение:**
```bash
# Пересоберите статику
./build_frontend.sh --force-refresh

# Или вручную:
cd guscha_django
docker-compose exec django python manage.py collectstatic --noinput --clear
docker-compose restart nginx
```

---

### ❌ Проблема: "Image not found" или "No such file"

**Решение:**
```bash
cd guscha_django

# Пересоберите образы
docker-compose build --no-cache

# Запустите
docker-compose up -d
```

---

## Полезные команды

### Перезапуск сервисов

```bash
cd guscha_django

# Перезапуск всех контейнеров
docker-compose restart

# Перезапуск конкретного сервиса
docker-compose restart django
docker-compose restart nginx
```

### Просмотр логов

```bash
# Все логи
docker-compose logs -f

# Последние 100 строк
docker-compose logs --tail=100

# Конкретный сервис
docker-compose logs -f django
```

### Работа с базой данных

```bash
# Подключение к PostgreSQL
docker-compose exec db psql -U guscha -d guscha_dev

# Бэкап базы данных
docker-compose exec db pg_dump -U guscha guscha_dev > backup.sql

# Восстановление из бэкапа
cat backup.sql | docker-compose exec -T db psql -U guscha -d guscha_dev
```

### Очистка Docker

```bash
# Удаление неиспользуемых образов
docker image prune -a

# Удаление неиспользуемых volumes
docker volume prune

# Полная очистка (ВНИМАНИЕ: удалит всё!)
docker system prune -a --volumes
```

---

## Следующие шаги

После успешного запуска:

1. ✅ Войдите в админку и создайте тестовые данные
2. ✅ Протестируйте основные функции
3. ✅ Настройте Telegram бота (если используете)
4. ✅ Настройте резервное копирование базы данных
5. ✅ Изучите документацию API

---

## Остановка проекта

```bash
cd guscha_django

# Остановка без удаления данных
docker-compose stop

# Остановка с удалением контейнеров (данные сохраняются)
docker-compose down

# Полное удаление (включая volumes - данные будут потеряны!)
docker-compose down -v
```

---

## Запуск после остановки

```bash
# Просто запустите контейнеры
cd guscha_django
docker-compose up -d

# Или используйте скрипт (если нужна пересборка фронтенда)
cd ..
./build_frontend.sh --skip-build
```

---

**Готово! Проект должен работать на http://localhost** 🎉

*Если возникли проблемы, откройте Issue на GitHub или обратитесь к основной документации в README_MACOS.md*
