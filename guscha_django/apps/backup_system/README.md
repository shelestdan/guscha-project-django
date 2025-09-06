# Система резервного копирования

Минималистичная система резервного копирования на основе django-dbbackup.

## Возможности

- Логирование операций резервного копирования для аудита
- Простая админка для просмотра истории операций
- Интеграция с django-dbbackup

## Использование

### Основные команды django-dbbackup

```bash
# Создание резервной копии базы данных
python manage.py dbbackup

# Создание резервной копии медиа-файлов
python manage.py mediabackup

# Восстановление базы данных
python manage.py dbrestore

# Восстановление медиа-файлов
python manage.py mediarestore

# Список доступных резервных копий
python manage.py listbackups
```

### Логирование операций

Для ручного логирования операций используйте утилиту из signals.py:

```python
from apps.backup_system.signals import log_backup_operation

# Логирование успешной операции
log_backup_operation('backup_db', 'success', 'Database backup completed')

# Логирование ошибки
log_backup_operation('backup_db', 'error', 'Backup failed: disk full')
```

### Просмотр логов

1. Перейдите в админку Django: `/admin/`
2. Откройте раздел "Система резервного копирования"
3. Выберите "Логи операций резервного копирования"

## Настройка

Убедитесь, что в settings.py настроен django-dbbackup:

```python
INSTALLED_APPS = [
    # ...
    'dbbackup',
    'apps.backup_system',
    # ...
]

# Настройки django-dbbackup
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': '/path/to/backups/'}
```

## Модели

### BackupLog

Модель для хранения логов операций резервного копирования:

- `timestamp` - время операции
- `operation_type` - тип операции (backup_db, backup_media, restore_db, restore_media)
- `status` - статус (success, error, in_progress)
- `user` - пользователь, выполнивший операцию (опционально)
- `details` - дополнительные детали операции