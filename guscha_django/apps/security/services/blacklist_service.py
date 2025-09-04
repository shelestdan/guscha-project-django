from django.utils import timezone
from django.db import transaction
from typing import Dict, Any, List, Optional
import logging
import ipaddress

from ..models import SecurityBlacklist, SecurityReport

logger = logging.getLogger(__name__)


class BlacklistService:
    """
    Сервис для управления черными списками
    """
    
    @staticmethod
    def add_to_blacklist(value: str, blacklist_type: str, 
                        reason: str = None, expires_at: timezone.datetime = None) -> SecurityBlacklist:
        """
        Добавляет значение в черный список
        """
        try:
            with transaction.atomic():
                # Проверяем, не существует ли уже такая запись
                existing = SecurityBlacklist.objects.filter(
                    value=value,
                    blacklist_type=blacklist_type,
                    is_active=True
                ).first()
                
                if existing:
                    logger.info(f"Значение {value} уже в черном списке")
                    return existing
                
                blacklist_entry = SecurityBlacklist.objects.create(
                    value=value,
                    blacklist_type=blacklist_type,
                    reason=reason or f"Автоматически добавлено: {blacklist_type}",
                    expires_at=expires_at
                )
                
                logger.info(f"Добавлено в черный список: {value} ({blacklist_type})")
                return blacklist_entry
                
        except Exception as e:
            logger.error(f"Ошибка добавления в черный список {value}: {e}")
            raise
    
    @staticmethod
    def is_blacklisted(value: str, blacklist_type: str = None) -> bool:
        """
        Проверяет, находится ли значение в черном списке
        """
        query = SecurityBlacklist.objects.filter(
            value=value,
            is_active=True
        )
        
        if blacklist_type:
            query = query.filter(blacklist_type=blacklist_type)
        
        # Проверяем срок действия
        from django.db import models
        now = timezone.now()
        query = query.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )
        
        return query.exists()
    
    @staticmethod
    def check_ip_blacklist(ip_address: str) -> bool:
        """
        Проверяет IP адрес в черном списке
        """
        # Прямая проверка IP
        if BlacklistService.is_blacklisted(ip_address, 'ip_address'):
            return True
        
        # Проверка подсетей
        try:
            ip = ipaddress.ip_address(ip_address)
            subnets = SecurityBlacklist.objects.filter(
                blacklist_type='ip_subnet',
                is_active=True
            )
            
            for subnet_entry in subnets:
                try:
                    subnet = ipaddress.ip_network(subnet_entry.value, strict=False)
                    if ip in subnet:
                        return True
                except ValueError:
                    continue
                    
        except ValueError:
            logger.warning(f"Некорректный IP адрес: {ip_address}")
        
        return False
    
    @staticmethod
    def auto_blacklist_suspicious_ip(ip_address: str) -> Optional[SecurityBlacklist]:
        """
        Автоматически добавляет подозрительный IP в черный список
        """
        # Анализируем активность IP за последние 24 часа
        day_ago = timezone.now() - timezone.timedelta(days=1)
        reports = SecurityReport.objects.filter(
            ip_address=ip_address,
            created_at__gte=day_ago
        )
        
        report_count = reports.count()
        high_risk_count = reports.filter(overall_risk_score__gte=70).count()
        
        # Критерии для автоматического добавления в черный список
        should_blacklist = (
            report_count > 100 or  # Более 100 запросов за день
            high_risk_count > 10 or  # Более 10 высокорисковых событий
            (report_count > 50 and high_risk_count > 5)  # Комбинированный критерий
        )
        
        if should_blacklist:
            reason = f"Автоблокировка: {report_count} запросов, {high_risk_count} высокорисковых"
            expires_at = timezone.now() + timezone.timedelta(hours=24)  # Блокировка на 24 часа
            
            return BlacklistService.add_to_blacklist(
                value=ip_address,
                blacklist_type='ip_address',
                reason=reason,
                expires_at=expires_at
            )
        
        return None
    
    @staticmethod
    def remove_from_blacklist(value: str, blacklist_type: str = None) -> bool:
        """
        Удаляет значение из черного списка
        """
        try:
            query = SecurityBlacklist.objects.filter(
                value=value,
                is_active=True
            )
            
            if blacklist_type:
                query = query.filter(blacklist_type=blacklist_type)
            
            updated = query.update(is_active=False)
            
            if updated:
                logger.info(f"Удалено из черного списка: {value}")
                return True
            else:
                logger.warning(f"Значение не найдено в черном списке: {value}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка удаления из черного списка {value}: {e}")
            return False
    
    @staticmethod
    def cleanup_expired_entries() -> int:
        """
        Удаляет истекшие записи из черного списка
        """
        now = timezone.now()
        expired_count = SecurityBlacklist.objects.filter(
            expires_at__lt=now,
            is_active=True
        ).update(is_active=False)
        
        logger.info(f"Деактивировано {expired_count} истекших записей черного списка")
        return expired_count
    
    @staticmethod
    def get_blacklist_stats() -> Dict[str, Any]:
        """
        Получает статистику черного списка
        """
        from django.db.models import Count
        
        from django.db import models
        
        stats = SecurityBlacklist.objects.filter(is_active=True).aggregate(
            total_entries=Count('id'),
            ip_entries=Count('id', filter=models.Q(blacklist_type='ip_address')),
            subnet_entries=Count('id', filter=models.Q(blacklist_type='ip_subnet')),
            user_agent_entries=Count('id', filter=models.Q(blacklist_type='user_agent'))
        )
        
        # Записи с истекающим сроком (в течение 24 часов)
        expiring_soon = SecurityBlacklist.objects.filter(
            is_active=True,
            expires_at__lte=timezone.now() + timezone.timedelta(hours=24),
            expires_at__gt=timezone.now()
        ).count()
        
        stats['expiring_soon'] = expiring_soon
        
        return stats