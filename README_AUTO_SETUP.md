# 🚀 Guscha Project - Автоматическая настройка для macOS

Этот документ описывает автоматическую настройку проекта Guscha на macOS с помощью специальных скриптов.

## 📋 Системные требования

- **macOS** 10.15+ 
- **Docker Desktop** 20.10+
- **Node.js** 18+
- **npm** 9+
- **Git** 2.0+

## 🎯 Способы запуска

### Способ 1: Полная автоматическая настройка (Рекомендуется)

```bash
# Клонируйте репозиторий и переключитесь на ветку macOS
git clone https://github.com/shelestdan/guscha-project-django.git
cd guscha-project-django
git checkout macOS

# Запустите полную автоматическую настройку
./setup_macos.sh
```

**Что делает скрипт `setup_macos.sh`:**
- ✅ Проверяет системные требования
- ✅ Настраивает окружение (.env файл)
- ✅ Собирает frontend приложение
- ✅ Собирает Docker контейнеры
- ✅ Выполняет миграции базы данных
- ✅ Создает суперпользователя
- ✅ Запускает все сервисы
- ✅ Проверяет работоспособность

### Способ 2: Через build_frontend.sh с авто-настройкой

```bash
# Клонируйте репозиторий и переключитесь на ветку macOS
git clone https://github.com/shelestdan/guscha-project-django.git
cd guscha-django-project
git checkout macOS

# Запустите с опцией --auto-setup
./build_frontend.sh --auto-setup
```

### Способ 3: Построчная настройка

```bash
# 1. Сборка frontend
./build_frontend.sh

# 2. Настройка окружения
cd guscha_django
cp .env.example .env
# Отредактируйте .env файл с реальными данными

# 3. Запуск Docker
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up -d

# 4. Миграции базы данных
docker-compose -f docker-compose.dev.yml exec django python manage.py migrate

# 5. Создание суперпользователя
docker-compose -f docker-compose.dev.yml exec django python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin@guscha.ru', 'SecureAdminPass123!')
"

# 6. Создание директории для профилирования
docker-compose -f docker-compose.dev.yml exec django mkdir -p /app/profiles
```

## 🌐 Доступ к приложению

После успешной настройки:

| Сервис | URL | Описание |
|--------|-----|----------|
| Основное приложение | http://localhost | Главное веб-приложение |
| Админ-панель | http://localhost/secure-admin-guscha-2024/ | Панель управления Django |
| API | http://localhost/api/ | REST API endpoints |
| Health Check | http://localhost/nginx-health | Проверка состояния nginx |

### 👤 Данные для входа в админку

- **Email:** `admin@guscha.ru`
- **Пароль:** `SecureAdminPass123!`

## 🔧 Управление проектом

### Основные команды

```bash
# Остановка всех контейнеров
cd guscha_django
docker-compose -f docker-compose.dev.yml down

# Перезапуск всех контейнеров
docker-compose -f docker-compose.dev.yml restart

# Просмотр логов
docker-compose -f docker-compose.dev.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.dev.yml logs -f django
docker-compose -f docker-compose.dev.yml logs -f telegram-bot

# Обновление frontend
cd ..
./build_frontend.sh

# Полная пересборка
./build_frontend.sh --force-refresh
```

### Обновление зависимостей

```bash
# Обновление frontend зависимостей
cd guscha_django_frontend
npm install
npm run build
cd ..

# Обновление backend зависимостей
cd guscha_django
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up -d
```

## 🐛 Устранение常见 проблем

### Проблема: Docker не запускается

```bash
# Перезапустите Docker Desktop
# Проверьте статус
docker ps
docker-compose ps
```

### Проблема: Frontend не собирается

```bash
# Очистите кэш npm
cd guscha_django_frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Проблема: База данных не доступна

```bash
# Перезапустите базу данных
cd guscha_django
docker-compose -f docker-compose.dev.yml restart db redis

# Проверьте подключение
docker-compose -f docker-compose.dev.yml exec db pg_isready -U guscha
```

### Проблема: Миграции не применяются

```bash
# Принудительное применение миграций
cd guscha_django
docker-compose -f docker-compose.dev.yml exec django python manage.py migrate --fake-initial
```

### Проблема: Телеграм-бот не работает

1. Проверьте токен в `.env` файле
2. Убедитесь, что токен правильный и активный
3. Перезапустите телеграм-бот:

```bash
cd guscha_django
docker-compose -f docker-compose.dev.yml restart telegram-bot
docker-compose -f docker-compose.dev.yml logs -f telegram-bot
```

## 📁 Структура проекта

```
guscha-project-django/
├── setup_macos.sh              # Скрипт полной автоматической настройки
├── build_frontend.sh           # Скрипт сборки frontend
├── guscha_django/              # Django backend
│   ├── .env                    # Конфигурация окружения
│   ├── docker-compose.dev.yml # Docker конфигурация
│   ├── Dockerfile             # Docker образ
│   └── requirements*.txt      # Python зависимости
└── guscha_django_frontend/     # React frontend
    ├── package.json           # Node.js зависимости
    └── src/                   # Исходный код
```

## 🔄 Обновление проекта

Для обновления до последней версии:

```bash
# Получите последние изменения
git pull origin macOS

# Перезапустите с авто-настройкой
./setup_macos.sh
```

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте системные требования
2. Убедитесь, что все сервисы запущены: `docker-compose ps`
3. Проверьте логи: `docker-compose logs -f`
4. Попробуйте полную пересборку: `./setup_macos.sh`

---

**🎉 Готово!** После выполнения этих шагов проект будет полностью настроен и готов к работе на macOS.
