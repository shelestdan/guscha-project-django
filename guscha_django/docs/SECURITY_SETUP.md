# 🔒 Готовое решение безопасности для Django Unfold админки

## ✅ Что уже настроено

В проект интегрировано готовое решение безопасности, включающее:

### 1. Защита от brute-force атак (django-axes)
- Блокировка после 5 неудачных попыток входа
- Блокировка на 1 час
- Логирование всех попыток
- Защита по комбинации IP + пользователь

### 2. Honeypot (ложная админка)
- Стандартный URL `/admin/` теперь ведет на ложную админку
- Все попытки входа логируются и отправляются уведомления
- Настоящая админка перенесена на секретный URL

### 3. Кастомный URL админки
- Настоящая админка доступна по секретному URL
- URL настраивается через переменную окружения `ADMIN_URL`
- По умолчанию: `secure-admin-panel/`

### 4. Система логирования
- Все события безопасности записываются в `logs/security.log`
- Отдельные логи для axes и honeypot
- Консольный вывод для разработки

## 🚀 Быстрый запуск

### Шаг 1: Скопируйте переменные окружения

Скопируйте содержимое файла `.env.security` в ваш основной `.env` файл:

```bash
# Добавьте эти строки в ваш .env файл
ADMIN_URL=secure-admin-panel/
ADMIN_IP_WHITELIST=
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
ADMINS=Admin <admin@yourdomain.com>
```

### Шаг 2: Установите зависимости

```powershell
# В контейнере или локально
docker-compose exec django pip install -r requirements.txt
```

### Шаг 3: Примените миграции

```powershell
# Создайте и примените миграции для axes
docker-compose exec django python manage.py makemigrations
docker-compose exec django python manage.py migrate
```

### Шаг 4: Перезапустите контейнеры

```powershell
docker-compose down
docker-compose up -d
```

## 🔑 Доступ к админке

### Ложная админка (Honeypot)
- **URL**: `http://localhost:8000/admin/`
- **Назначение**: Ловушка для злоумышленников
- **Действие**: Логирует попытки входа, отправляет уведомления

### Настоящая админка
- **URL**: `http://localhost:8000/secure-admin-panel/` (или ваш кастомный URL)
- **Назначение**: Реальная админка Django Unfold
- **Защита**: Axes + опциональный IP whitelist

## ⚙️ Настройка

### Изменение URL админки

```bash
# В .env файле
ADMIN_URL=my-secret-admin-123/
```

**⚠️ КРИТИЧЕСКИЕ ТРЕБОВАНИЯ БЕЗОПАСНОСТИ ДЛЯ ADMIN_URL**:

1. **НЕ ХРАНИТЕ ADMIN_URL В КОДЕ** - только в переменных окружения
2. **НЕ КОММИТЬТЕ .env ФАЙЛЫ** - добавьте их в .gitignore
3. **ИСПОЛЬЗУЙТЕ СЛУЧАЙНЫЕ ЗНАЧЕНИЯ** - например: `secret-panel-a1b2c3d4e5f6/`
4. **ИЗБЕГАЙТЕ ОЧЕВИДНЫХ ПУТЕЙ** - не используйте 'admin', 'panel', 'control'
5. **РЕГУЛЯРНО МЕНЯЙТЕ ПУТЬ** - особенно после компрометации
6. **URL должен заканчиваться слешем** `/`

### Генерация безопасного ADMIN_URL

```bash
# Linux/Mac
echo "ADMIN_URL=admin-$(openssl rand -hex 12)/" >> .env

# Windows PowerShell
$randomPath = -join ((1..24) | ForEach {'{0:X}' -f (Get-Random -Max 16)})
Add-Content .env "ADMIN_URL=admin-$randomPath/"
```

### Ограничение доступа по IP

```bash
# Разрешить доступ только с определенных IP
ADMIN_IP_WHITELIST=127.0.0.1,192.168.1.100,10.0.0.5

# Разрешить доступ со всех IP (по умолчанию)
ADMIN_IP_WHITELIST=
```

### Настройка email уведомлений

```bash
# Gmail (рекомендуется использовать App Password)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
ADMINS=Admin <admin@yourdomain.com>
```

## 📊 Мониторинг

### Просмотр логов безопасности

```powershell
# Логи в реальном времени
docker-compose exec django tail -f logs/security.log

# Последние 50 записей
docker-compose exec django tail -n 50 logs/security.log
```

### Проверка заблокированных IP

```powershell
# Войдите в Django shell
docker-compose exec django python manage.py shell

# Выполните в shell:
from axes.models import AccessAttempt
AccessAttempt.objects.all()
```

### Разблокировка IP

```powershell
# Разблокировать конкретный IP
docker-compose exec django python manage.py axes_reset_ip 192.168.1.100

# Разблокировать все IP
docker-compose exec django python manage.py axes_reset
```

## 🛡️ Уровни защиты

1. **Honeypot** - Ловушка на `/admin/`
2. **Axes** - Защита от brute-force
3. **IP Whitelist** - Ограничение по IP (опционально)
4. **Кастомный URL** - Скрытие реальной админки
5. **Логирование** - Полная история событий
6. **Email уведомления** - Мгновенные алерты

## 🔧 Устранение неполадок

### Не могу войти в админку

1. Проверьте правильность URL (должен заканчиваться `/`)
2. Убедитесь, что ваш IP не заблокирован
3. Проверьте логи: `docker-compose logs django`

### Не приходят email уведомления

1. Проверьте настройки EMAIL в `.env`
2. Для Gmail используйте App Password
3. Проверьте логи: `docker-compose exec django tail -f logs/security.log`

### Заблокировали себя

```powershell
# Разблокируйте свой IP
docker-compose exec django python manage.py axes_reset_ip YOUR_IP

# Или сбросьте все блокировки
docker-compose exec django python manage.py axes_reset
```

## 📈 Дополнительные возможности

### Настройка времени блокировки

В `settings.py` измените:

```python
AXES_COOLOFF_TIME = 2  # Блокировка на 2 часа
AXES_FAILURE_LIMIT = 3  # Блокировка после 3 попыток
```

### Добавление Telegram уведомлений

Можно интегрировать с существующим Telegram ботом для получения уведомлений.

---

## ✅ Готово!

Ваша Django Unfold админка теперь защищена многоуровневой системой безопасности. Все настройки применяются автоматически после перезапуска контейнеров.

**Рекомендации**:
- Регулярно проверяйте логи безопасности
- Используйте сложные пароли
- Настройте email уведомления
- Периодически меняйте URL админки
- Ведите whitelist разрешенных IP адресов