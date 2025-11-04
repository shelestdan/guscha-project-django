# 🚀 Полное руководство по развертыванию проекта Guscha

## 📋 Обзор
Этот проект готов к развертыванию на новом сервере с нуля одним скриптом.

---

## ⚡ Быстрый старт (One-click deployment)

### 1. Клонирование проекта
```bash
git clone https://github.com/shelestdan/guscha-project-django.git
cd guscha-project-django
```

### 2. Запуск установки
```bash
chmod +x FULL_SETUP.sh
./FULL_SETUP.sh
```

### 3. Настройка OAuth (опционально)
Следуйте инструкциям в файле `OAUTH_SETUP.md`

---

## 🔧 Что делает скрипт FULL_SETUP.sh

### ✅ Автоматически устанавливает:
- **Docker** и **Docker Compose**
- **PostgreSQL** базу данных
- **Redis** для кэширования
- **Nginx** веб-сервер
- **Django** бэкенд
- **React** фронтенд
- **Telegram Bot** для авторизации

### ✅ Автоматически настраивает:
- Все переменные окружения
- Сетевые соединения между сервисами
- Миграции базы данных
- Административного пользователя
- Статические файлы и медиа

### ✅ Проверяет работоспособность:
- Доступность сайта по http://localhost
- Работу API эндпоинтов
- Корректность настроек OAuth

---

## 📁 Структура после установки

```
guscha-project-django/
├── 📂 guscha_django/          # Django проект
│   ├── 📂 apps/               # Django приложения
│   ├── 📂 guscha_project/     # Настройки Django
│   ├── 📄 .env                # Переменные окружения
│   └── 📄 docker-compose.dev.yml
├── 📂 guscha_django_frontend/ # React проект
├── 📄 FULL_SETUP.sh           # Скрипт установки
├── 📄 OAUTH_SETUP.md          # Инструкция OAuth
└── 📄 DEPLOYMENT_GUIDE.md     # Это руководство
```

---

## 🎯 Результат установки

### 🔐 Доступные методы входа:
- **📧 Email/Password**: `admin@example.com` / `Admin123!@#`
- **🔵 Google OAuth**: После настройки в `OAUTH_SETUP.md`
- **📱 Telegram**: После настройки бота в `OAUTH_SETUP.md`

### 🌱 Доступные сервисы:
- **🌐 Сайт**: http://localhost
- **🔧 API**: http://localhost/api/
- **👤 Админка**: http://localhost/admin/
- **📊 Health**: http://localhost/health/

---

## 🔄 Управление проектом

### Основные команды:
```bash
# Статус всех сервисов
cd guscha_django && docker-compose -f docker-compose.dev.yml ps

# Просмотр логов
cd guscha_django && docker-compose -f docker-compose.dev.yml logs

# Перезапуск всех сервисов
cd guscha_django && docker-compose -f docker-compose.dev.yml restart

# Остановка всех сервисов
cd guscha_django && docker-compose -f docker-compose.dev.yml down

# Обновление проекта
git pull origin macOS
cd guscha_django && docker-compose -f docker-compose.dev.yml build
cd guscha_django && docker-compose -f docker-compose.dev.yml up -d
```

---

## 🛠️ Требования к серверу

### Минимальные:
- **ОС**: macOS или Linux (Ubuntu/CentOS)
- **RAM**: 4GB+
- **Disk**: 10GB+
- **Internet**: Для установки Docker и зависимостей

### Рекомендуемые:
- **CPU**: 2+ cores
- **RAM**: 8GB+
- **Disk**: 20GB+

---

## 🔒 Безопасность

### Продакшн настройка:
1. **Измените пароль администратора**:
   ```bash
   cd guscha_django
   docker-compose exec django python manage.py changepassword admin@example.com
   ```

2. **Настройте HTTPS** через Let's Encrypt
3. **Измените SECRET_KEY** в .env файле
4. **Ограничьте доступ** к админке по IP

### Переменные окружения:
- Все токены и ключи хранятся в `.env`
- Файл `.env` не должен попадать в Git
- Используйте сложные пароли

---

## 📊 Мониторинг

### Health checks:
```bash
# Проверка здоровья Django
curl http://localhost/health/

# Проверка здоровья Nginx
curl http://localhost/nginx-health

# Статус контейнеров
cd guscha_django && docker-compose -f docker-compose.dev.yml ps
```

### Логи:
```bash
# Все логи
cd guscha_django && docker-compose -f docker-compose.dev.yml logs

# Логи конкретного сервиса
cd guscha_django && docker-compose -f docker-compose.dev.yml logs django
cd guscha_django && docker-compose -f docker-compose.dev.yml logs nginx
cd guscha_django && docker-compose -f docker-compose.dev.yml logs telegram-bot
```

---

## 🆘 Частые проблемы

### Проблема: Сайт недоступен
```bash
# Перезапустите все сервисы
cd guscha_django && docker-compose -f docker-compose.dev.yml restart

# Проверьте порты
netstat -tulpn | grep :80
```

### Проблема: OAuth не работает
- Проверьте настройки в `OAUTH_SETUP.md`
- Убедитесь что redirect URIs правильные
- Проверьте логи: `docker-compose logs django`

### Проблема: Telegram бот не отвечает
- Проверьте токен в `.env`
- Проверьте логи: `docker-compose logs telegram-bot`
- Убедитесь что бот запущен: `docker-compose ps`

---

## 📈 Масштабирование

### Для продакшн используйте:
- **HTTPS** через Let's Encrypt
- **Балансировщик нагрузки** (если нужно)
- **Отдельный сервер базы данных**
- **Redis кластер** для кэширования
- **Мониторинг** через Prometheus/Grafana

---

## 🎉 Готово!

После выполнения `FULL_SETUP.sh` у вас будет полностью рабочий проект с:
- ✅ Django бэкендом
- ✅ React фронтендом
- ✅ PostgreSQL базой данных
- ✅ Redis кэшем
- ✅ Nginx веб-сервером
- ✅ Telegram ботом
- ✅ OAuth авторизацией
- ✅ Административной панелью

**Проект готов к разработке и продакшн использованию!** 🚀
