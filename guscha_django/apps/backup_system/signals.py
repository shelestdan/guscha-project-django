from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import BackupLog
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def log_backup_operation(operation_type, status='success', details='', user=None):
    """Утилита для логирования операций резервного копирования"""
    try:
        BackupLog.objects.create(
            operation_type=operation_type,
            status=status,
            details=details,
            user=user
        )
        logger.info(f"Logged backup operation: {operation_type} - {status}")
    except Exception as e:
        logger.error(f"Failed to log backup operation: {str(e)}")


# Пример использования:
# from apps.backup_system.signals import log_backup_operation
# 
# # После выполнения команды dbbackup
# log_backup_operation('backup_db', 'success', 'Database backup completed')
# 
# # После выполнения команды mediabackup  
# log_backup_operation('backup_media', 'success', 'Media backup completed')
# 
# # После выполнения команды dbrestore
# log_backup_operation('restore_db', 'success', 'Database restored from backup')
# 
# # При ошибке
# log_backup_operation('backup_db', 'error', 'Backup failed: disk full')