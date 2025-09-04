from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import json
import sys
from ...services.monitoring_service import monitoring_service
from ...models.security_report import SecurityReport, ThreatDetection
from ...settings.security_settings import get_security_setting


class Command(BaseCommand):
    help = 'Управление мониторингом безопасности'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['run', 'status', 'stats', 'alerts', 'test'],
            help='Действие для выполнения'
        )
        
        parser.add_argument(
            '--format',
            choices=['console', 'json'],
            default='console',
            help='Формат вывода'
        )
        
        parser.add_argument(
            '--period',
            choices=['1h', '6h', '24h', '7d'],
            default='24h',
            help='Период для анализа'
        )
        
        parser.add_argument(
            '--output',
            help='Файл для сохранения результатов'
        )
        
        parser.add_argument(
            '--threshold',
            type=float,
            help='Порог риска для фильтрации'
        )
        
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='Отправлять алерты при обнаружении проблем'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'run':
                self.run_monitoring(options)
            elif action == 'status':
                self.show_status(options)
            elif action == 'stats':
                self.show_stats(options)
            elif action == 'alerts':
                self.show_alerts(options)
            elif action == 'test':
                self.test_monitoring(options)
        
        except Exception as e:
            raise CommandError(f'Ошибка при выполнении команды: {str(e)}')
    
    def run_monitoring(self, options):
        """Запускает мониторинг безопасности"""
        self.stdout.write('Запуск мониторинга безопасности...')
        
        # Запускаем все проверки
        alerts = monitoring_service.run_all_checks()
        
        result = {
            'timestamp': timezone.now().isoformat(),
            'alerts_found': len(alerts),
            'alerts': alerts
        }
        
        if options['format'] == 'json':
            output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            output = self._format_monitoring_result(result)
        
        # Сохраняем в файл или выводим в консоль
        if options['output']:
            with open(options['output'], 'w', encoding='utf-8') as f:
                f.write(output)
            self.stdout.write(
                self.style.SUCCESS(f'Результаты сохранены в {options["output"]}')
            )
        else:
            self.stdout.write(output)
        
        # Показываем итоги
        if alerts:
            self.stdout.write(
                self.style.WARNING(f'Обнаружено {len(alerts)} алертов безопасности')
            )
            for alert in alerts:
                severity_style = {
                    'low': self.style.SUCCESS,
                    'medium': self.style.WARNING,
                    'high': self.style.ERROR,
                    'critical': self.style.ERROR
                }.get(alert.get('severity', 'medium'), self.style.WARNING)
                
                self.stdout.write(
                    severity_style(f"- {alert['type']}: {alert.get('severity', 'unknown')}")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('Алертов безопасности не обнаружено')
            )
    
    def show_status(self, options):
        """Показывает статус системы мониторинга"""
        self.stdout.write('Статус системы мониторинга:')
        
        # Проверяем настройки
        monitoring_enabled = get_security_setting('SECURITY_MONITORING_ENABLED', True)
        notifications_enabled = get_security_setting('SECURITY_NOTIFICATIONS_ENABLED', True)
        
        status = {
            'monitoring_enabled': monitoring_enabled,
            'notifications_enabled': notifications_enabled,
            'email_notifications': len(get_security_setting('SECURITY_EMAIL_NOTIFICATIONS', [])),
            'webhook_configured': bool(get_security_setting('SECURITY_WEBHOOK_URL')),
            'thresholds': {
                'mass_registration': get_security_setting('MASS_REGISTRATION_THRESHOLD', 10),
                'suspicious_ip': get_security_setting('SUSPICIOUS_IP_THRESHOLD', 5),
                'high_risk': get_security_setting('RISK_THRESHOLD_HIGH', 0.8)
            }
        }
        
        if options['format'] == 'json':
            self.stdout.write(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            self.stdout.write(f"Мониторинг: {'✓ Включен' if monitoring_enabled else '✗ Отключен'}")
            self.stdout.write(f"Уведомления: {'✓ Включены' if notifications_enabled else '✗ Отключены'}")
            self.stdout.write(f"Email уведомления: {status['email_notifications']} адресов")
            self.stdout.write(f"Webhook: {'✓ Настроен' if status['webhook_configured'] else '✗ Не настроен'}")
            self.stdout.write("\nПороги алертов:")
            for key, value in status['thresholds'].items():
                self.stdout.write(f"  {key}: {value}")
    
    def show_stats(self, options):
        """Показывает статистику безопасности"""
        period = options['period']
        
        # Определяем временной период
        period_map = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7)
        }
        
        time_delta = period_map.get(period, timedelta(hours=24))
        start_time = timezone.now() - time_delta
        
        # Собираем статистику
        stats = {
            'period': period,
            'start_time': start_time.isoformat(),
            'end_time': timezone.now().isoformat(),
            'total_reports': SecurityReport.objects.filter(
                created_at__gte=start_time
            ).count(),
            'total_threats': ThreatDetection.objects.filter(
                detected_at__gte=start_time
            ).count(),
            'high_risk_reports': SecurityReport.objects.filter(
                created_at__gte=start_time,
                risk_score__gte=options.get('threshold', 0.8)
            ).count(),
            'automation_detected': SecurityReport.objects.filter(
                created_at__gte=start_time,
                device_fingerprint_data__contains='"automation_detected": true'
            ).count(),
            'unique_ips': SecurityReport.objects.filter(
                created_at__gte=start_time
            ).values('ip_address').distinct().count()
        }
        
        # Дополнительная статистика
        threat_types = ThreatDetection.objects.filter(
            detected_at__gte=start_time
        ).values('threat_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['threat_types'] = list(threat_types)
        
        if options['format'] == 'json':
            output = json.dumps(stats, indent=2, ensure_ascii=False)
        else:
            output = self._format_stats(stats)
        
        if options['output']:
            with open(options['output'], 'w', encoding='utf-8') as f:
                f.write(output)
            self.stdout.write(
                self.style.SUCCESS(f'Статистика сохранена в {options["output"]}')
            )
        else:
            self.stdout.write(output)
    
    def show_alerts(self, options):
        """Показывает последние алерты"""
        period = options['period']
        
        # Определяем временной период
        period_map = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7)
        }
        
        time_delta = period_map.get(period, timedelta(hours=24))
        start_time = timezone.now() - time_delta
        
        # Получаем данные для алертов
        high_risk_reports = SecurityReport.objects.filter(
            created_at__gte=start_time,
            risk_score__gte=0.8
        ).order_by('-created_at')[:10]
        
        recent_threats = ThreatDetection.objects.filter(
            detected_at__gte=start_time
        ).order_by('-detected_at')[:10]
        
        alerts_data = {
            'period': period,
            'high_risk_reports': [
                {
                    'id': report.id,
                    'ip_address': report.ip_address,
                    'risk_score': float(report.risk_score),
                    'created_at': report.created_at.isoformat(),
                    'request_path': report.request_path
                }
                for report in high_risk_reports
            ],
            'recent_threats': [
                {
                    'id': threat.id,
                    'threat_type': threat.threat_type,
                    'severity': threat.severity,
                    'ip_address': threat.ip_address,
                    'detected_at': threat.detected_at.isoformat(),
                    'status': threat.status
                }
                for threat in recent_threats
            ]
        }
        
        if options['format'] == 'json':
            output = json.dumps(alerts_data, indent=2, ensure_ascii=False)
        else:
            output = self._format_alerts(alerts_data)
        
        if options['output']:
            with open(options['output'], 'w', encoding='utf-8') as f:
                f.write(output)
            self.stdout.write(
                self.style.SUCCESS(f'Алерты сохранены в {options["output"]}')
            )
        else:
            self.stdout.write(output)
    
    def test_monitoring(self, options):
        """Тестирует систему мониторинга"""
        self.stdout.write('Тестирование системы мониторинга...')
        
        tests = [
            ('Проверка настроек', self._test_settings),
            ('Проверка подключения к БД', self._test_database),
            ('Проверка сервиса мониторинга', self._test_monitoring_service),
            ('Проверка уведомлений', self._test_notifications)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            self.stdout.write(f'Выполняется: {test_name}...', ending='')
            try:
                result = test_func()
                if result:
                    self.stdout.write(self.style.SUCCESS(' ✓'))
                    results.append({'test': test_name, 'status': 'passed', 'message': result})
                else:
                    self.stdout.write(self.style.ERROR(' ✗'))
                    results.append({'test': test_name, 'status': 'failed', 'message': 'Тест не прошел'})
            except Exception as e:
                self.stdout.write(self.style.ERROR(f' ✗ ({str(e)})'))
                results.append({'test': test_name, 'status': 'error', 'message': str(e)})
        
        # Итоги тестирования
        passed = sum(1 for r in results if r['status'] == 'passed')
        total = len(results)
        
        self.stdout.write(f'\nРезультаты тестирования: {passed}/{total} тестов прошли успешно')
        
        if options['format'] == 'json':
            self.stdout.write(json.dumps(results, indent=2, ensure_ascii=False))
    
    def _test_settings(self):
        """Тестирует настройки мониторинга"""
        required_settings = [
            'SECURITY_MONITORING_ENABLED',
            'MASS_REGISTRATION_THRESHOLD',
            'RISK_THRESHOLD_HIGH'
        ]
        
        for setting in required_settings:
            value = get_security_setting(setting)
            if value is None:
                return f'Отсутствует настройка {setting}'
        
        return 'Настройки корректны'
    
    def _test_database(self):
        """Тестирует подключение к базе данных"""
        try:
            SecurityReport.objects.count()
            ThreatDetection.objects.count()
            return 'Подключение к БД работает'
        except Exception as e:
            raise Exception(f'Ошибка БД: {str(e)}')
    
    def _test_monitoring_service(self):
        """Тестирует сервис мониторинга"""
        try:
            stats = monitoring_service.get_monitoring_stats()
            if isinstance(stats, dict):
                return 'Сервис мониторинга работает'
            else:
                return 'Сервис мониторинга вернул некорректные данные'
        except Exception as e:
            raise Exception(f'Ошибка сервиса: {str(e)}')
    
    def _test_notifications(self):
        """Тестирует систему уведомлений"""
        notifications_enabled = get_security_setting('SECURITY_NOTIFICATIONS_ENABLED', True)
        if not notifications_enabled:
            return 'Уведомления отключены'
        
        email_notifications = get_security_setting('SECURITY_EMAIL_NOTIFICATIONS', [])
        webhook_url = get_security_setting('SECURITY_WEBHOOK_URL')
        
        if not email_notifications and not webhook_url:
            return 'Не настроены каналы уведомлений'
        
        return 'Система уведомлений настроена'
    
    def _format_monitoring_result(self, result):
        """Форматирует результат мониторинга для консольного вывода"""
        output = f"Результаты мониторинга ({result['timestamp']}):\n"
        output += f"Обнаружено алертов: {result['alerts_found']}\n\n"
        
        if result['alerts']:
            for alert in result['alerts']:
                output += f"🚨 {alert['type']} ({alert['severity']})\n"
                if 'total_registrations' in alert:
                    output += f"   Регистраций: {alert['total_registrations']}\n"
                if 'detected_ips' in alert:
                    output += f"   Подозрительных IP: {len(alert['detected_ips'])}\n"
                output += "\n"
        
        return output
    
    def _format_stats(self, stats):
        """Форматирует статистику для консольного вывода"""
        output = f"Статистика безопасности за {stats['period']}:\n\n"
        output += f"Всего отчетов: {stats['total_reports']}\n"
        output += f"Всего угроз: {stats['total_threats']}\n"
        output += f"Высокорисковых отчетов: {stats['high_risk_reports']}\n"
        output += f"Обнаружена автоматизация: {stats['automation_detected']}\n"
        output += f"Уникальных IP: {stats['unique_ips']}\n\n"
        
        if stats['threat_types']:
            output += "Типы угроз:\n"
            for threat_type in stats['threat_types']:
                output += f"  {threat_type['threat_type']}: {threat_type['count']}\n"
        
        return output
    
    def _format_alerts(self, alerts_data):
        """Форматирует алерты для консольного вывода"""
        output = f"Алерты за {alerts_data['period']}:\n\n"
        
        if alerts_data['high_risk_reports']:
            output += "Высокорисковые отчеты:\n"
            for report in alerts_data['high_risk_reports']:
                output += f"  IP: {report['ip_address']}, Риск: {report['risk_score']:.2f}\n"
            output += "\n"
        
        if alerts_data['recent_threats']:
            output += "Недавние угрозы:\n"
            for threat in alerts_data['recent_threats']:
                output += f"  {threat['threat_type']} ({threat['severity']}) - {threat['ip_address']}\n"
        
        return output