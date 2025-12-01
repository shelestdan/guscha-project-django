# 🔍 Полный анализ проекта Guscha

**Дата анализа:** 1 декабря 2025  
**Версия:** 1.0

---

## 📋 Общая информация

| Параметр | Значение |
|----------|----------|
| **Backend** | Django 5.2 + Django REST Framework |
| **Frontend** | React 19 + Zustand + TailwindCSS |
| **База данных** | PostgreSQL |
| **Кэширование** | Redis |
| **Аутентификация** | JWT + Django Allauth + Telegram |
| **Деплой** | Docker + Nginx |

---

## 🏗️ Архитектура проекта

```
guscha_project/
├── guscha_django/           # Backend (Django)
│   ├── apps/                # Django приложения
│   │   ├── accounts/        # Пользователи, аутентификация
│   │   ├── products/        # Товары, категории
│   │   ├── orders/          # Заказы
│   │   ├── cart/            # Корзина
│   │   ├── addresses/       # Адреса доставки
│   │   ├── collections/     # Коллекции товаров
│   │   ├── background_content/ # Фоновый контент
│   │   ├── backup_system/   # Резервное копирование
│   │   └── core/            # Общие утилиты, middleware
│   ├── telegram_bot/        # Telegram бот
│   └── guscha_project/      # Настройки Django
│
└── guscha_django_frontend/  # Frontend (React)
    └── src/
        ├── api/             # API слой
        ├── components/      # React компоненты
        ├── pages/           # Страницы
        ├── store/           # Zustand stores
        ├── hooks/           # Custom hooks
        └── utils/           # Утилиты
```

---

## 🔗 Связи между компонентами

### Backend → Frontend API связи

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
├─────────────────────────────────────────────────────────────────┤
│  Store Layer (Zustand)                                          │
│  ├── userStore.js      ←→ authApi.js                           │
│  ├── cartStore.js      ←→ cartApi.js                           │
│  └── productsStore.js  ←→ productsApi.js                       │
├─────────────────────────────────────────────────────────────────┤
│  API Layer (axios)                                              │
│  └── axiosInstance.js  → baseURL: window.location.origin       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (Django)                         │
├─────────────────────────────────────────────────────────────────┤
│  URL Router (guscha_project/urls.py)                           │
│  ├── /api/accounts/    → apps.accounts.urls                    │
│  ├── /api/products/    → apps.products.urls                    │
│  ├── /api/orders/      → apps.orders.urls                      │
│  ├── /api/cart/        → apps.cart.urls                        │
│  ├── /api/addresses/   → apps.addresses.urls                   │
│  ├── /api/collections/ → apps.collections.urls                 │
│  ├── /api/background/  → apps.background_content.urls          │
│  ├── /api/admin/       → apps.core.urls                        │
│  ├── /api/backup/      → apps.backup_system.urls               │
│  └── /api/auth/        → dj_rest_auth.urls                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛣️ API Маршруты (Routes)

### 1. Accounts API (`/api/accounts/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/users/` | Регистрация пользователя |
| POST | `/users/login/` | Вход в систему |
| POST | `/users/logout/` | Выход из системы |
| GET/PUT | `/users/me/` | Профиль текущего пользователя |
| PUT | `/users/change_password/` | Смена пароля |
| POST | `/auth/token/` | Получение JWT токена |
| POST | `/auth/token/refresh/` | Обновление JWT токена |
| POST | `/password-reset/` | Запрос сброса пароля |
| POST | `/telegram/login/initiate/` | Вход через Telegram |
| POST | `/telegram/verify/` | Верификация Telegram кода |
| POST | `/qr/create/` | Создание QR кода |
| GET | `/qr/status/<id>/` | Статус QR кода |

### 2. Products API (`/api/products/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/categories/` | Список категорий |
| GET | `/products/` | Список товаров |
| GET | `/products/<slug>/` | Детали товара |
| GET | `/preorders/` | Список предзаказов |
| GET/POST | `/wishlist/` | Избранное |

### 3. Cart API (`/api/cart/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/items/` | Содержимое корзины |
| POST | `/add/` | Добавить товар |
| POST | `/add_preorder/` | Добавить предзаказ |
| PUT | `/update/<id>/` | Обновить количество |
| DELETE | `/remove/<id>/` | Удалить товар |
| POST | `/clear/` | Очистить корзину |

### 4. Orders API (`/api/orders/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/orders/` | Список заказов |
| POST | `/orders/` | Создать заказ |
| GET | `/orders/<id>/` | Детали заказа |

### 5. Addresses API (`/api/addresses/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Список адресов |
| POST | `/` | Добавить адрес |
| PUT | `/<id>/` | Обновить адрес |
| DELETE | `/<id>/` | Удалить адрес |

### 6. Collections API (`/api/collections/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Список коллекций |
| GET | `/<slug>/images/` | Изображения коллекции |

### 7. Background Content API (`/api/background/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/active/` | Активный фон |
| GET | `/images/` | Фоновые изображения |
| GET | `/videos/` | Фоновые видео |
| GET | `/slideshows/` | Слайдшоу |

---

## 🔐 Безопасность

### ✅ Реализованные меры безопасности

| Мера | Статус | Описание |
|------|--------|----------|
| JWT аутентификация | ✅ | Access token 15 мин, Refresh 7 дней |
| CSRF защита | ✅ | Токен в cookie + заголовок |
| CORS настройки | ✅ | Whitelist доменов |
| Rate Limiting | ⚠️ | Временно отключен для тестирования |
| Brute Force защита | ✅ | django-defender |
| Password Validators | ✅ | 4 валидатора Django |
| Security Headers | ✅ | X-Frame-Options, XSS, etc. |
| HTTPS в продакшене | ✅ | HSTS, SSL Redirect |
| Логирование безопасности | ✅ | Отдельные файлы логов |
| 2FA через Telegram | ✅ | Верификация по коду |
| Google OAuth | ✅ | Социальная аутентификация |

### ⚠️ Рекомендации по безопасности

1. **Rate Limiting отключен** — включить `RATE_LIMITING_ENABLED = True` в продакшене
2. **DEBUG режим** — убедиться что `DEBUG=False` в продакшене
3. **SECRET_KEY** — использовать уникальный ключ в продакшене
4. **ADMIN_URL** — изменить на случайный путь (уже реализовано)

---

## 📦 Анализ зависимостей

### Backend (requirements.txt)

| Категория | Пакеты | Статус |
|-----------|--------|--------|
| **Core** | Django 5.2, DRF, psycopg2 | ✅ Актуальные |
| **Auth** | allauth, dj-rest-auth, simplejwt | ✅ Актуальные |
| **Security** | django-defender, django-ratelimit, django-otp | ✅ Актуальные |
| **Cache** | django-redis, django-cachalot | ✅ Актуальные |
| **Admin** | django-unfold, django-import-export | ✅ Актуальные |
| **Monitoring** | django-silk | ✅ Актуальный |

### Frontend (package.json)

| Категория | Пакеты | Статус |
|-----------|--------|--------|
| **Core** | React 19, react-router-dom 7 | ✅ Актуальные |
| **State** | Zustand 5 | ✅ Актуальный |
| **UI** | MUI 7, TailwindCSS 3, Framer Motion | ✅ Актуальные |
| **HTTP** | Axios | ✅ Актуальный |
| **Forms** | react-phone-number-input | ✅ Актуальный |

### ⚠️ Потенциально лишние зависимости

**Frontend:**
- `bcryptjs` — хеширование должно быть на backend
- `lighthouse` — dev dependency, не нужен в production
- `@prisma/client` — не используется (проект на Django)

**Backend:**
- `celery` — установлен, но не настроен (нет celery.py)
- `boto3` — установлен для S3, но не настроен

---

## 🍝 Анализ "спагетти-кода"

### ✅ Хорошие практики

1. **Разделение на приложения** — каждая функциональность в отдельном Django app
2. **Service Layer** — accounts использует сервисы (UserService, AuthService)
3. **Repository Pattern** — accounts имеет repositories/
4. **Централизованный API** — все API в одном месте (frontend/src/api/)
5. **State Management** — Zustand stores для глобального состояния
6. **Lazy Loading** — страницы загружаются лениво

### ⚠️ Проблемные места

1. **Дублирование API файлов:**
   - `orderApi.js` и `ordersApi.js` — дублирование
   - `addressApi.js` и `addresses.js` — дублирование

2. **Смешанная структура компонентов:**
   - Часть компонентов в корне `/components/`
   - Часть в `/components/features/`
   - Нет единого стандарта

3. **Большие файлы views:**
   - `accounts/views.py` — 1737 строк (рекомендуется разбить)

4. **Закомментированный код:**
   - В `urls.py` много закомментированных маршрутов
   - В `settings.py` закомментированные middleware

---

## 📊 Frontend страницы и компоненты

### Страницы (Pages)

| Страница | Файл | Описание |
|----------|------|----------|
| Главная | `HomePage.jsx` | Лендинг с фоном |
| Товар | `ProductDetailPage.jsx` | Детали товара |
| Предзаказ | `PreorderDetailPage.jsx` | Детали предзаказа |
| Коллекции | `CollectionsPage.jsx` | Список коллекций |
| Коллекция | `CollectionDetailPage.jsx` | Детали коллекции |
| Аккаунт | `Account.jsx` | Личный кабинет |
| Адреса | `AddressesPage.jsx` | Управление адресами |
| Оформление | `CheckoutPage.jsx` | Оформление заказа |
| Подтверждение | `OrderConfirmationPage.jsx` | Подтверждение заказа |

### Ключевые компоненты

| Компонент | Путь | Описание |
|-----------|------|----------|
| Header | `layout/Header/` | Шапка сайта |
| Footer | `layout/Footer.jsx` | Подвал |
| CartSidebar | `features/cart/` | Боковая корзина |
| BackgroundContent | `BackgroundContent/` | Фоновый контент |
| FlowingMenu | `FlowingMenu/` | Анимированное меню |
| VideoPlayer | `VideoPlayer/` | Видеоплеер |

---

## 🔄 Поток данных

```
┌──────────────────────────────────────────────────────────────┐
│                      USER ACTION                              │
│                    (click, submit, etc.)                      │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    REACT COMPONENT                            │
│              (calls store action or API)                      │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    ZUSTAND STORE                              │
│         (userStore, cartStore, productsStore)                 │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      API LAYER                                │
│              (authApi, cartApi, etc.)                         │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                   AXIOS INSTANCE                              │
│        (adds JWT, CSRF, handles errors)                       │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    DJANGO REST API                            │
│              (ViewSets, APIViews)                             │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER                               │
│        (UserService, AuthService, etc.)                       │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    DJANGO ORM                                 │
│              (Models, QuerySets)                              │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    POSTGRESQL                                 │
│                   (Database)                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 📝 Рекомендации по улучшению

### Высокий приоритет

1. **Включить Rate Limiting в продакшене**
2. **Разбить `accounts/views.py`** на отдельные файлы по функциональности
3. **Удалить дублирующиеся API файлы** (orderApi/ordersApi, addressApi/addresses)
4. **Настроить Celery** для фоновых задач или удалить зависимость

### Средний приоритет

5. **Стандартизировать структуру компонентов** — все feature-компоненты в `/features/`
6. **Удалить закомментированный код** из urls.py и settings.py
7. **Добавить TypeScript** — уже есть tsconfig.json, но файлы .jsx
8. **Настроить S3 для медиа** или удалить boto3

### Низкий приоритет

9. **Удалить bcryptjs** из frontend — хеширование на backend
10. **Добавить E2E тесты** — Playwright или Cypress
11. **Настроить CI/CD** — GitHub Actions

---

## ✅ Заключение

Проект имеет **хорошую архитектуру** с разделением на слои и модули. Основные проблемы:
- Некоторое дублирование кода
- Большие файлы, требующие рефакторинга
- Неиспользуемые зависимости

**Общая оценка: 7.5/10** — проект готов к продакшену после устранения указанных замечаний.
