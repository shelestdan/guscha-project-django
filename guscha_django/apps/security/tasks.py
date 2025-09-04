from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from .services.monitoring_service import monitoring_service
from .models.security_report import SecurityReport, ThreatDetection, SecurityBlacklist
from .settings.security_settings import get_security_setting

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_security_monitoring(self):
    """
    Задача для запуска мониторинга безопасности
    """
    try:
        logger.info('Запуск мониторинга безопасности')
        
        # Запускаем все проверки
        alerts = monitoring_service.run_all_checks()
        
        if alerts:
            logger.info(f'Обнаружено {len(alerts)} алертов безопасности')
            for alert in alerts:
                logger.warning(f'Алерт: {alert["type"]} - {alert["severity"]}')
        else:
            logger.debug('Алертов безопасности не обнаружено')
        
        return {
            'status': 'success',
            'alerts_count': len(alerts),
            'alerts': alerts,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f'Ошибка при выполнении мониторинга безопасности: {str(exc)}')
        
        # Повторяем задачу с экспоненциальной задержкой
        countdown = 2 ** self.request.retries * 60  # 1, 2, 4 минуты
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=2)
def cleanup_old_security_data(self):
    """
    Задача для очистки старых данных безопасности
    """
    try:
        logger.info('Запуск очистки старых данных безопасности')
        
        # Получаем настройки хранения данных
        reports_retention_days = get_security_setting('SECURITY_REPORTS_RETENTION_DAYS', 30)
        threats_retention_days = get_security_setting('SECURITY_THREATS_RETENTION_DAYS', 90)
        
        # Удаляем старые отчеты
        reports_cutoff = timezone.now() - timedelta(days=reports_retention_days)
        old_reports = SecurityReport.objects.filter(created_at__lt=reports_cutoff)
        reports_deleted = old_reports.count()
        old_reports.delete()
        
        # Удаляем старые угрозы
        threats_cutoff = timezone.now() - timedelta(days=threats_retention_days)
        old_threats = ThreatDetection.objects.filter(detected_at__lt=threats_cutoff)
        threats_deleted = old_threats.count()
        old_threats.delete()
        
        # Удаляем истекшие записи из черного списка
        expired_blacklist = SecurityBlacklist.objects.filter(
            expires_at__lt=timezone.now(),
            expires_at__isnull=False
        )
        blacklist_deleted = expired_blacklist.count()
        expired_blacklist.delete()
        
        logger.info(
            f'Очистка завершена: удалено {reports_deleted} отчетов, '
            f'{threats_deleted} угроз, {blacklist_deleted} записей из черного списка'
        )
        
        return {
            'status': 'success',
            'reports_deleted': reports_deleted,
            'threats_deleted': threats_deleted,
            'blacklist_deleted': blacklist_deleted,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f'Ошибка при очистке данных безопасности: {str(exc)}')
        
        # Повторяем задачу
        countdown = 300  # 5 минут
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=3)
def analyze_security_trends(self):
    """
    Задача для анализа трендов безопасности
    """
    try:
        logger.info('Запуск анализа трендов безопасности')
        
        # Анализируем данные за последние 7 дней
        week_ago = timezone.now() - timedelta(days=7)
        
        # Тренды по дням
        daily_stats = []
        for i in range(7):
            day_start = week_ago + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_reports = SecurityReport.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            )
            
            day_threats = ThreatDetection.objects.filter(
                detected_at__gte=day_start,
                detected_at__lt=day_end
            )
            
            daily_stats.append({
                'date': day_start.date().isoformat(),
                'reports': day_reports.count(),
                'threats': day_threats.count(),
                'high_risk': day_reports.filter(risk_score__gte=0.8).count(),
                'automation': day_reports.filter(
                    device_fingerprint_data__contains='"automation_detected": true'
                ).count()
            })
        
        # Анализируем тренды
        trends = {
            'period': '7 дней',
            'daily_stats': daily_stats,
            'total_reports': sum(day['reports'] for day in daily_stats),
            'total_threats': sum(day['threats'] for day in daily_stats),
            'avg_daily_reports': sum(day['reports'] for day in daily_stats) / 7,
            'avg_daily_threats': sum(day['threats'] for day in daily_stats) / 7
        }
        
        # Определяем тренды
        recent_avg = sum(day['reports'] for day in daily_stats[-3:]) / 3
        earlier_avg = sum(day['reports'] for day in daily_stats[:3]) / 3
        
        if recent_avg > earlier_avg * 1.5:
            trends['trend'] = 'increasing'
            trends['trend_severity'] = 'high' if recent_avg > earlier_avg * 2 else 'medium'
        elif recent_avg < earlier_avg * 0.5:
            trends['trend'] = 'decreasing'
            trends['trend_severity'] = 'low'
        else:
            trends['trend'] = 'stable'
            trends['trend_severity'] = 'normal'
        
        logger.info(f'Анализ трендов завершен: тренд {trends["trend"]}')
        
        # Если тренд негативный, отправляем алерт
        if trends['trend'] == 'increasing' and trends['trend_severity'] == 'high':
            alert_data = {
                'type': 'security_trend_alert',
                'severity': 'medium',
                'timestamp': timezone.now().isoformat(),
                'trend': trends['trend'],
                'recent_avg': recent_avg,
                'earlier_avg': earlier_avg,
                'increase_factor': recent_avg / earlier_avg if earlier_avg > 0 else 0
            }
            
            monitoring_service._send_alert(alert_data)
        
        return {
            'status': 'success',
            'trends': trends,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f'Ошибка при анализе трендов безопасности: {str(exc)}')
        
        countdown = 2 ** self.request.retries * 300  # 5, 10, 20 минут
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=2)
def update_threat_intelligence(self):
    """
    Задача для обновления данных об угрозах
    """
    try:
        logger.info('Запуск обновления данных об угрозах')
        
        # Анализируем неразрешенные угрозы
        unresolved_threats = ThreatDetection.objects.filter(
            status='detected'
        )
        
        updated_count = 0
        
        for threat in unresolved_threats:
            # Проверяем, есть ли новые данные для этой угрозы
            recent_reports = SecurityReport.objects.filter(
                ip_address=threat.ip_address,
                created_at__gte=threat.detected_at
            )
            
            if recent_reports.exists():
                # Обновляем информацию об угрозе
                latest_report = recent_reports.latest('created_at')
                
                # Если активность продолжается, повышаем приоритет
                if recent_reports.count() > 5:
                    if threat.severity == 'low':
                        threat.severity = 'medium'
                    elif threat.severity == 'medium':
                        threat.severity = 'high'
                    
                    threat.description += f' [Обновлено: продолжающаяся активность - {recent_reports.count()} отчетов]'
                    threat.save()
                    updated_count += 1
        
        # Автоматически закрываем старые угрозы без активности
        old_threats = ThreatDetection.objects.filter(
            status='detected',
            detected_at__lt=timezone.now() - timedelta(days=7)
        )
        
        auto_resolved_count = 0
        for threat in old_threats:
            # Проверяем, была ли активность за последние 7 дней
            recent_activity = SecurityReport.objects.filter(
                ip_address=threat.ip_address,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if not recent_activity:
                threat.status = 'resolved'
                threat.resolution_notes = 'Автоматически закрыто - нет активности 7 дней'
                threat.resolved_at = timezone.now()
                threat.save()
                auto_resolved_count += 1
        
        logger.info(
            f'Обновление угроз завершено: обновлено {updated_count}, '
            f'автоматически закрыто {auto_resolved_count}'
        )
        
        return {
            'status': 'success',
            'updated_threats': updated_count,
            'auto_resolved_threats': auto_resolved_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f'Ошибка при обновлении данных об угрозах: {str(exc)}')
        
        countdown = 600  # 10 минут
        raise self.retry(exc=exc, countdown=countdown)


@shared_task
def generate_security_report():
    """
    Задача для генерации ежедневного отчета по безопасности
    """
    try:
        logger.info('Генерация ежедневного отчета по безопасности')
        
        # Статистика за последние 24 часа
        yesterday = timezone.now() - timedelta(hours=24)
        
        report_data = {
            'period': '24 часа',
            'generated_at': timezone.now().isoformat(),
            'total_reports': SecurityReport.objects.filter(
                created_at__gte=yesterday
            ).count(),
            'total_threats': ThreatDetection.objects.filter(
                detected_at__gte=yesterday
            ).count(),
            'high_risk_reports': SecurityReport.objects.filter(
                created_at__gte=yesterday,
                risk_score__gte=0.8
            ).count(),
            'automation_detected': SecurityReport.objects.filter(
                created_at__gte=yesterday,
                device_fingerprint_data__contains='"automation_detected": true'
            ).count(),
            'unique_ips': SecurityReport.objects.filter(
                created_at__gte=yesterday
            ).values('ip_address').distinct().count(),
            'blacklist_additions': SecurityBlacklist.objects.filter(
                created_at__gte=yesterday
            ).count()
        }
        
        # Топ угроз
        top_threats = ThreatDetection.objects.filter(
            detected_at__gte=yesterday
        ).values('threat_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        report_data['top_threats'] = list(top_threats)
        
        # Топ подозрительных IP
        top_ips = SecurityReport.objects.filter(
            created_at__gte=yesterday,
            risk_score__gte=0.5
        ).values('ip_address').annotate(
            count=Count('id'),
            avg_risk=Avg('risk_score')
        ).order_by('-avg_risk')[:10]
        
        report_data['top_suspicious_ips'] = list(top_ips)
        
        logger.info('Ежедневный отчет по безопасности сгенерирован')
        
        # Отправляем отчет как алерт (если настроено)
        if get_security_setting('DAILY_REPORTS_ENABLED', False):
            alert_data = {
                'type': 'daily_security_report',
                'severity': 'info',
                'timestamp': timezone.now().isoformat(),
                'report': report_data
            }
            
            monitoring_service._send_alert(alert_data)
        
        return report_data
        
    except Exception as e:
        logger.error(f'Ошибка при генерации отчета по безопасности: {str(e)}')
        return {'status': 'error', 'error': str(e)}