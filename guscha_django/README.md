# Guscha Django Project

Проект с интеграцией React фронтенда и Django бэкенда.

## 🚀 Быстрый запуск

### Локальная разработка

#### Windows (PowerShell)
```powershell
.\build_and_run.ps1
```

#### Linux/macOS (Bash)
```bash
./build_and_run.sh
```

### Docker

#### Запуск с Docker Compose
```bash
docker-compose up --build
```

#### Только Django контейнер
```bash
docker build -t guscha-django .
docker run -p 8000:8000 guscha-django
```

## 📁 Структура проекта

```
guscha_django/
├── guscha_project/          # Django настройки
├── core/                    # Основное Django приложение
├── static_root/             # Собранные статические файлы
├── Dockerfile              # Docker конфигурация
├── docker-compose.yml      # Docker Compose конфигурация
├── build_and_run.ps1       # PowerShell скрипт сборки
├── build_and_run.sh        # Bash скрипт сборки
└── requirements.txt        # Python зависимости

guscha_django_frontend/
├── src/                    # React исходники
├── build/                  # Собранный фронтенд
├── package.json           # Node.js зависимости
└── ...
```

## 🔧 Ручная сборка

### 1. Сборка фронтенда
```bash
cd ../guscha_django_frontend
npm install
npm run build
```

### 2. Копирование статических файлов
```bash
cd ../guscha_django
cp -r ../guscha_django_frontend/build/* ./static_root/
cp -r ../guscha_django_frontend/build/static/* ./static_root/
```

### 3. Сборка Django статики
```bash
python manage.py collectstatic --noinput
```

### 4. Запуск сервера
```bash
python manage.py runserver 0.0.0.0:8000
```

## 🌐 Доступ к приложению

- **Локально**: http://localhost:8000
- **Docker**: http://localhost:8000
- **С nginx**: http://localhost:80

## 📝 Примечания

- Фронтенд автоматически собирается в `build/` директорию
- Статические файлы копируются в `static_root/` для Django
- Django обслуживает статические файлы в режиме разработки
- Для продакшена рекомендуется использовать nginx для статики

## 🐛 Решение проблем

### Статические файлы не загружаются
1. Убедитесь, что фронтенд собран: `npm run build`
2. Проверьте копирование файлов в `static_root/`
3. Запустите `python manage.py collectstatic --noinput`
4. Перезапустите Django сервер

### Docker проблемы
1. Очистите кэш: `docker system prune -a`
2. Пересоберите образы: `docker-compose up --build --force-recreate`

## 🔄 Автоматизация

Используйте предоставленные скрипты для автоматической сборки и запуска:
- `build_and_run.ps1` для Windows
- `build_and_run.sh` для Linux/macOS
- `docker-compose.yml` для контейнеризации