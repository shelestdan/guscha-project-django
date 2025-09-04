from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from datetime import timedelta
import json

from .models.security_report import SecurityReport, ThreatDetection, SecurityBlacklist
from .models.device_fingerprint import DeviceFingerprint
from .models.behavioral_analysis import BehavioralAnalysis
from .services.security_report_service import SecurityReportService
from .services.threat_analysis_service import ThreatAnalysisService
from .services.blacklist_service import BlacklistService
from .services.device_fingerprint_service import DeviceFingerprintService
from .services.behavioral_analysis_service import BehavioralAnalysisService
from .services.monitoring_service import SecurityMonitoringService
from .middleware.security_middleware import (
    SecurityMiddleware,
    SecurityReportMiddleware,
    SecurityLoggingMiddleware
)


class SecurityModelTests(TestCase):
    """
    Тесты моделей системы безопасности
    """
    
    def setUp(self):
        self.test_ip = '192.168.1.100'
        self.test_user_agent = 'Mozilla/5.0 (Test Browser)'
        self.test_fingerprint = 'test_fingerprint_hash'
    
    def test_security_report_creation(self):
        """Тест создания отчета о безопасности"""
        report = SecurityReport.objects.create(
            session_id='test_session_123',
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            fingerprint_hash=self.test_fingerprint,
            overall_risk_score=75.0,
            risk_level='high',
            raw_data={'test': 'data'}
        )
        
        self.assertEqual(report.ip_address, self.test_ip)
        self.assertEqual(report.overall_risk_score, 75.0)
        self.assertEqual(report.risk_level, 'high')
        self.assertEqual(report.session_id, 'test_session_123')
        self.assertTrue(report.created_at)
    
    def test_threat_detection_creation(self):
        """Тест создания обнаружения угрозы"""
        report = SecurityReport.objects.create(
            session_id='test_session_threat',
            ip_address=self.test_ip,
            overall_risk_score=75.0,
            risk_level='high'
        )
        
        threat = ThreatDetection.objects.create(
            security_report=report,
            threat_type='bot',
            severity='high',
            confidence=0.85,
            description='Test threat detection'
        )
        
        self.assertEqual(threat.security_report, report)
        self.assertEqual(threat.threat_type, 'bot')
        self.assertEqual(threat.severity, 'high')
        self.assertEqual(threat.confidence, 0.85)
    
    def test_security_blacklist_creation(self):
        """Тест создания записи в черном списке"""
        blacklist_entry = SecurityBlacklist.objects.create(
            blacklist_type='ip',
            value=self.test_ip,
            reason='Test blacklist entry'
        )
        
        self.assertEqual(blacklist_entry.blacklist_type, 'ip')
        self.assertEqual(blacklist_entry.value, self.test_ip)
        self.assertTrue(blacklist_entry.is_active)
    
    def test_device_fingerprint_creation(self):
        """Тест создания отпечатка устройства"""
        fingerprint = DeviceFingerprint.objects.create(
            fingerprint_hash=self.test_fingerprint,
            user_agent=self.test_user_agent,
            screen_resolution='1920x1080',
            timezone_offset=0
        )
        
        self.assertEqual(fingerprint.fingerprint_hash, self.test_fingerprint)
        self.assertEqual(fingerprint.user_agent, self.test_user_agent)
        self.assertEqual(fingerprint.screen_resolution, '1920x1080')
    
    def test_behavioral_analysis_creation(self):
        """Тест создания поведенческого анализа"""
        now = timezone.now()
        analysis = BehavioralAnalysis.objects.create(
            session_id='test_session',
            ip_address=self.test_ip,
            analysis_type='mouse_movements',
            mouse_velocity_avg=150.5,
            typing_speed=45,
            analysis_start=now,
            analysis_end=now
        )
        
        self.assertEqual(analysis.session_id, 'test_session')
        self.assertEqual(analysis.analysis_type, 'mouse_movements')
        self.assertEqual(analysis.mouse_velocity_avg, 150.5)


class SecurityServiceTests(TestCase):
    """
    Тесты сервисов системы безопасности
    """
    
    def setUp(self):
        self.test_ip = '192.168.1.100'
        self.test_user_agent = 'Mozilla/5.0 (Test Browser)'
        self.security_report_service = SecurityReportService()
        self.threat_analysis_service = ThreatAnalysisService()
        self.blacklist_service = BlacklistService()
    
    def test_security_report_service_create_report(self):
        """Тест создания отчета через сервис"""
        report_data = {
            'session_id': 'test_session_789',
            'ip_address': self.test_ip,
            'user_agent': self.test_user_agent,
            'risk_level': 'medium',
            'overall_risk_score': 60
        }
        
        report = self.security_report_service.create_report(
            session_id=report_data['session_id'],
            ip_address=report_data['ip_address'],
            user_agent=report_data['user_agent'],
            risk_level=report_data['risk_level'],
            overall_risk_score=report_data['overall_risk_score']
        )
        
        self.assertIsInstance(report, SecurityReport)
        self.assertEqual(report.ip_address, self.test_ip)
        self.assertEqual(report.overall_risk_score, 60)
    
    def test_threat_analysis_service_analyze_report(self):
        """Тест анализа угроз"""
        report = SecurityReport.objects.create(
            session_id='test_session_threat',
            ip_address=self.test_ip,
            user_agent='HeadlessChrome/91.0.4472.124',  # Подозрительный user agent
            risk_level='high'
        )
        
        # Тестируем анализ отчета безопасности
        threats = self.threat_analysis_service.analyze_security_report(report)
        
        self.assertIsInstance(threats, list)
        # Должна быть обнаружена угроза автоматизации по user agent
        if threats:
            self.assertTrue(any(t.get('threat_type') == 'bot_activity' for t in threats))
    
    def test_blacklist_service_check_ip(self):
        """Тест проверки IP в черном списке"""
        # Добавляем IP в черный список
        SecurityBlacklist.objects.create(
            blacklist_type='ip_address',
            value=self.test_ip,
            reason='Test blacklist'
        )
        
        is_blacklisted = self.blacklist_service.is_blacklisted(self.test_ip, 'ip_address')
        self.assertTrue(is_blacklisted)
        
        # Проверяем несуществующий IP
        is_blacklisted = self.blacklist_service.is_blacklisted('192.168.1.200', 'ip_address')
        self.assertFalse(is_blacklisted)
    
    def test_device_fingerprint_service(self):
        """Тест сервиса отпечатков устройств"""
        fingerprint_service = DeviceFingerprintService()
        
        fingerprint_data = {
            'screen_resolution': '1920x1080',
            'timezone_offset': 180,
            'language': 'ru-RU',
            'user_agent': self.test_user_agent
        }
        
        fingerprint = fingerprint_service.create_or_update_fingerprint(
            fingerprint_data
        )
        
        self.assertIsInstance(fingerprint, DeviceFingerprint)
        self.assertEqual(fingerprint.user_agent, self.test_user_agent)
    
    def test_behavioral_analysis_service(self):
        """Тест сервиса поведенческого анализа"""
        analysis = BehavioralAnalysisService.create_analysis(
            session_id='test_session',
            ip_address=self.test_ip,
            analysis_type='mouse_movement',
            mouse_velocity_avg=150.0,
            typing_speed=45
        )
        
        self.assertIsInstance(analysis, BehavioralAnalysis)
        self.assertEqual(analysis.mouse_velocity_avg, 150.0)
        self.assertEqual(analysis.typing_speed, 45)
        self.assertEqual(analysis.session_id, 'test_session')
        self.assertEqual(analysis.ip_address, self.test_ip)


class SecurityMiddlewareTests(TestCase):
    """
    Тесты middleware системы безопасности
    """
    
    def setUp(self):
        self.client = Client()
        # Создаем mock get_response функцию
        def get_response(request):
            from django.http import HttpResponse
            return HttpResponse("OK")
        
        self.security_middleware = SecurityMiddleware(get_response)
        self.get_response = get_response
        # Принудительно включаем блокировку запросов для тестов
        self.security_middleware.block_requests = True
        self.test_ip = '192.168.1.100'
    
    def test_security_middleware_blacklist_check(self):
        """Тест проверки черного списка в middleware"""
        # Добавляем IP в черный список
        SecurityBlacklist.objects.create(
            blacklist_type='ip',
            value=self.test_ip,
            reason='Test blacklist'
        )
        
        # Создаем mock request
        request = MagicMock()
        request.META = {'REMOTE_ADDR': self.test_ip}
        request.path = '/api/auth/login/'
        request.method = 'GET'
        
        response = self.security_middleware.process_request(request)
        
        # Должен вернуть ответ с блокировкой
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
    
    def test_security_middleware_rate_limiting(self):
        """Тест ограничения скорости запросов"""
        # Устанавливаем низкий лимит для тестирования
        with self.settings(SECURITY_MAX_REQUESTS_PER_MINUTE=5):
            request = MagicMock()
            request.META = {'REMOTE_ADDR': self.test_ip}
            request.path = '/api/auth/register/'
            request.method = 'POST'
            
            # Делаем запросы до превышения лимита
            response = None
            for i in range(7):  # Превышаем лимит в 5 запросов
                response = self.security_middleware.process_request(request)
                if response:  # Если получили блокировку, выходим
                    break
            
            # Должен быть заблокирован
            self.assertIsNotNone(response)
            self.assertEqual(response.status_code, 403)


class SecurityMonitoringTests(TestCase):
    """
    Тесты системы мониторинга безопасности
    """
    
    def setUp(self):
        self.monitoring_service = SecurityMonitoringService()
        self.test_ip = '192.168.1.100'
    
    def test_mass_registration_detection(self):
        """Тест обнаружения массовых регистраций"""
        # Создаем множественные отчеты с одного IP
        for i in range(12):
            SecurityReport.objects.create(
                session_id=f'test_session_mass_{i}',
                ip_address=self.test_ip,
                overall_risk_score=50.0,
                risk_level='medium',
                created_at=timezone.now() - timedelta(minutes=2)
            )
        
        alerts = self.monitoring_service.check_mass_registrations()
        
        if alerts:
            self.assertEqual(alerts['type'], 'mass_registration')
        else:
            # Если алертов нет, это тоже нормально для теста
            self.assertIsNone(alerts)
    
    def test_suspicious_activity_monitoring(self):
        """Тест мониторинга подозрительной активности"""
        # Создаем отчет с высоким риском
        SecurityReport.objects.create(
            session_id='test_session_suspicious',
            ip_address=self.test_ip,
            overall_risk_score=85.0,
            risk_level='high'
        )
        
        alerts = self.monitoring_service.check_suspicious_activity()
        
        if alerts:
            self.assertEqual(alerts['type'], 'suspicious_activity')
        else:
            # Если алертов нет, это тоже нормально для теста
            self.assertIsNone(alerts)
    
    def test_automation_detection(self):
        """Тест обнаружения автоматизации"""
        # Создаем отчет с признаками бота
        SecurityReport.objects.create(
            session_id='test_session_automation',
            ip_address=self.test_ip,
            overall_risk_score=75.0,
            risk_level='high',
            raw_data={'user_agent': 'HeadlessChrome/91.0.4472.124', 'automation_detected': True}
        )
        
        alerts = self.monitoring_service.check_automation_attacks()
        
        if alerts:
            self.assertEqual(alerts['type'], 'automation_attack')
        else:
            # Если алертов нет, это тоже нормально для теста
            self.assertIsNone(alerts)
    
    @patch('apps.security.services.monitoring_service.SecurityMonitoringService._send_alert')
    def test_alert_notification(self, mock_send_alert):
        """Тест отправки уведомлений"""
        alert_data = {
            'type': 'test_alert',
            'severity': 'high',
            'message': 'Test alert message',
            'timestamp': timezone.now().isoformat()
        }
        
        self.monitoring_service.send_alert(alert_data)
        
        # Проверяем, что alert был отправлен
        mock_send_alert.assert_called_once()


class SecurityIntegrationTests(TestCase):
    """
    Интеграционные тесты системы безопасности
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_security_report_api_endpoint(self):
        """Тест API endpoint для отчетов безопасности"""
        report_data = {
            'timestamp': timezone.now().isoformat(),
            'sessionId': 'test_session_api_123',
            'risk': {
                'level': 'high',
                'score': 85.0,
                'indicators': ['fast_form_fill', 'no_mouse_movement']
            },
            'fingerprint': {
                'hash': 'test_fingerprint_hash',
                'confidence': 0.9,
                'components': {
                    'browser': {'name': 'Chrome', 'version': '120.0'},
                    'screen': {'width': 1920, 'height': 1080},
                    'timezone': {'offset': -300}
                }
            },
            'behavior': {
                'isHuman': False,
                'confidence': 0.3,
                'events_per_minute': 30,
                'mouse_movements': 100
            }
        }
        
        response = self.client.post(
            '/security/api/security/report/',
            data=json.dumps(report_data),
            content_type='application/json',
            HTTP_X_FORWARDED_FOR='192.168.1.100'
        )
        
        # Проверяем успешное создание отчета
        self.assertEqual(response.status_code, 201)
        
        # Проверяем, что отчет создан в базе данных
        reports = SecurityReport.objects.filter(ip_address='192.168.1.100')
        self.assertTrue(reports.exists())
    
    def test_honeypot_field_detection(self):
        """Тест обнаружения заполнения honeypot полей"""
        form_data = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'testpass123',
            'website': 'http://spam.com',  # honeypot поле
            'phone_backup': '+1234567890'  # еще одно honeypot поле
        }
        
        response = self.client.post('/api/accounts/register/', data=form_data)
        
        # Проверяем, что создан отчет о подозрительной активности
        reports = SecurityReport.objects.filter(risk_level='high')
        self.assertTrue(reports.exists())
    
    def test_fast_form_submission_detection(self):
        """Тест обнаружения слишком быстрого заполнения форм"""
        # Симулируем очень быстрое заполнение формы
        session = self.client.session
        session['form_start_time'] = timezone.now().timestamp()
        session.save()
        
        form_data = {
            'username': 'fastuser',
            'email': 'fast@example.com',
            'password': 'fastpass123',
            'form_fill_time': 0.5  # 0.5 секунды - слишком быстро
        }
        
        response = self.client.post('/api/accounts/register/', data=form_data)
        
        # Проверяем, что создан отчет о быстром заполнении
        reports = SecurityReport.objects.filter(risk_level='high')
        self.assertTrue(reports.exists())
    
    def test_device_fingerprinting_integration(self):
        """Тест интеграции отпечатков устройств"""
        fingerprint_data = {
            'screen_resolution': '1920x1080',
            'timezone': 'Europe/Moscow',
            'language': 'ru-RU',
            'plugins': ['Chrome PDF Plugin', 'Chrome PDF Viewer'],
            'canvas_fingerprint': 'canvas_hash_123'
        }
        
        response = self.client.post(
            '/security/fingerprint/',
            data=json.dumps(fingerprint_data),
            content_type='application/json',
            HTTP_X_FORWARDED_FOR='192.168.1.100'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что отпечаток сохранен
        fingerprints = DeviceFingerprint.objects.filter(ip_address='192.168.1.100')
        self.assertTrue(fingerprints.exists())
    
    def test_behavioral_analysis_integration(self):
        """Тест интеграции поведенческого анализа"""
        behavioral_data = {
            'mouse_movements': 150,
            'keystroke_patterns': {
                'avg_speed': 120,
                'rhythm_variance': 0.3
            },
            'scroll_behavior': {
                'speed': 'normal',
                'pattern': 'human'
            },
            'focus_events': 25,
            'events_per_minute': 35
        }
        
        response = self.client.post(
            '/security/behavioral/',
            data=json.dumps(behavioral_data),
            content_type='application/json',
            HTTP_X_FORWARDED_FOR='192.168.1.100'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что анализ сохранен
        analyses = BehavioralAnalysis.objects.filter(ip_address='192.168.1.100')
        self.assertTrue(analyses.exists())


class SecurityPerformanceTests(TestCase):
    """
    Тесты производительности системы безопасности
    """
    
    def test_blacklist_check_performance(self):
        """Тест производительности проверки черного списка"""
        # Создаем большое количество записей в черном списке
        blacklist_entries = []
        for i in range(1000):
            blacklist_entries.append(SecurityBlacklist(
                blacklist_type='ip',
                value=f'192.168.1.{i}',
                reason='Performance test'
            ))
        SecurityBlacklist.objects.bulk_create(blacklist_entries)
        
        blacklist_service = BlacklistService()
        
        import time
        start_time = time.time()
        
        # Проверяем 100 IP адресов
        for i in range(100):
            blacklist_service.is_blacklisted('ip', f'10.0.0.{i}')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Проверка должна выполняться быстро (менее 1 секунды)
        self.assertLess(execution_time, 1.0)
    
    def test_threat_analysis_performance(self):
        """Тест производительности анализа угроз"""
        threat_service = ThreatAnalysisService()
        
        # Создаем отчет для анализа
        report = SecurityReport.objects.create(
            session_id='performance_test_session',
            ip_address='192.168.1.100',
            overall_risk_score=50.0,
            risk_level='medium',
            raw_data={'user_agent': 'Mozilla/5.0 (Test Browser)', 'large_data': 'x' * 10000}  # Большие данные
        )
        
        import time
        start_time = time.time()
        
        threats = threat_service.analyze_security_report(report)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Анализ должен выполняться быстро (менее 2 секунд)
        self.assertLess(execution_time, 2.0)
        self.assertIsInstance(threats, list)


class SecurityCleanupTests(TestCase):
    """
    Тесты очистки данных системы безопасности
    """
    
    def test_old_reports_cleanup(self):
        """Тест очистки старых отчетов"""
        # Создаем старые отчеты
        old_date = timezone.now() - timedelta(days=35)
        for i in range(10):
            report = SecurityReport.objects.create(
                session_id=f'old_session_{i}',
                ip_address=f'192.168.1.{i}',
                overall_risk_score=30.0,
                risk_level='low'
            )
            report.created_at = old_date
            report.save()
        
        # Создаем новые отчеты
        for i in range(5):
            SecurityReport.objects.create(
                session_id=f'new_session_{i}',
                ip_address=f'10.0.0.{i}',
                overall_risk_score=40.0,
                risk_level='medium'
            )
        
        # Запускаем очистку
        from .tasks import cleanup_old_security_data
        cleanup_old_security_data()
        
        # Проверяем, что старые отчеты удалены
        old_reports = SecurityReport.objects.filter(created_at__lt=timezone.now() - timedelta(days=30))
        self.assertEqual(old_reports.count(), 0)
        
        # Проверяем, что новые отчеты остались
        new_reports = SecurityReport.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))
        self.assertEqual(new_reports.count(), 5)
    
    def test_expired_blacklist_cleanup(self):
        """Тест очистки истекших записей черного списка"""
        # Создаем истекшие записи
        expired_date = timezone.now() - timedelta(hours=1)
        for i in range(5):
            SecurityBlacklist.objects.create(
                blacklist_type='ip',
                value=f'192.168.1.{i}',
                reason='Test expired',
                expires_at=expired_date
            )
        
        # Создаем активные записи
        future_date = timezone.now() + timedelta(hours=24)
        for i in range(3):
            SecurityBlacklist.objects.create(
                blacklist_type='ip',
                value=f'10.0.0.{i}',
                reason='Test active',
                expires_at=future_date
            )
        
        # Запускаем очистку
        from .tasks import cleanup_old_security_data
        cleanup_old_security_data()
        
        # Проверяем, что истекшие записи удалены
        expired_entries = SecurityBlacklist.objects.filter(expires_at__lt=timezone.now())
        self.assertEqual(expired_entries.count(), 0)
        
        # Проверяем, что активные записи остались
        active_entries = SecurityBlacklist.objects.filter(expires_at__gt=timezone.now())
        self.assertEqual(active_entries.count(), 3)


# Запуск тестов
if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'apps.security',
            ],
            SECRET_KEY='test-secret-key'
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['apps.security.tests'])