from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import BackupLog
from .signals import log_backup_operation

User = get_user_model()


class BackupLogModelTest(TestCase):
    """Тесты для модели BackupLog"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_backup_log(self):
        """Тест создания лога резервного копирования"""
        log = BackupLog.objects.create(
            operation_type='backup_db',
            status='success',
            details='Test backup completed',
            user=self.user
        )
        
        self.assertEqual(log.operation_type, 'backup_db')
        self.assertEqual(log.status, 'success')
        self.assertEqual(log.details, 'Test backup completed')
        self.assertEqual(log.user, self.user)
        self.assertIsNotNone(log.timestamp)
    
    def test_backup_log_str_method(self):
        """Тест строкового представления BackupLog"""
        log = BackupLog.objects.create(
            operation_type='backup_media',
            status='error'
        )
        
        expected_str = f"backup_media - error ({log.timestamp.strftime('%Y-%m-%d %H:%M')})"
        self.assertEqual(str(log), expected_str)
    
    def test_backup_log_ordering(self):
        """Тест сортировки логов по времени"""
        log1 = BackupLog.objects.create(
            operation_type='backup_db',
            status='success'
        )
        log2 = BackupLog.objects.create(
            operation_type='restore_db',
            status='success'
        )
        
        logs = BackupLog.objects.all()
        # Должны быть отсортированы по убыванию времени (новые первыми)
        self.assertEqual(logs[0], log2)
        self.assertEqual(logs[1], log1)


class BackupSignalsTest(TestCase):
    """Тесты для утилит логирования"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_log_backup_operation_success(self):
        """Тест успешного логирования операции"""
        log_backup_operation(
            operation_type='backup_db',
            status='success',
            details='Database backup completed successfully',
            user=self.user
        )
        
        log = BackupLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.operation_type, 'backup_db')
        self.assertEqual(log.status, 'success')
        self.assertEqual(log.details, 'Database backup completed successfully')
        self.assertEqual(log.user, self.user)
    
    def test_log_backup_operation_without_user(self):
        """Тест логирования операции без пользователя"""
        log_backup_operation(
            operation_type='restore_media',
            status='error',
            details='Restore failed: file not found'
        )
        
        log = BackupLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.operation_type, 'restore_media')
        self.assertEqual(log.status, 'error')
        self.assertEqual(log.details, 'Restore failed: file not found')
        self.assertIsNone(log.user)
    
    def test_log_backup_operation_choices(self):
        """Тест различных типов операций и статусов"""
        operations = [
            ('backup_db', 'success'),
            ('backup_media', 'error'),
            ('restore_db', 'in_progress'),
            ('restore_media', 'success')
        ]
        
        for op_type, status in operations:
            log_backup_operation(
                operation_type=op_type,
                status=status,
                details=f'Test {op_type} with {status}'
            )
        
        logs = BackupLog.objects.all()
        self.assertEqual(logs.count(), 4)
        
        for i, (op_type, status) in enumerate(reversed(operations)):
            self.assertEqual(logs[i].operation_type, op_type)
            self.assertEqual(logs[i].status, status)
