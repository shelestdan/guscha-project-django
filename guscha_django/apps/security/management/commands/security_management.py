import json
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Q
from ...models.security_report import SecurityReport, ThreatDetection, SecurityBlacklist
from ...services.security_analysis_service import SecurityAnalysisService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Управление системой безопасности'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Доступные действия')
        
        # Анализ безопасности
        analyze_parser = subparsers.add_parser('analyze', help='Анализ данных безопасности')
        analyze_parser.add_argument(
            '--days', type=int, default=7,
            help='Количество дней для анализа (по умолчанию: 7)'
        )
        analyze_parser.add_argument(
            '--output', choices=['console', 'json', 'file'], default='console',
            help='Формат вывода результатов'
        )
        analyze_parser.add_argument(
            '--file', type=str,
            help='Файл для сохранения результатов (при output=file)'
        )
        
        # Очистка старых данных
        cleanup_parser = subparsers.add_parser('cleanup', help='Очистка старых данных')
        cleanup_parser.add_argument(
            '--days', type=int, default=30,
            help='Удалить данные старше указанного количества дней'
        )
        cleanup_parser.add_argument(
            '--dry-run', action='store_true',
            help='Показать что будет удалено, но не удалять'
        )
        
        # Управление черным списком
        blacklist_parser = subparsers.add_parser('blacklist', help='Управление черным списком')
        blacklist_subparsers = blacklist_parser.add_subparsers(dest='blacklist_action')
        
        # Добавление в черный список
        add_parser = blacklist_subparsers.add_parser('add', help='Добавить в черный список')
        add_parser.add_argument('--type', choices=['ip', 'fingerprint', 'user_agent'], required=True)
        add_parser.add_argument('--value', required=True, help='Значение для блокировки')
        add_parser.add_argument('--reason', required=True, help='Причина блокировки')
        add_parser.add_argument('--expires', type=int, help='Срок действия в часах')
        
        # Удаление из черного списка
        remove_parser = blacklist_subparsers.add_parser('remove', help='Удалить из черного списка')
        remove_parser.add_argument('--type', choices=['ip', 'fingerprint', 'user_agent'], required=True)
        remove_parser.add_argument('--value', required=True, help='Значение для разблокировки')
        
        # Список черного списка
        list_parser = blacklist_subparsers.add_parser('list', help='Показать черный список')
        list_parser.add_argument('--type', choices=['ip', 'fingerprint', 'user_agent'])
        list_parser.add_argument('--active-only', action='store_true', help='Только активные записи')
        
        # Статистика
        stats_parser = subparsers.add_parser('stats', help='Показать статистику безопасности')
        stats_parser.add_argument(
            '--days', type=int, default=7,
            help='Период для статистики в днях'
        )
        
        # Мониторинг угроз
        monitor_parser = subparsers.add_parser('monitor', help='Мониторинг угроз')
        monitor_parser.add_argument(
            '--threshold', type=float, default=0.7,
            help='Порог риска для оповещений (0.0-1.0)'
        )
        monitor_parser.add_argument(
            '--auto-block', action='store_true',
            help='Автоматически блокировать высокорисковые IP'
        )
    
    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.print_help('manage.py', 'security_management')
            return
        
        try:
            if action == 'analyze':
                self.handle_analyze(options)
            elif action == 'cleanup':
                self.handle_cleanup(options)
            elif action == 'blacklist':
                self.handle_blacklist(options)
            elif action == 'stats':
                self.handle_stats(options)
            elif action == 'monitor':
                self.handle_monitor(options)
            else:
                raise CommandError(f'Неизвестное действие: {action}')
        
        except Exception as e:
            logger.error(f'Ошибка выполнения команды: {str(e)}')
            raise CommandError(f'Ошибка: {str(e)}')
    
    def handle_analyze(self, options):
        """Анализ данных безопасности"""
        days = options['days']
        output_format = options['output']
        output_file = options.get('file')
        
        self.stdout.write(f'Анализ данных за последние {days} дней...')
        
        # Получаем данные
        start_date = timezone.now() - timedelta(days=days)
        reports = SecurityReport.objects.filter(created_at__gte=start_date)
        
        # Анализируем
        service = SecurityAnalysisService()
        analysis_results = {
            'period': f'{days} дней',
            'total_reports': reports.count(),
            'risk_distribution': self._get_risk_distribution(reports),
            'threat_types': self._get_threat_types(start_date),
            'top_suspicious_ips': self._get_top_suspicious_ips(reports),
            'automation_detection': self._get_automation_stats(reports),
            'behavioral_analysis': self._get_behavioral_stats(reports)
        }
        
        # Выводим результаты
        if output_format == 'json':
            result_json = json.dumps(analysis_results, indent=2, ensure_ascii=False, default=str)
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result_json)
                self.stdout.write(f'Результаты сохранены в {output_file}')
            else:
                self.stdout.write(result_json)
        else:
            self._print_analysis_results(analysis_results)
    
    def handle_cleanup(self, options):
        """Очистка старых данных"""
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Подсчитываем что будет удалено
        old_reports = SecurityReport.objects.filter(created_at__lt=cutoff_date)
        old_threats = ThreatDetection.objects.filter(detected_at__lt=cutoff_date)
        expired_blacklist = SecurityBlacklist.objects.filter(
            expires_at__lt=timezone.now(),
            expires_at__isnull=False
        )
        
        self.stdout.write(f'Данные старше {days} дней:')
        self.stdout.write(f'  - Отчеты безопасности: {old_reports.count()}')
        self.stdout.write(f'  - Обнаружения угроз: {old_threats.count()}')
        self.stdout.write(f'  - Истекшие записи черного списка: {expired_blacklist.count()}')
        
        if dry_run:
            self.stdout.write('Режим тестирования - данные не удалены')
            return
        
        # Удаляем данные
        deleted_reports = old_reports.delete()[0]
        deleted_threats = old_threats.delete()[0]
        deleted_blacklist = expired_blacklist.delete()[0]
        
        self.stdout.write(self.style.SUCCESS(
            f'Удалено: {deleted_reports} отчетов, {deleted_threats} угроз, '
            f'{deleted_blacklist} записей черного списка'
        ))
    
    def handle_blacklist(self, options):
        """Управление черным списком"""
        blacklist_action = options.get('blacklist_action')
        
        if blacklist_action == 'add':
            self._add_to_blacklist(options)
        elif blacklist_action == 'remove':
            self._remove_from_blacklist(options)
        elif blacklist_action == 'list':
            self._list_blacklist(options)
        else:
            self.stdout.write('Доступные действия: add, remove, list')
    
    def handle_stats(self, options):
        """Показать статистику"""
        days = options['days']
        start_date = timezone.now() - timedelta(days=days)
        
        # Общая статистика
        total_reports = SecurityReport.objects.filter(created_at__gte=start_date).count()
        total_threats = ThreatDetection.objects.filter(detected_at__gte=start_date).count()
        active_blacklist = SecurityBlacklist.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\nСтатистика за последние {days} дней:')
        self.stdout.write(f'  Всего отчетов: {total_reports}')
        self.stdout.write(f'  Обнаружено угроз: {total_threats}')
        self.stdout.write(f'  Активных блокировок: {active_blacklist}')
        
        # Распределение по уровням риска
        risk_stats = SecurityReport.objects.filter(
            created_at__gte=start_date
        ).values('risk_level').annotate(count=Count('id'))
        
        self.stdout.write('\nРаспределение по уровням риска:')
        for stat in risk_stats:
            self.stdout.write(f'  {stat["risk_level"]}: {stat["count"]}')
    
    def handle_monitor(self, options):
        """Мониторинг угроз"""
        threshold = options['threshold']
        auto_block = options['auto_block']
        
        # Ищем высокорисковые отчеты за последний час
        one_hour_ago = timezone.now() - timedelta(hours=1)
        high_risk_reports = SecurityReport.objects.filter(
            created_at__gte=one_hour_ago,
            risk_score__gte=threshold
        )
        
        if not high_risk_reports.exists():
            self.stdout.write('Высокорисковых событий не обнаружено')
            return
        
        self.stdout.write(f'Обнаружено {high_risk_reports.count()} высокорисковых событий:')
        
        for report in high_risk_reports:
            self.stdout.write(
                f'  IP: {report.ip_address}, Риск: {report.risk_score:.2f}, '
                f'Время: {report.created_at}'
            )
            
            if auto_block and report.risk_score >= 0.9:
                # Автоматическая блокировка
                SecurityBlacklist.objects.get_or_create(
                    blocked_type='ip',
                    blocked_value=report.ip_address,
                    defaults={
                        'reason': f'Автоблокировка: высокий риск {report.risk_score:.2f}',
                        'expires_at': timezone.now() + timedelta(hours=24)
                    }
                )
                self.stdout.write(
                    self.style.WARNING(f'    -> IP {report.ip_address} заблокирован')
                )
    
    def _add_to_blacklist(self, options):
        """Добавить в черный список"""
        blocked_type = options['type']
        blocked_value = options['value']
        reason = options['reason']
        expires_hours = options.get('expires')
        
        expires_at = None
        if expires_hours:
            expires_at = timezone.now() + timedelta(hours=expires_hours)
        
        blacklist_entry, created = SecurityBlacklist.objects.get_or_create(
            blocked_type=blocked_type,
            blocked_value=blocked_value,
            defaults={
                'reason': reason,
                'expires_at': expires_at
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Добавлено в черный список: {blocked_type} = {blocked_value}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Уже в черном списке: {blocked_type} = {blocked_value}'
                )
            )
    
    def _remove_from_blacklist(self, options):
        """Удалить из черного списка"""
        blocked_type = options['type']
        blocked_value = options['value']
        
        try:
            blacklist_entry = SecurityBlacklist.objects.get(
                blocked_type=blocked_type,
                blocked_value=blocked_value
            )
            blacklist_entry.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Удалено из черного списка: {blocked_type} = {blocked_value}'
                )
            )
        except SecurityBlacklist.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Не найдено в черном списке: {blocked_type} = {blocked_value}'
                )
            )
    
    def _list_blacklist(self, options):
        """Показать черный список"""
        blocked_type = options.get('type')
        active_only = options.get('active_only', False)
        
        queryset = SecurityBlacklist.objects.all()
        
        if blocked_type:
            queryset = queryset.filter(blocked_type=blocked_type)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        if not queryset.exists():
            self.stdout.write('Черный список пуст')
            return
        
        self.stdout.write('Черный список:')
        for entry in queryset:
            status = 'Активно' if entry.is_active else 'Неактивно'
            expires = entry.expires_at.strftime('%Y-%m-%d %H:%M') if entry.expires_at else 'Никогда'
            self.stdout.write(
                f'  {entry.blocked_type}: {entry.blocked_value} '
                f'({status}, истекает: {expires}) - {entry.reason}'
            )
    
    def _get_risk_distribution(self, reports):
        """Получить распределение по уровням риска"""
        return dict(
            reports.values('risk_level').annotate(count=Count('id')).values_list('risk_level', 'count')
        )
    
    def _get_threat_types(self, start_date):
        """Получить типы угроз"""
        return dict(
            ThreatDetection.objects.filter(
                detected_at__gte=start_date
            ).values('threat_type').annotate(count=Count('id')).values_list('threat_type', 'count')
        )
    
    def _get_top_suspicious_ips(self, reports, limit=10):
        """Получить топ подозрительных IP"""
        return list(
            reports.values('ip_address').annotate(
                count=Count('id'),
                avg_risk=models.Avg('risk_score')
            ).order_by('-avg_risk', '-count')[:limit].values_list('ip_address', 'count', 'avg_risk')
        )
    
    def _get_automation_stats(self, reports):
        """Статистика по автоматизации"""
        total = reports.count()
        if total == 0:
            return {}
        
        automation_detected = reports.filter(
            device_fingerprint_data__contains='"automation_detected": true'
        ).count()
        
        return {
            'total_reports': total,
            'automation_detected': automation_detected,
            'automation_percentage': (automation_detected / total) * 100
        }
    
    def _get_behavioral_stats(self, reports):
        """Статистика поведенческого анализа"""
        total = reports.count()
        if total == 0:
            return {}
        
        human_like = reports.filter(
            behavioral_data__contains='"human_like_behavior": true'
        ).count()
        
        return {
            'total_reports': total,
            'human_like_behavior': human_like,
            'human_like_percentage': (human_like / total) * 100
        }
    
    def _print_analysis_results(self, results):
        """Вывести результаты анализа в консоль"""
        self.stdout.write(f'\nАнализ безопасности за {results["period"]}:')
        self.stdout.write(f'Всего отчетов: {results["total_reports"]}')
        
        if results['risk_distribution']:
            self.stdout.write('\nРаспределение по уровням риска:')
            for level, count in results['risk_distribution'].items():
                self.stdout.write(f'  {level}: {count}')
        
        if results['threat_types']:
            self.stdout.write('\nТипы угроз:')
            for threat_type, count in results['threat_types'].items():
                self.stdout.write(f'  {threat_type}: {count}')
        
        if results['top_suspicious_ips']:
            self.stdout.write('\nТоп подозрительных IP:')
            for ip, count, avg_risk in results['top_suspicious_ips']:
                self.stdout.write(f'  {ip}: {count} отчетов, средний риск: {avg_risk:.2f}')