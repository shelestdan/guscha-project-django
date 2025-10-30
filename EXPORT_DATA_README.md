# 📦 Экспорт данных для тестирования

## ⚠️ ВАЖНО: Только для разработки!

Этот коммит содержит:
- ✅ Медиа файлы (`media/`)
- ✅ Данные базы данных (дамп)

**Не используйте это в production!** Это только для тестирования на другой системе.

---

## Структура медиа файлов

```
guscha_django/media/
├── backgrounds/        # Фоновые изображения
├── collections/        # Изображения коллекций
├── preorders/          # Изображения предзаказов
├── products/           # Изображения продуктов
├── slideshow/          # Изображения слайдшоу
├── uploads/            # Прочие загрузки
└── test-image.jpg      # Тестовое изображение
```

---

## Как восстановить данные на новой системе

### 1. Клонировать репозиторий (ветка macOS)
```bash
git clone https://github.com/shelestdan/guscha-project-django.git
cd guscha-project-django
git checkout macOS
```

### 2. Запустить проект
```bash
# На macOS/Linux:
./build_frontend.sh

# На Windows:
.\build_frontend_improved.ps1
```

### 3. Медиа файлы будут автоматически доступны
Медиа файлы уже находятся в `guscha_django/media/` и будут смонтированы в Docker контейнер через volume.

### 4. Восстановить дамп БД (если нужно)

**Если БД уже создана:**
```bash
cd guscha_django

# Остановить контейнеры
docker-compose -f docker-compose.dev.yml down

# Удалить старую БД
docker volume rm guscha_django_postgres_data_dev

# Запустить заново
docker-compose -f docker-compose.dev.yml up -d

# Дождаться запуска (30 секунд)
sleep 30

# Восстановить дамп (если он есть)
cat db_dump.sql | docker-compose -f docker-compose.dev.yml exec -T db psql -U guscha -d guscha_dev
```

**Или создать новую БД с миграциями:**
```bash
# Применить миграции
docker-compose -f docker-compose.dev.yml exec django python manage.py migrate

# Создать суперпользователя
docker-compose -f docker-compose.dev.yml exec django python manage.py createsuperuser
```

---

## Создание дампа БД (для экспорта)

Если вам нужно создать дамп текущей БД:

```bash
cd guscha_django

# Создать дамп
docker-compose -f docker-compose.dev.yml exec db pg_dump -U guscha -d guscha_dev > db_dump.sql

# Добавить в git (ТОЛЬКО для разработки!)
git add -f db_dump.sql
git commit -m "Add database dump for testing"
git push origin macOS
```

---

## Удаление данных из репозитория (перед production)

Когда закончите тестирование, ОБЯЗАТЕЛЬНО удалите данные:

```bash
# Удалить медиа файлы из git
git rm -r --cached guscha_django/media/
git rm --cached db_dump.sql

# Восстановить .gitignore
git add .gitignore

# Закоммитить
git commit -m "Remove media and database dump from git"
git push origin macOS
```

---

## ⚠️ Безопасность

**НЕ делайте это в production!**

Причины:
- 🚫 Медиа файлы могут быть большими
- 🚫 База данных может содержать пользовательские данные
- 🚫 Это увеличивает размер репозитория
- 🚫 История git сохранит все файлы навсегда

**Используйте это ТОЛЬКО для:**
- ✅ Локального тестирования
- ✅ Разработки на нескольких устройствах
- ✅ Приватных репозиториев
- ✅ Временного экспорта данных

---

## Альтернативные способы переноса данных

### 1. Через облачное хранилище
```bash
# Создать архив
tar -czf project_data.tar.gz guscha_django/media/ db_dump.sql

# Загрузить на Google Drive, Dropbox, etc.
```

### 2. Через Docker volumes
```bash
# Экспорт volume
docker run --rm -v guscha_django_postgres_data_dev:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data.tar.gz /data

# Импорт на другой системе
docker run --rm -v guscha_django_postgres_data_dev:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_data.tar.gz -C /
```

### 3. Через fixtures Django
```bash
# Экспорт данных
docker-compose exec django python manage.py dumpdata > fixtures.json

# Импорт данных
docker-compose exec django python manage.py loaddata fixtures.json
```

---

**Дата экспорта:** 30 октября 2024  
**Ветка:** macOS  
**Статус:** Только для разработки и тестирования
