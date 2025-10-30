# 🔍 Полный аудит проекта Guscha

## 📊 Общая статистика

### Размер проекта: **1,467 GB (1467 MB)**

---

## 📁 Распределение по директориям

| Директория | Размер | % от общего | Статус |
|------------|--------|-------------|--------|
| **guscha_django_frontend** | 1,028 GB | 70% | ⚠️ Оптимизировать |
| **guscha_django** | 412 MB | 28% | ⚠️ Оптимизировать |
| node_modules (корень) | 27 MB | 2% | ❌ Удалить |
| Остальное | 0.3 MB | <1% | ✅ OK |

---

## 🎯 Детальный анализ guscha_django (412 MB)

| Директория | Размер | Нужна? | Действие |
|------------|--------|--------|----------|
| **media/** | 104 MB | ✅ Да | Оставить (пользовательские файлы) |
| **data/** | 99 MB | ✅ Да | Оставить (БД данные) |
| **profiles/** | 87 MB | ❓ Проверить | Профили Django Silk? |
| **venv/** | 83 MB | ❌ Нет | **УДАЛИТЬ из git!** |
| **logs/** | 16 MB | ❌ Нет | **Очистить старые логи** |
| **static_root/** | 12 MB | ✅ Да | Оставить (собранная статика) |
| **apps/** | 6 MB | ✅ Да | Оставить (код приложения) |
| **static/** | 3 MB | ✅ Да | Оставить (исходная статика) |
| **telegram_bot/** | 0.7 MB | ✅ Да | Оставить (код бота) |
| **guscha_project/** | 0.13 MB | ✅ Да | Оставить (настройки) |
| **templates/** | 0.03 MB | ✅ Да | Оставить (шаблоны) |
| Остальное | <0.1 MB | ✅ Да | Оставить |

### 🚨 Критические проблемы:

1. **venv/** (83 MB) - **НЕ ДОЛЖЕН быть в git!**
2. **profiles/** (87 MB) - Профили Django Silk, можно очистить
3. **logs/** (16 MB) - Старые логи, можно очистить

---

## 🎨 Детальный анализ guscha_django_frontend (1,028 GB)

| Директория | Размер | Нужна? | Действие |
|------------|--------|--------|----------|
| **node_modules/** | 1,017 GB | ❌ Нет | **УДАЛИТЬ из git!** |
| **src/** | 3.7 MB | ✅ Да | Оставить (исходный код) |
| **build/** | 3.3 MB | ❌ Нет | **УДАЛИТЬ из git!** |
| **coverage/** | 3.2 MB | ❌ Нет | **УДАЛИТЬ из git!** |
| **public/** | 0.02 MB | ✅ Да | Оставить |

### 🚨 Критические проблемы:

1. **node_modules/** (1,017 GB) - **НЕ ДОЛЖЕН быть в git!**
2. **build/** (3.3 MB) - Собранные файлы, не нужны в git
3. **coverage/** (3.2 MB) - Отчёты тестов, не нужны в git

---

## 📦 Анализ Python пакетов (374 шт.)

### Категории пакетов:

#### ✅ Необходимые (используются в коде):

**Django Core (15 пакетов):**
- Django
- djangorestframework
- django-filter
- django-cors-headers
- asgiref
- sqlparse
- и др.

**Безопасность (25 пакетов):**
- django-axes
- django-guardian
- django-defender
- django-ratelimit
- django-recaptcha
- django-csp
- django-honeypot
- django-security
- cryptography
- bcrypt
- и др.

**Аутентификация (20 пакетов):**
- django-allauth
- dj-rest-auth
- djangorestframework-simplejwt
- django-otp
- PyJWT
- pyotp
- и др.

**База данных (10 пакетов):**
- psycopg2-binary
- redis
- django-redis
- и др.

**Telegram (35 пакетов):**
- python-telegram-bot
- httpx
- APScheduler
- и транзитивные зависимости

**Celery (20 пакетов):**
- celery
- django-celery-beat
- django-celery-results
- kombu
- billiard
- и др.

**AWS/Storage (20 пакетов):**
- boto3
- botocore
- s3transfer
- django-dbbackup
- и др.

**Утилиты (30 пакетов):**
- Pillow
- requests
- python-slugify
- python-dotenv
- str2bool
- phonenumbers
- pytz
- structlog
- и др.

**Админка (20 пакетов):**
- django-unfold
- django-simple-history
- django-import-export
- и др.

**Формы/UI (10 пакетов):**
- django-crispy-forms
- crispy-tailwind
- django-money
- и др.

**WSGI (5 пакетов):**
- gunicorn
- и зависимости

**Транзитивные зависимости (164 пакета):**
- Зависимости вышеперечисленных пакетов

#### ❌ Неиспользуемые (можно удалить):

**Альтернативные админки (4 пакета + зависимости ~20):**
- django-admin-datta
- django-adminlte3
- django-jazzmin
- django-volt-admin

**Flask пакеты (2 пакета + зависимости ~10):**
- Flask-JWT-Extended
- Flask-Bcrypt

**Другие неиспользуемые (~10 пакетов):**
- django-eventstream
- django-grip
- ansible (если не используется для деплоя)
- и др.

**Итого можно удалить:** ~40-50 пакетов

---

## 🎯 План оптимизации

### Шаг 1: Обновите .gitignore (КРИТИЧНО!)

```bash
# Проверьте что эти директории в .gitignore:
cat .gitignore | grep -E "venv|node_modules|build|coverage|profiles|logs|data"
```

Должно быть:
```gitignore
# Python
venv/
*.pyc
__pycache__/

# Node.js
node_modules/
build/
coverage/

# Django
logs/
*.log
profiles/
data/
media/
static_root/
db.sqlite3
```

### Шаг 2: Удалите из git (если попали)

```bash
# Проверьте что в git:
git ls-files | grep -E "venv|node_modules|build|coverage"

# Если что-то найдено - удалите:
git rm -r --cached guscha_django/venv/
git rm -r --cached guscha_django_frontend/node_modules/
git rm -r --cached guscha_django_frontend/build/
git rm -r --cached guscha_django_frontend/coverage/
git rm -r --cached guscha_django/profiles/
git rm -r --cached guscha_django/logs/
git rm -r --cached guscha_django/data/

git commit -m "chore: Remove build artifacts and dependencies from git"
```

### Шаг 3: Очистите локально

```bash
# Очистите старые логи
Remove-Item guscha_django/logs/*.log -Force

# Очистите профили Django Silk
Remove-Item guscha_django/profiles/* -Recurse -Force

# Пересоздайте node_modules (если нужно)
cd guscha_django_frontend
Remove-Item node_modules -Recurse -Force
npm install
```

### Шаг 4: Удалите неиспользуемые Python пакеты

```bash
cd guscha_django

# Активируйте виртуальное окружение
.\venv\Scripts\activate

# Удалите альтернативные админки
pip uninstall -y django-admin-datta django-adminlte3 django-jazzmin django-volt-admin

# Удалите Flask пакеты
pip uninstall -y Flask-JWT-Extended Flask-Bcrypt Flask

# Удалите другие неиспользуемые
pip uninstall -y django-eventstream django-grip

# Обновите requirements
pip freeze > requirements-clean.txt
```

### Шаг 5: Создайте чистое окружение

```bash
# Создайте новое виртуальное окружение
python -m venv venv_clean

# Активируйте
venv_clean\Scripts\activate

# Установите только необходимое
pip install -r requirements.txt

# Проверьте количество пакетов
pip list | Measure-Object -Line
```

---

## 📊 Ожидаемые результаты после оптимизации

### Размер проекта:

| Что | Было | Станет | Экономия |
|-----|------|--------|----------|
| **Общий размер** | 1,467 GB | ~50 MB | **97%** |
| guscha_django | 412 MB | ~20 MB | 95% |
| guscha_django_frontend | 1,028 GB | ~4 MB | 99.6% |
| Python пакетов | 374 | ~320 | 54 шт. |

### Что останется в git:

- ✅ Исходный код Python (~10 MB)
- ✅ Исходный код React (~4 MB)
- ✅ Конфигурационные файлы (~1 MB)
- ✅ Документация (~5 MB)
- ✅ Статические файлы (~3 MB)
- ✅ Шаблоны (~0.1 MB)

**Итого:** ~25-30 MB (вместо 1,467 GB!)

---

## 🔍 Детальный анализ неиспользуемых пакетов

### Как проверить что пакет используется:

```bash
# Поиск импортов в коде
Get-ChildItem -Path guscha_django -Include "*.py" -Recurse | Select-String -Pattern "import django_admin_datta|from django_admin_datta"

# Если ничего не найдено - пакет не используется
```

### Список пакетов для проверки:

1. **django-admin-datta** - альтернативная админка
2. **django-adminlte3** - альтернативная админка
3. **django-jazzmin** - альтернативная админка
4. **django-volt-admin** - альтернативная админка
5. **Flask-JWT-Extended** - Flask пакет
6. **Flask-Bcrypt** - Flask пакет
7. **django-eventstream** - Server-Sent Events
8. **django-grip** - Realtime push
9. **ansible** - Автоматизация (если не используется)
10. **bandit** - Security linter (dev-зависимость)

---

## 📝 Скрипт автоматической очистки

Создам скрипт для автоматической очистки:

```powershell
# cleanup.ps1
Write-Host "=== Очистка проекта ===" -ForegroundColor Cyan

# 1. Очистка логов
Write-Host "Очистка логов..." -ForegroundColor Yellow
Remove-Item guscha_django/logs/*.log -Force -ErrorAction SilentlyContinue

# 2. Очистка профилей
Write-Host "Очистка профилей Django Silk..." -ForegroundColor Yellow
Remove-Item guscha_django/profiles/* -Recurse -Force -ErrorAction SilentlyContinue

# 3. Очистка build артефактов
Write-Host "Очистка build артефактов..." -ForegroundColor Yellow
Remove-Item guscha_django_frontend/build -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item guscha_django_frontend/coverage -Recurse -Force -ErrorAction SilentlyContinue

# 4. Очистка Python cache
Write-Host "Очистка Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Include __pycache__,*.pyc -Recurse | Remove-Item -Recurse -Force

# 5. Очистка node_modules (опционально)
# Remove-Item guscha_django_frontend/node_modules -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Очистка завершена!" -ForegroundColor Green
```

---

## ✅ Checklist оптимизации

### Перед коммитом:
- [ ] venv/ в .gitignore
- [ ] node_modules/ в .gitignore
- [ ] build/ в .gitignore
- [ ] coverage/ в .gitignore
- [ ] logs/ в .gitignore
- [ ] profiles/ в .gitignore
- [ ] data/ в .gitignore
- [ ] media/ в .gitignore (кроме примеров)
- [ ] static_root/ в .gitignore

### Удалить из git:
- [ ] guscha_django/venv/
- [ ] guscha_django_frontend/node_modules/
- [ ] guscha_django_frontend/build/
- [ ] guscha_django_frontend/coverage/
- [ ] guscha_django/profiles/
- [ ] guscha_django/logs/
- [ ] guscha_django/data/

### Удалить неиспользуемые пакеты:
- [ ] django-admin-datta
- [ ] django-adminlte3
- [ ] django-jazzmin
- [ ] django-volt-admin
- [ ] Flask-JWT-Extended
- [ ] Flask-Bcrypt
- [ ] django-eventstream
- [ ] django-grip

### После оптимизации:
- [ ] Размер проекта < 50 MB
- [ ] Python пакетов ~320
- [ ] Все тесты проходят
- [ ] Приложение запускается

---

## 🎯 Итоговые рекомендации

### 1. КРИТИЧНО - Обновите .gitignore
Убедитесь что venv/, node_modules/, build/ и другие артефакты НЕ попадают в git.

### 2. Удалите из git
Если эти директории уже в git - удалите их командой `git rm -r --cached`.

### 3. Очистите неиспользуемые пакеты
Удалите ~40-50 неиспользуемых пакетов.

### 4. Регулярная очистка
Запускайте cleanup.ps1 перед каждым коммитом.

### 5. Используйте Docker
В Docker все зависимости устанавливаются автоматически, не нужно хранить их в git.

---

## 📞 Следующие шаги

1. Прочитайте этот отчёт
2. Выполните план оптимизации
3. Проверьте результаты
4. Закоммитьте изменения

---

**Проект можно оптимизировать с 1.5 GB до 30 MB! 🚀**
