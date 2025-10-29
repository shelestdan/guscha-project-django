# Отчет: Подготовка проекта для Mac (с сохранением совместимости с Windows)

## 🎯 Цель
Сделать проект запускаемым на Mac **БЕЗ** нарушения работы на Windows.

## ✅ Что уже работает хорошо

1. **Статические файлы** - правильная структура и конфигурация
2. **CORS/CSRF** - корректные настройки для обеих платформ
3. **Nginx конфигурация** - правильная маршрутизация
4. **Dockerfile** - multi-stage build совместим с обеими платформами
5. **axiosInstance.js** - автоматическое определение baseURL работает везде

## ⚠️ Критические изменения (обязательные)

### 1. Docker Volumes (docker-compose.dev.yml)

**Проблема:** 
```yaml
volumes:
  postgres_data_dev:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/postgres
```
Эти `driver_opts` не работают на Mac.

**Решение (работает на Windows + Mac):**
```yaml
volumes:
  postgres_data_dev:
    driver: local
    # Убрать driver_opts полностью
  redis_data_dev:
    driver: local
    # Убрать driver_opts полностью
```

### 2. Platform для M1/M2 Mac (опционально)

**Проблема:** На Mac M1/M2 могут быть warning о platform.

**Решение (не влияет на Windows):**
Создать отдельный файл `docker-compose.mac.yml`:
```yaml
version: '3.8'

services:
  django:
    platform: linux/amd64
  
  telegram-bot:
    platform: linux/amd64
```

Использование:
```bash
# На Mac M1/M2
docker-compose -f docker-compose.dev.yml -f docker-compose.mac.yml up

# На Windows (как обычно)
docker-compose -f docker-compose.dev.yml up
```

## 📝 Рекомендуемые изменения (не обязательные)

### 1. Создать .env.example

Создать файл с безопасными значениями по умолчанию (работает на обеих платформах):

```env
# Django settings
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,guscha-django,nginx
SECRET_KEY=your-secret-key-here-change-in-production

# Database
POSTGRES_DB=guscha_dev
POSTGRES_USER=guscha
POSTGRES_PASSWORD=change-this-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# CORS (для разработки)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:80

# Admin
ADMIN_URL=your-custom-admin-url/
```

### 2. Обновить .gitignore

Добавить Mac-специфичные файлы (уже есть Windows файлы):

```gitignore
# Mac
.DS_Store
.AppleDouble
.LSOverride
```

### 3. Создать скрипт для Mac

Создать `deploy.sh` (аналог `build_frontend_improved.ps1` для Mac):

```bash
#!/bin/bash
# deploy.sh - Deployment script for Mac/Linux

echo "🚀 Building and deploying..."

# Build frontend
cd guscha_django_frontend
npm install
npm run build
cd ..

# Copy static files
cp -r guscha_django_frontend/build/* guscha_django/static_root/

# Start Docker
cd guscha_django
docker-compose -f docker-compose.dev.yml up -d

# Wait and collect static
sleep 10
docker-compose -f docker-compose.dev.yml exec -T django python manage.py collectstatic --noinput

echo "✅ Done! Application: http://localhost"
```

## 🚫 Что НЕ нужно менять

1. **НЕ добавлять** `:cached` или `:delegated` к volumes - они игнорируются на Windows
2. **НЕ менять** пути в Dockerfile - они уже кроссплатформенные
3. **НЕ менять** settings.py пути - используют `Path` объекты (работают везде)
4. **НЕ менять** nginx.conf - работает одинаково на обеих платформах
5. **НЕ менять** существующий `build_frontend_improved.ps1` - он нужен для Windows

## 📋 Чеклист для проверки на Mac

После внесения изменений:

```bash
# 1. Проверить Docker Desktop запущен
docker info

# 2. Собрать фронтенд
cd guscha_django_frontend
npm install
npm run build
cd ..

# 3. Скопировать статику
cp -r guscha_django_frontend/build/* guscha_django/static_root/

# 4. Запустить Docker
cd guscha_django
docker-compose -f docker-compose.dev.yml up -d

# 5. Проверить статус
docker-compose ps

# 6. Проверить логи
docker-compose logs --tail=50

# 7. Проверить приложение
curl http://localhost/nginx-health
open http://localhost
```

## 🎯 Минимальные изменения для запуска на Mac

Если нужно **прямо сейчас** запустить на Mac с минимальными изменениями:

1. Открыть `guscha_django/docker-compose.dev.yml`
2. Найти секцию `volumes:` в конце файла
3. Удалить `driver_opts` из `postgres_data_dev` и `redis_data_dev`:

```yaml
volumes:
  redis_data_dev:
    driver: local
    # Удалить эти 3 строки:
    # driver_opts:
    #   type: none
    #   o: bind
    #   device: ./data/redis
  postgres_data_dev:
    driver: local
    # Удалить эти 3 строки:
    # driver_opts:
    #   type: none
    #   o: bind
    #   device: ./data/postgres
```

4. Сохранить и запустить:
```bash
cd guscha_django
docker-compose -f docker-compose.dev.yml up -d
```

**Это изменение безопасно для Windows** - Docker просто будет использовать named volumes вместо bind mounts.

## 📚 Дополнительная информация

- `host.docker.internal` работает на Mac и Windows (не нужны отдельные .env файлы)
- Docker Desktop для Mac автоматически эмулирует x86_64 на M1/M2
- Все пути в проекте используют forward slashes `/` (работают на обеих платформах)
- PostgreSQL и Redis volumes будут храниться в Docker managed volumes (безопаснее и быстрее)

## 🔗 Следующие шаги

1. Внести минимальные изменения в docker-compose.dev.yml (volumes)
2. Протестировать на Mac
3. Убедиться что всё ещё работает на Windows
4. Создать документацию (опционально)
5. Создать скрипты для Mac (опционально)
