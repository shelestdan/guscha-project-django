from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    SecurityReport,
    ThreatDetection,
    SecurityBlacklist,
    DeviceFingerprint,
    BehavioralAnalysis
)
from .services.threat_analysis_service import ThreatAnalysisService
from .services.monitoring_service import SecurityMonitoringService
from .settings import get_security_setting, is_security_enabled

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SecurityReport)
def handle_security_report_created(sender, instance, created, **kwargs):
    """
    Обработка создания нового отчета о безопасности
    """
    if not created or not is_security_enabled():
        return
    
    try:
        # Автоматический анализ угроз для новых отчетов
        if get_security_setting('SECURITY_AUTO_THREAT_ANALYSIS', True):
            threat_service = ThreatAnalysisService()
            threat_service.analyze_report(instance)
        
        # Проверка на массовые атаки
        if get_security_setting('SECURITY_MASS_ATTACK_DETECTION', True):
            _check_mass_attack(instance)
        
        # Обновление статистики в кэше
        _update_security_stats_cache()
        
        logger.info(f"Security report {instance.id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing security report {instance.id}: {e}")


@receiver(post_save, sender=ThreatDetection)
def handle_threat_detection_created(sender, instance, created, **kwargs):
    """
    Обработка создания нового обнаружения угрозы
    """
    if not created or not is_security_enabled():
        return
    
    try:
        # Автоматическое добавление в черный список для критических угроз
        if (instance.risk_score >= get_security_setting('SECURITY_AUTO_BLACKLIST_THRESHOLD', 80) and
            get_security_setting('SECURITY_AUTO_BLACKLIST_ENABLED', True)):
            _auto_blacklist_threat(instance)
        
        # Отправка уведомлений для высокорисковых угроз
        if (instance.risk_score >= get_security_setting('SECURITY_ALERT_THRESHOLD', 70) and
            get_security_setting('SECURITY_NOTIFICATIONS_ENABLED', False)):
            _send_threat_notification(instance)
        
        # Запуск дополнительного мониторинга
        if instance.risk_score >= get_security_setting('SECURITY_ENHANCED_MONITORING_THRESHOLD', 60):
            _trigger_enhanced_monitoring(instance)
        
        logger.info(f"Threat detection {instance.id} processed, risk score: {instance.risk_score}")
        
    except Exception as e:
        logger.error(f"Error processing threat detection {instance.id}: {e}")


@receiver(post_save, sender=SecurityBlacklist)
def handle_blacklist_updated(sender, instance, created, **kwargs):
    """
    Обработка обновления черного списка
    """
    if not is_security_enabled():
        return
    
    try:
        # Очистка кэша при изменении черного списка
        cache_key = f"blacklist_{instance.blacklist_type}_{instance.value}"
        cache.delete(cache_key)
        
        # Очистка общего кэша черного списка
        cache.delete('security_blacklist_all')
        cache.delete(f'security_blacklist_{instance.blacklist_type}')
        
        # Логирование изменений
        action = "added to" if created else "updated in"
        logger.info(f"{instance.blacklist_type} '{instance.value}' {action} blacklist")
        
        # Уведомление о критических добавлениях
        if created and instance.blacklist_type in ['ip', 'user_agent']:
            _notify_blacklist_addition(instance)
        
    except Exception as e:
        logger.error(f"Error processing blacklist update for {instance.id}: {e}")


@receiver(pre_delete, sender=SecurityBlacklist)
def handle_blacklist_deletion(sender, instance, **kwargs):
    """
    Обработка удаления из черного списка
    """
    if not is_security_enabled():
        return
    
    try:
        # Логирование удаления
        logger.info(f"{instance.blacklist_type} '{instance.value}' removed from blacklist")
        
        # Очистка кэша
        cache_key = f"blacklist_{instance.blacklist_type}_{instance.value}"
        cache.delete(cache_key)
        
    except Exception as e:
        logger.error(f"Error processing blacklist deletion for {instance.id}: {e}")


@receiver(post_delete, sender=SecurityBlacklist)
def handle_blacklist_deleted(sender, instance, **kwargs):
    """
    Обработка после удаления из черного списка
    """
    if not is_security_enabled():
        return
    
    try:
        # Очистка общего кэша черного списка
        cache.delete('security_blacklist_all')
        cache.delete(f'security_blacklist_{instance.blacklist_type}')
        
    except Exception as e:
        logger.error(f"Error in post-delete processing for blacklist {instance.id}: {e}")


@receiver(post_save, sender=DeviceFingerprint)
def handle_device_fingerprint_updated(sender, instance, created, **kwargs):
    """
    Обработка обновления отпечатка устройства
    """
    if not is_security_enabled():
        return
    
    try:
        # Проверка на подозрительные устройства
        if created and get_security_setting('SECURITY_DEVICE_ANALYSIS_ENABLED', True):
            _analyze_device_fingerprint(instance)
        
        # Обновление кэша устройств
        cache_key = f"device_fingerprint_{instance.fingerprint_hash}"
        cache.set(cache_key, instance, timeout=3600)  # 1 час
        
        logger.debug(f"Device fingerprint {instance.fingerprint_hash} processed")
        
    except Exception as e:
        logger.error(f"Error processing device fingerprint {instance.id}: {e}")


@receiver(post_save, sender=BehavioralAnalysis)
def handle_behavioral_analysis_updated(sender, instance, created, **kwargs):
    """
    Обработка обновления поведенческого анализа
    """
    if not is_security_enabled():
        return
    
    try:
        # Проверка на аномальное поведение
        if get_security_setting('SECURITY_BEHAVIORAL_ANOMALY_DETECTION', True):
            _check_behavioral_anomalies(instance)
        
        # Обновление профиля пользователя
        if instance.session_key:
            cache_key = f"behavioral_profile_{instance.session_key}"
            cache.set(cache_key, instance, timeout=1800)  # 30 минут
        
        logger.debug(f"Behavioral analysis {instance.id} processed")
        
    except Exception as e:
        logger.error(f"Error processing behavioral analysis {instance.id}: {e}")


@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    """
    Обработка успешного входа пользователя
    """
    if not is_security_enabled():
        return
    
    try:
        # Проверка на подозрительный вход
        if get_security_setting('SECURITY_LOGIN_MONITORING', True):
            _monitor_user_login(request, user)
        
        # Очистка счетчиков неудачных попыток
        ip_address = _get_client_ip(request)
        if ip_address:
            cache.delete(f"failed_login_attempts_{ip_address}")
            cache.delete(f"failed_login_attempts_{user.username}")
        
        logger.info(f"User {user.username} logged in successfully from {ip_address}")
        
    except Exception as e:
        logger.error(f"Error processing user login for {user.username}: {e}")


@receiver(user_login_failed)
def handle_user_login_failed(sender, credentials, request, **kwargs):
    """
    Обработка неудачной попытки входа
    """
    if not is_security_enabled():
        return
    
    try:
        # Увеличение счетчика неудачных попыток
        ip_address = _get_client_ip(request)
        username = credentials.get('username', 'unknown')
        
        if ip_address:
            _increment_failed_attempts(ip_address, username)
        
        # Проверка на брутфорс атаку
        if get_security_setting('SECURITY_BRUTE_FORCE_DETECTION', True):
            _check_brute_force_attack(ip_address, username)
        
        logger.warning(f"Failed login attempt for {username} from {ip_address}")
        
    except Exception as e:
        logger.error(f"Error processing failed login: {e}")


# Вспомогательные функции

def _check_mass_attack(security_report):
    """
    Проверка на массовую атаку
    """
    try:
        # Подсчет отчетов за последние 5 минут с того же IP
        time_threshold = timezone.now() - timedelta(minutes=5)
        recent_reports = SecurityReport.objects.filter(
            ip_address=security_report.ip_address,
            created_at__gte=time_threshold
        ).count()
        
        threshold = get_security_setting('SECURITY_MASS_ATTACK_THRESHOLD', 10)
        if recent_reports >= threshold:
            # Создание угрозы массовой атаки
            ThreatDetection.objects.create(
                security_report=security_report,
                threat_type='mass_attack',
                risk_score=85,
                description=f'Mass attack detected: {recent_reports} reports in 5 minutes',
                metadata={'report_count': recent_reports, 'time_window': 5}
            )
            
            logger.warning(f"Mass attack detected from {security_report.ip_address}")
    
    except Exception as e:
        logger.error(f"Error checking mass attack: {e}")


def _auto_blacklist_threat(threat_detection):
    """
    Автоматическое добавление в черный список
    """
    try:
        security_report = threat_detection.security_report
        
        # Добавление IP в черный список
        if security_report.ip_address:
            SecurityBlacklist.objects.get_or_create(
                blacklist_type='ip',
                value=security_report.ip_address,
                defaults={
                    'reason': f'Auto-blacklisted due to threat {threat_detection.id}',
                    'expires_at': timezone.now() + timedelta(
                        hours=get_security_setting('SECURITY_AUTO_BLACKLIST_DURATION_HOURS', 24)
                    )
                }
            )
        
        # Добавление отпечатка устройства в черный список
        if security_report.device_fingerprint:
            SecurityBlacklist.objects.get_or_create(
                blacklist_type='fingerprint',
                value=security_report.device_fingerprint,
                defaults={
                    'reason': f'Auto-blacklisted due to threat {threat_detection.id}',
                    'expires_at': timezone.now() + timedelta(
                        hours=get_security_setting('SECURITY_AUTO_BLACKLIST_DURATION_HOURS', 24)
                    )
                }
            )
        
        logger.info(f"Auto-blacklisted threat {threat_detection.id}")
    
    except Exception as e:
        logger.error(f"Error auto-blacklisting threat {threat_detection.id}: {e}")


def _send_threat_notification(threat_detection):
    """
    Отправка уведомления об угрозе
    """
    try:
        from .services.monitoring_service import SecurityMonitoringService
        monitoring_service = SecurityMonitoringService()
        
        alert_data = {
            'type': 'threat_detection',
            'threat_id': threat_detection.id,
            'threat_type': threat_detection.threat_type,
            'risk_score': threat_detection.risk_score,
            'ip_address': threat_detection.security_report.ip_address,
            'timestamp': threat_detection.created_at.isoformat()
        }
        
        monitoring_service.send_alert(alert_data)
        
    except Exception as e:
        logger.error(f"Error sending threat notification: {e}")


def _trigger_enhanced_monitoring(threat_detection):
    """
    Запуск усиленного мониторинга
    """
    try:
        # Увеличение частоты мониторинга для данного IP
        ip_address = threat_detection.security_report.ip_address
        if ip_address:
            cache_key = f"enhanced_monitoring_{ip_address}"
            cache.set(cache_key, True, timeout=3600)  # 1 час усиленного мониторинга
        
        logger.info(f"Enhanced monitoring triggered for threat {threat_detection.id}")
    
    except Exception as e:
        logger.error(f"Error triggering enhanced monitoring: {e}")


def _notify_blacklist_addition(blacklist_entry):
    """
    Уведомление о добавлении в черный список
    """
    try:
        if get_security_setting('SECURITY_BLACKLIST_NOTIFICATIONS', True):
            logger.info(f"Critical blacklist addition: {blacklist_entry.blacklist_type} - {blacklist_entry.value}")
    
    except Exception as e:
        logger.error(f"Error sending blacklist notification: {e}")


def _analyze_device_fingerprint(device_fingerprint):
    """
    Анализ отпечатка устройства на подозрительность
    """
    try:
        # Проверка на известные боты/автоматизацию
        suspicious_indicators = [
            'headless', 'phantom', 'selenium', 'webdriver',
            'bot', 'crawler', 'spider'
        ]
        
        fingerprint_data = device_fingerprint.fingerprint_data
        if any(indicator in str(fingerprint_data).lower() for indicator in suspicious_indicators):
            # Создание отчета о подозрительном устройстве
            SecurityReport.objects.create(
                ip_address=device_fingerprint.ip_address,
                user_agent=fingerprint_data.get('user_agent', ''),
                device_fingerprint=device_fingerprint.fingerprint_hash,
                report_type='suspicious_device',
                risk_score=60,
                metadata={'analysis': 'Suspicious device fingerprint detected'}
            )
    
    except Exception as e:
        logger.error(f"Error analyzing device fingerprint: {e}")


def _check_behavioral_anomalies(behavioral_analysis):
    """
    Проверка поведенческих аномалий
    """
    try:
        # Проверка на слишком быстрые действия
        if behavioral_analysis.events_per_minute > get_security_setting('SECURITY_MAX_EVENTS_PER_MINUTE', 60):
            SecurityReport.objects.create(
                ip_address=behavioral_analysis.ip_address,
                report_type='behavioral_anomaly',
                risk_score=50,
                metadata={
                    'anomaly_type': 'high_event_rate',
                    'events_per_minute': behavioral_analysis.events_per_minute
                }
            )
    
    except Exception as e:
        logger.error(f"Error checking behavioral anomalies: {e}")


def _monitor_user_login(request, user):
    """
    Мониторинг входа пользователя
    """
    try:
        ip_address = _get_client_ip(request)
        
        # Проверка на вход с нового IP
        cache_key = f"user_known_ips_{user.id}"
        known_ips = cache.get(cache_key, set())
        
        if ip_address and ip_address not in known_ips:
            # Новый IP для пользователя
            logger.info(f"User {user.username} logged in from new IP: {ip_address}")
            
            # Добавляем IP в известные
            known_ips.add(ip_address)
            cache.set(cache_key, known_ips, timeout=86400 * 30)  # 30 дней
    
    except Exception as e:
        logger.error(f"Error monitoring user login: {e}")


def _increment_failed_attempts(ip_address, username):
    """
    Увеличение счетчика неудачных попыток
    """
    try:
        # Счетчик по IP
        ip_key = f"failed_login_attempts_{ip_address}"
        ip_attempts = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_attempts, timeout=3600)  # 1 час
        
        # Счетчик по пользователю
        user_key = f"failed_login_attempts_{username}"
        user_attempts = cache.get(user_key, 0) + 1
        cache.set(user_key, user_attempts, timeout=3600)  # 1 час
    
    except Exception as e:
        logger.error(f"Error incrementing failed attempts: {e}")


def _check_brute_force_attack(ip_address, username):
    """
    Проверка на брутфорс атаку
    """
    try:
        threshold = get_security_setting('SECURITY_BRUTE_FORCE_THRESHOLD', 5)
        
        # Проверка по IP
        ip_key = f"failed_login_attempts_{ip_address}"
        ip_attempts = cache.get(ip_key, 0)
        
        if ip_attempts >= threshold:
            # Брутфорс с IP
            SecurityReport.objects.create(
                ip_address=ip_address,
                report_type='brute_force_attack',
                risk_score=75,
                metadata={
                    'attack_type': 'ip_based',
                    'failed_attempts': ip_attempts,
                    'target_username': username
                }
            )
            
            logger.warning(f"Brute force attack detected from IP {ip_address}")
    
    except Exception as e:
        logger.error(f"Error checking brute force attack: {e}")


def _update_security_stats_cache():
    """
    Обновление статистики безопасности в кэше
    """
    try:
        # Обновляем счетчики
        cache.delete('security_stats_today')
        cache.delete('security_stats_week')
        cache.delete('security_stats_month')
    
    except Exception as e:
        logger.error(f"Error updating security stats cache: {e}")


def _get_client_ip(request):
    """
    Получение IP адреса клиента
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip