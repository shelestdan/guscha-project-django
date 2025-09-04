import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Q
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from ..models.security_report import SecurityReport, ThreatDetection
from ..settings.security_settings import get_security_setting
import requests

logger = logging.getLogger(__name__)


class SecurityMonitoringService:
    """
    Сервис для мониторинга безопасности и отправки алертов
    """
    
    def __init__(self):
        self.cache_timeout = get_security_setting('SECURITY_CACHE_TIMEOUT', 300)
        self.notification_enabled = get_security_setting('SECURITY_NOTIFICATIONS_ENABLED', True)
        self.email_notifications = get_security_setting('SECURITY_EMAIL_NOTIFICATIONS', [])
        self.webhook_url = get_security_setting('SECURITY_WEBHOOK_URL')
        
        # Пороги для алертов
        self.mass_registration_threshold = get_security_setting('MASS_REGISTRATION_THRESHOLD', 10)
        self.mass_registration_window = get_security_setting('MASS_REGISTRATION_WINDOW_MINUTES', 5)
        self.suspicious_ip_threshold = get_security_setting('SUSPICIOUS_IP_THRESHOLD', 5)
        self.high_risk_threshold = get_security_setting('RISK_THRESHOLD_HIGH', 0.8)
        
    def check_mass_registrations(self) -> Optional[Dict]:
        """
        Проверяет массовые регистрации
        """
        try:
            # Проверяем за последние N минут
            time_window = timezone.now() - timedelta(minutes=self.mass_registration_window)
            
            # Подсчитываем регистрации по IP
            registrations_by_ip = SecurityReport.objects.filter(
                created_at__gte=time_window,
                user__isnull=False  # Только отчеты с привязанными пользователями (регистрации)
            ).values('ip_address').annotate(
                count=Count('id')
            ).filter(count__gte=self.mass_registration_threshold)
            
            if registrations_by_ip.exists():
                alert_data = {
                    'type': 'mass_registration',
                    'severity': 'high',
                    'timestamp': timezone.now().isoformat(),
                    'window_minutes': self.mass_registration_window,
                    'threshold': self.mass_registration_threshold,
                    'detected_ips': list(registrations_by_ip),
                    'total_registrations': sum(item['count'] for item in registrations_by_ip)
                }
                
                self._send_alert(alert_data)
                return alert_data
            
            return None
            
        except Exception as e:
            logger.error(f'Ошибка при проверке массовых регистраций: {str(e)}')
            return None
    
    def check_suspicious_activity(self) -> Optional[Dict]:
        """
        Проверяет подозрительную активность
        """
        try:
            # Проверяем за последний час
            one_hour_ago = timezone.now() - timedelta(hours=1)
            
            # Высокорисковые отчеты
            high_risk_reports = SecurityReport.objects.filter(
                created_at__gte=one_hour_ago,
                overall_risk_score__gte=self.high_risk_threshold
            )
            
            if high_risk_reports.count() >= 5:  # Порог для алерта
                # Группируем по IP
                suspicious_ips = high_risk_reports.values('ip_address').annotate(
                    count=Count('id'),
                    avg_risk=models.Avg('overall_risk_score')
                ).order_by('-avg_risk')
                
                alert_data = {
                    'type': 'suspicious_activity',
                    'severity': 'medium',
                    'timestamp': timezone.now().isoformat(),
                    'high_risk_reports': high_risk_reports.count(),
                    'suspicious_ips': list(suspicious_ips[:10]),  # Топ 10
                    'time_window': '1 час'
                }
                
                self._send_alert(alert_data)
                return alert_data
            
            return None
            
        except Exception as e:
            logger.error(f'Ошибка при проверке подозрительной активности: {str(e)}')
            return None
    
    def check_automation_attacks(self) -> Optional[Dict]:
        """
        Проверяет атаки автоматизации
        """
        try:
            # Проверяем за последние 30 минут
            thirty_minutes_ago = timezone.now() - timedelta(minutes=30)
            
            # Отчеты с обнаруженной автоматизацией
            automation_reports = SecurityReport.objects.filter(
                created_at__gte=thirty_minutes_ago,
                device_fingerprint_data__contains='"automation_detected": true'
            )
            
            if automation_reports.count() >= 3:  # Порог для алерта
                # Анализируем источники
                automation_sources = automation_reports.values('ip_address').annotate(
                    count=Count('id')
                ).order_by('-count')
                
                alert_data = {
                    'type': 'automation_attack',
                    'severity': 'high',
                    'timestamp': timezone.now().isoformat(),
                    'automation_reports': automation_reports.count(),
                    'sources': list(automation_sources[:5]),
                    'time_window': '30 минут'
                }
                
                self._send_alert(alert_data)
                return alert_data
            
            return None
            
        except Exception as e:
            logger.error(f'Ошибка при проверке атак автоматизации: {str(e)}')
            return None
    
    def check_threat_patterns(self) -> Optional[Dict]:
        """
        Проверяет паттерны угроз
        """
        try:
            # Проверяем за последние 2 часа
            two_hours_ago = timezone.now() - timedelta(hours=2)
            
            # Обнаруженные угрозы
            recent_threats = ThreatDetection.objects.filter(
                created_at__gte=two_hours_ago
            )
            
            if recent_threats.count() >= 5:
                # Анализируем типы угроз
                threat_types = recent_threats.values('threat_type').annotate(
                    count=Count('id')
                ).order_by('-count')
                
                # Анализируем серьезность
                severity_distribution = recent_threats.values('severity').annotate(
                    count=Count('id')
                )
                
                alert_data = {
                    'type': 'threat_pattern',
                    'severity': 'medium',
                    'timestamp': timezone.now().isoformat(),
                    'total_threats': recent_threats.count(),
                    'threat_types': list(threat_types),
                    'severity_distribution': list(severity_distribution),
                    'time_window': '2 часа'
                }
                
                self._send_alert(alert_data)
                return alert_data
            
            return None
            
        except Exception as e:
            logger.error(f'Ошибка при проверке паттернов угроз: {str(e)}')
            return None
    
    def run_all_checks(self) -> List[Dict]:
        """
        Запускает все проверки мониторинга
        """
        alerts = []
        
        # Проверяем, не запускались ли проверки недавно
        cache_key = 'security_monitoring_last_run'
        last_run = cache.get(cache_key)
        
        if last_run and (timezone.now() - last_run).seconds < 60:
            logger.debug('Мониторинг уже запускался недавно, пропускаем')
            return alerts
        
        # Обновляем время последнего запуска
        cache.set(cache_key, timezone.now(), 300)
        
        # Запускаем все проверки
        checks = [
            self.check_mass_registrations,
            self.check_suspicious_activity,
            self.check_automation_attacks,
            self.check_threat_patterns
        ]
        
        for check in checks:
            try:
                result = check()
                if result:
                    alerts.append(result)
            except Exception as e:
                logger.error(f'Ошибка при выполнении проверки {check.__name__}: {str(e)}')
        
        return alerts
    
    def _send_alert(self, alert_data: Dict) -> None:
        """
        Отправляет алерт
        """
        if not self.notification_enabled:
            return
        
        try:
            # Проверяем, не отправляли ли уже такой алерт недавно
            alert_key = f"alert_{alert_data['type']}_{alert_data.get('severity', 'unknown')}"
            if cache.get(alert_key):
                logger.debug(f'Алерт {alert_key} уже отправлялся недавно')
                return
            
            # Устанавливаем блокировку на 15 минут
            cache.set(alert_key, True, 900)
            
            # Логируем алерт
            logger.warning(f'Отправка алерта безопасности: {alert_data["type"]}')
            
            # Отправляем email уведомления
            if self.email_notifications:
                self._send_email_alert(alert_data)
            
            # Отправляем webhook
            if self.webhook_url:
                self._send_webhook_alert(alert_data)
            
        except Exception as e:
            logger.error(f'Ошибка при отправке алерта: {str(e)}')
    
    def send_alert(self, alert_data: Dict) -> None:
        """Публичный метод для отправки алертов"""
        self._send_alert(alert_data)
    
    def _send_email_alert(self, alert_data: Dict) -> None:
        """
        Отправляет email алерт
        """
        try:
            subject = f"🚨 Алерт безопасности: {alert_data['type']}"
            
            # Формируем контекст для шаблона
            context = {
                'alert': alert_data,
                'site_name': getattr(settings, 'SITE_NAME', 'Система безопасности'),
                'timestamp': timezone.now()
            }
            
            # Рендерим шаблон (если есть) или используем простой текст
            try:
                message = render_to_string('security/alert_email.html', context)
            except:
                message = self._format_alert_text(alert_data)
            
            # Отправляем email
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'security@example.com'),
                recipient_list=self.email_notifications,
                fail_silently=False,
                html_message=message if '<' in message else None
            )
            
            logger.info(f'Email алерт отправлен: {alert_data["type"]}')
            
        except Exception as e:
            logger.error(f'Ошибка при отправке email алерта: {str(e)}')
    
    def _send_webhook_alert(self, alert_data: Dict) -> None:
        """
        Отправляет webhook алерт
        """
        try:
            payload = {
                'alert_type': alert_data['type'],
                'severity': alert_data['severity'],
                'timestamp': alert_data['timestamp'],
                'data': alert_data,
                'source': 'security_monitoring'
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f'Webhook алерт отправлен: {alert_data["type"]}')
            else:
                logger.warning(
                    f'Webhook вернул статус {response.status_code} для алерта {alert_data["type"]}'
                )
            
        except Exception as e:
            logger.error(f'Ошибка при отправке webhook алерта: {str(e)}')
    
    def _format_alert_text(self, alert_data: Dict) -> str:
        """
        Форматирует алерт в текстовом виде
        """
        alert_type = alert_data['type']
        severity = alert_data['severity']
        timestamp = alert_data['timestamp']
        
        text = f"🚨 АЛЕРТ БЕЗОПАСНОСТИ\n\n"
        text += f"Тип: {alert_type}\n"
        text += f"Серьезность: {severity}\n"
        text += f"Время: {timestamp}\n\n"
        
        if alert_type == 'mass_registration':
            text += f"Обнаружены массовые регистрации:\n"
            text += f"- Порог: {alert_data['threshold']} регистраций за {alert_data['window_minutes']} минут\n"
            text += f"- Всего регистраций: {alert_data['total_registrations']}\n"
            text += f"- Подозрительных IP: {len(alert_data['detected_ips'])}\n"
        
        elif alert_type == 'suspicious_activity':
            text += f"Обнаружена подозрительная активность:\n"
            text += f"- Высокорисковых отчетов: {alert_data['high_risk_reports']}\n"
            text += f"- Подозрительных IP: {len(alert_data['suspicious_ips'])}\n"
        
        elif alert_type == 'automation_attack':
            text += f"Обнаружена атака автоматизации:\n"
            text += f"- Отчетов с автоматизацией: {alert_data['automation_reports']}\n"
            text += f"- Источников атаки: {len(alert_data['sources'])}\n"
        
        elif alert_type == 'threat_pattern':
            text += f"Обнаружены паттерны угроз:\n"
            text += f"- Всего угроз: {alert_data['total_threats']}\n"
            text += f"- Типов угроз: {len(alert_data['threat_types'])}\n"
        
        text += f"\nПроверьте панель администратора для получения подробной информации."
        
        return text
    
    def get_monitoring_stats(self) -> Dict:
        """
        Получает статистику мониторинга
        """
        try:
            # Статистика за последние 24 часа
            twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
            
            stats = {
                'period': '24 часа',
                'total_reports': SecurityReport.objects.filter(
                    created_at__gte=twenty_four_hours_ago
                ).count(),
                'total_threats': ThreatDetection.objects.filter(
                    detected_at__gte=twenty_four_hours_ago
                ).count(),
                'high_risk_reports': SecurityReport.objects.filter(
                    created_at__gte=twenty_four_hours_ago,
                    overall_risk_score__gte=self.high_risk_threshold
                ).count(),
                'automation_detected': SecurityReport.objects.filter(
                    created_at__gte=twenty_four_hours_ago,
                    device_fingerprint_data__contains='"automation_detected": true'
                ).count(),
                'unique_ips': SecurityReport.objects.filter(
                    created_at__gte=twenty_four_hours_ago
                ).values('ip_address').distinct().count()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f'Ошибка при получении статистики мониторинга: {str(e)}')
            return {}


# Глобальный экземпляр сервиса
monitoring_service = SecurityMonitoringService()