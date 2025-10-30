# Архитектура сборки и развёртывания фронтенда

## Полная картина процесса

Этот документ описывает **реальную** архитектуру сборки фронтенда в вашем проекте на основе анализа `build_frontend_improved.ps1` и Docker конфигурации.

---

## 📋 Процесс сборки и развёртывания

### Этап 1: Локальная сборка React приложения

**Скрипт:** `build_frontend_improved.ps1`

```
guscha_django_frontend/
├── src/              # Исходники React
├── package.json
└── build/            # Результат npm run build
    ├── index.html
    ├── static/
    │   ├── css/
    │   ├── js/
    │   └── media/
    ├── favicon.ico
    ├── manifest.json
    └── robots.txt
```

**Что делает скрипт:**

1. **Сборка (`npm run build`):**
   ```powershell
   cd guscha_django_frontend
   npm install
   npm run build  # → создаёт build/
   ```

2. **Копирование в две директории:**
   
   **a) `guscha_django/static/` (для разработки):**
   ```powershell
   build/ → guscha_django/static/
   ```
   
   **b) `guscha_django/static_root/` (для продакшена):**
   ```powershell
   build/ → guscha_django/static_root/
   ```

3. **Специальная обработка файлов:**
   - Корневые файлы: `index.html`, `favicon.ico`, `manifest.json`, `robots.txt`
   - Статика: `build/static/*` → копируется целиком
   - Важный файл: `axiosConfig.js` - сохраняется и восстанавливается

4. **Внедрение axiosConfig.js в index.html:**
   ```html
   <head>
     ...
     <script src="/static/js/axiosConfig.js"></script>
   </head>
   ```

---

### Этап 2: Docker сборка и collectstatic

**Dockerfile процесс:**

```dockerfile
# Строка 78: Копирование static/ в контейнер
COPY --chown=app:app static/ $APP_HOME/static/

# При запуске контейнера:
# start.sh строка 28: Выполняется collectstatic
python manage.py collectstatic --noinput
```

**Что происходит в Docker:**

1. **При сборке образа:**
   ```
   guscha_django/static/ → /app/static/ (внутри контейнера)
   ```

2. **При запуске контейнера (`start.sh`):**
   ```bash
   # Очистка static_root
   rm -rf /app/static_root/*
   mkdir -p /app/static_root
   
   # Django collectstatic собирает:
   # /app/static/ + Django админка → /app/static_root/
   python manage.py collectstatic --noinput
   ```

3. **Маппинг volumes (docker-compose.dev.yml):**
   ```yaml
   django:
     volumes:
       - ./static_root:/app/static_root  # Двусторонняя синхронизация
   
   nginx:
     volumes:
       - ./static_root:/var/www/react:ro  # Только чтение
   ```

---

### Этап 3: Nginx раздаёт статику

**nginx.conf процесс:**

```nginx
server {
    listen 80;
    root /var/www/react;  # = guscha_django/static_root/

    # React статика
    location /static/css/ {
        alias /var/www/react/css/;
    }
    
    location /static/js/ {
        alias /var/www/react/js/;
    }
    
    # Корневые файлы React
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Django API
    location /api/ {
        proxy_pass http://django:8000;
    }
}
```

---

## 🔄 Полная схема потока данных

```
┌─────────────────────────────────────────────────────────────────┐
│ ЛОКАЛЬНАЯ РАЗРАБОТКА                                            │
│                                                                 │
│  guscha_django_frontend/                                        │
│       npm run build                                             │
│            ↓                                                    │
│       build/                                                    │
│            ↓                                                    │
│  build_frontend_improved.ps1                                    │
│            ↓                                                    │
│  ┌─────────────────┬─────────────────┐                        │
│  ↓                 ↓                 ↓                          │
│ static/    static_root/      templates/                        │
│ (dev)      (production)                                         │
└────┬────────────────┬─────────────────────────────────────────┘
     │                │
     │                │
┌────▼────────────────▼────────────────────────────────────────┐
│ DOCKER COMPOSE                                                │
│                                                               │
│  docker-compose build  (копирует static/ в образ)            │
│  docker-compose up -d  (запускает контейнеры)                │
│                                                               │
│  ┌───────────────────────────────────────┐                  │
│  │ django контейнер                      │                  │
│  │                                       │                  │
│  │  start.sh:                            │                  │
│  │    ↓ очистка /app/static_root/       │                  │
│  │    ↓ collectstatic                    │                  │
│  │    ↓ /app/static/ → /app/static_root/│                  │
│  │         +                              │                  │
│  │    Django админка → /app/static_root/ │                  │
│  │                                       │                  │
│  │  volumes:                             │                  │
│  │    ./static_root ↔ /app/static_root  │                  │
│  └───────────────────┬───────────────────┘                  │
│                      │                                       │
│  ┌───────────────────▼───────────────────┐                  │
│  │ nginx контейнер                       │                  │
│  │                                       │                  │
│  │  volumes:                             │                  │
│  │    ./static_root → /var/www/react:ro  │                  │
│  │                                       │                  │
│  │  nginx.conf:                          │                  │
│  │    root /var/www/react;               │                  │
│  │    location /static/ { ... }          │                  │
│  │    location /api/ { proxy_pass }      │                  │
│  └───────────────────────────────────────┘                  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ↓
                   http://localhost:80
```

---

## 📁 Структура директорий

### До сборки:
```
d:\GusTest\
├── guscha_django_frontend\
│   ├── src\                    # React исходники
│   ├── package.json
│   └── (нет build\)
│
└── guscha_django\
    ├── static\                 # Пустая или старая
    ├── static_root\            # Пустая или старая
    ├── config\nginx.conf
    └── docker-compose.dev.yml
```

### После `build_frontend_improved.ps1`:
```
d:\GusTest\
├── guscha_django_frontend\
│   └── build\                  # ✅ Собранный React
│       ├── index.html
│       └── static\
│           ├── css\
│           └── js\
│
└── guscha_django\
    ├── static\                 # ✅ Копия для dev
    │   ├── index.html
    │   ├── css\, js\, media\
    │   └── favicon.ico
    │
    └── static_root\            # ✅ Копия для production
        ├── index.html
        ├── css\, js\, media\
        └── favicon.ico
```

### После `docker-compose up`:
```
d:\GusTest\guscha_django\
└── static_root\                # ✅ Обогащена Django статикой
    ├── index.html              # (React)
    ├── css\, js\, media\       # (React)
    ├── favicon.ico             # (React)
    │
    └── admin\                  # ⭐ Django админка (добавлена collectstatic)
    └── unfold\                 # ⭐ Django Unfold (добавлена collectstatic)
```

---

## 🔧 Два режима работы

### 1. Режим разработки (`-DevMode`)
```powershell
.\build_frontend_improved.ps1 -DevMode
```
- ✅ Собирает React (`npm run build`)
- ✅ Копирует в `static/` и `static_root/`
- ❌ НЕ трогает Docker
- 📝 Используется: `guscha_django/static/`

### 2. Режим продакшена (по умолчанию)
```powershell
.\build_frontend_improved.ps1
```
- ✅ Собирает React
- ✅ Копирует в обе директории
- ✅ Работает с Docker:
  - Выполняет `collectstatic` в контейнере
  - Перезапускает nginx
- 📝 Используется: `guscha_django/static_root/` (через volume)

---

## 🚀 Параметры скрипта сборки

| Параметр | Назначение |
|----------|------------|
| `-SkipBuild` | Пропустить `npm run build`, использовать существующую сборку |
| `-SkipDocker` | Не трогать Docker контейнеры |
| `-DevMode` | Режим разработки (без Docker) |
| `-ForceRefresh` | Полный перезапуск контейнеров (`down` + `up`) |
| `-RestartContainers` | Перезапуск контейнеров |
| `-Verbose` | Подробное логирование |

**Примеры:**
```powershell
# Стандартная сборка с обновлением Docker
.\build_frontend_improved.ps1

# Полная очистка и перезапуск
.\build_frontend_improved.ps1 -ForceRefresh

# Только локальная сборка для разработки
.\build_frontend_improved.ps1 -DevMode

# Использовать существующую сборку, только обновить Docker
.\build_frontend_improved.ps1 -SkipBuild
```

---

## 🔍 Ключевые моменты архитектуры

### 1. ДВЕ копии статики
- **`static/`** - для локальной разработки Django (не используется в production)
- **`static_root/`** - для production через Docker + nginx

### 2. Файл axiosConfig.js
- Особый файл конфигурации для Axios
- Сохраняется при очистке
- Внедряется в `index.html` через скрипт

### 3. collectstatic дважды
1. **Локально** (опционально): `python manage.py collectstatic`
2. **В Docker**: автоматически в `start.sh` при запуске контейнера

### 4. Синхронизация через volumes
```yaml
# Docker volume = двусторонняя синхронизация
django:
  volumes:
    - ./static_root:/app/static_root
```
- Изменения на хосте → видны в контейнере
- `collectstatic` в контейнере → видны на хосте
- nginx читает из того же volume

### 5. Nginx НЕ внутри контейнера Django
- Отдельный контейнер nginx
- Читает static_root через volume (read-only)
- Проксирует API к Django

---

## 🎯 Workflow обновления фронтенда

### Полное обновление (production):
```powershell
# 1. Сборка и обновление всего
.\build_frontend_improved.ps1

# Скрипт автоматически:
# - Собирает React (npm run build)
# - Копирует в static_root/
# - Выполняет collectstatic в Django контейнере
# - Перезапускает nginx
```

### Быстрое обновление (без сборки):
```powershell
# 1. Если React уже собран
.\build_frontend_improved.ps1 -SkipBuild

# Скрипт:
# - Использует существующий build/
# - Обновляет только Docker
```

### С полной очисткой кэша:
```powershell
# 1. Полный перезапуск всех контейнеров
.\build_frontend_improved.ps1 -ForceRefresh

# Скрипт:
# - Останавливает все контейнеры (down)
# - Запускает заново (up -d)
# - Очищает весь кэш nginx
```

---

## ⚠️ Важные замечания

### 1. Docker НЕ собирает React
- React собирается **локально** через `npm run build`
- Docker только **использует** уже собранные файлы
- Dockerfile копирует `static/` (не `build/`)

### 2. static_root - единственный источник истины в production
- nginx читает ТОЛЬКО из `/var/www/react` (= `static_root/`)
- `static/` НЕ используется в Docker

### 3. collectstatic объединяет файлы
```
/app/static_root/ = React статика + Django админка + другие Django static файлы
```

### 4. Volumes обеспечивают синхронизацию
- Без volumes пришлось бы пересобирать образы
- С volumes достаточно перезапустить nginx

---

## 🏗️ Что происходит при разных сценариях

### Сценарий 1: Изменили React код
```powershell
# 1. Пересобрать фронтенд
.\build_frontend_improved.ps1

# Что происходит:
# ✅ npm run build → новый build/
# ✅ build/ → static_root/
# ✅ collectstatic в Django контейнере
# ✅ nginx restart
# ✅ Новый фронтенд доступен на http://localhost
```

### Сценарий 2: Изменили Django статику (админка, CSS)
```powershell
# 1. В Django контейнере
docker-compose exec django python manage.py collectstatic --noinput

# 2. Перезапустить nginx
docker-compose restart nginx
```

### Сценарий 3: Проблемы с кэшем nginx
```powershell
# Полная очистка
.\build_frontend_improved.ps1 -ForceRefresh
```

---

## 📊 Сравнение с тем, что я предлагал (неправильно)

| Аспект | Моё предложение ❌ | Ваша архитектура ✅ |
|--------|-------------------|-------------------|
| Сборка React | В Dockerfile | Локально через PowerShell |
| Nginx для фронтенда | Отдельный контейнер | В основном nginx (с Django) |
| Dockerfile фронтенда | Multi-stage с nginx | НЕ НУЖЕН |
| Точка входа | Два nginx (80, 3000) | Один nginx (80) |
| static_root | Копируется из build | Наполняется collectstatic |
| Обновление | Пересборка образов | PowerShell скрипт |

---

## ✅ Выводы

Ваша архитектура **правильная и эффективная**:

1. **Разделение ответственности:**
   - PowerShell → сборка React
   - Docker → запуск и статика Django
   - nginx → раздача всего

2. **Быстрое обновление:**
   - Не нужно пересобирать Docker образы
   - Достаточно скрипта и restart nginx

3. **Единая точка входа:**
   - Весь трафик через один nginx:80
   - React + API + админка

4. **Гибкость:**
   - Можно работать без Docker (`-DevMode`)
   - Можно обновлять без сборки (`-SkipBuild`)
   - Можно полностью очистить кэш (`-ForceRefresh`)

---

**Дата анализа:** 30 октября 2024  
**Статус:** ✅ Архитектура полностью понята и задокументирована
