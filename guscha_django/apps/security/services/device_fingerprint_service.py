from django.utils import timezone
from django.db import transaction
from typing import Dict, Any, List, Optional
import logging
import hashlib
import json

from ..models import DeviceFingerprint, SecurityReport

logger = logging.getLogger(__name__)


class DeviceFingerprintService:
    """
    Сервис для работы с отпечатками устройств
    """
    
    @staticmethod
    def generate_fingerprint(user_agent: str, screen_resolution: str = None,
                           timezone_offset: int = None, language: str = None,
                           platform: str = None, plugins: List[str] = None) -> str:
        """
        Генерирует уникальный отпечаток устройства
        """
        fingerprint_data = {
            'user_agent': user_agent,
            'screen_resolution': screen_resolution or '',
            'timezone_offset': timezone_offset or 0,
            'language': language or '',
            'platform': platform or '',
            'plugins': sorted(plugins or [])
        }
        
        # Создаем хеш из данных устройства
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint_hash = hashlib.sha256(fingerprint_string.encode()).hexdigest()
        
        return fingerprint_hash
    
    @staticmethod
    def create_or_update_fingerprint(fingerprint_data: Dict[str, Any]) -> DeviceFingerprint:
        """
        Создает или обновляет отпечаток устройства
        """
        try:
            with transaction.atomic():
                # Генерируем хеш отпечатка
                fingerprint_hash = DeviceFingerprintService.generate_fingerprint(
                    user_agent=fingerprint_data.get('user_agent', ''),
                    screen_resolution=fingerprint_data.get('screen_resolution'),
                    timezone_offset=fingerprint_data.get('timezone_offset'),
                    language=fingerprint_data.get('language'),
                    platform=fingerprint_data.get('platform'),
                    plugins=fingerprint_data.get('plugins')
                )
                
                fingerprint, created = DeviceFingerprint.objects.get_or_create(
                    fingerprint_hash=fingerprint_hash,
                    defaults={
                        'user_agent': fingerprint_data.get('user_agent', ''),
                        'screen_resolution': fingerprint_data.get('screen_resolution', ''),
                        'timezone_offset': fingerprint_data.get('timezone_offset', 0),
                        'language': fingerprint_data.get('language', ''),
                        'platform': fingerprint_data.get('platform', ''),
                        'usage_count': 1
                    }
                )
                
                if not created:
                    # Обновляем существующий отпечаток
                    fingerprint.usage_count += 1
                    fingerprint.last_seen = timezone.now()
                    fingerprint.save()
                
                logger.info(f"Отпечаток устройства {'создан' if created else 'обновлен'}: {fingerprint_hash[:8]}...")
                return fingerprint
                
        except Exception as e:
            logger.error(f"Ошибка создания/обновления отпечатка устройства: {e}")
            raise
    
    @staticmethod
    def analyze_fingerprint_risk(fingerprint: DeviceFingerprint) -> Dict[str, Any]:
        """
        Анализирует риски отпечатка устройства
        """
        risk_factors = []
        risk_score = 0
        
        # Проверка на подозрительный User Agent
        ua_lower = fingerprint.user_agent.lower()
        if any(bot_pattern in ua_lower for bot_pattern in ['bot', 'crawler', 'spider', 'scraper']):
            risk_factors.append('Подозрительный User Agent (бот)')
            risk_score += 40
        
        # Проверка частоты использования
        if fingerprint.usage_count > 100:
            risk_factors.append(f'Высокая частота использования ({fingerprint.usage_count})')
            risk_score += 30
        
        # Проверка на отсутствие важных данных
        if not fingerprint.screen_resolution:
            risk_factors.append('Отсутствует разрешение экрана')
            risk_score += 10
        
        if not fingerprint.language:
            risk_factors.append('Отсутствует информация о языке')
            risk_score += 10
        
        # Проверка на подозрительные плагины
        if fingerprint.plugins:
            suspicious_plugins = ['headless', 'automation', 'webdriver']
            for plugin in fingerprint.plugins:
                if any(sus in plugin.lower() for sus in suspicious_plugins):
                    risk_factors.append(f'Подозрительный плагин: {plugin}')
                    risk_score += 20
                    break
        
        # Проверка времени между первым и последним использованием
        if fingerprint.last_seen and fingerprint.first_seen:
            time_diff = fingerprint.last_seen - fingerprint.first_seen
            if time_diff.total_seconds() < 60 and fingerprint.usage_count > 10:
                risk_factors.append('Слишком частое использование за короткий период')
                risk_score += 25
        
        # Ограничиваем максимальный риск
        risk_score = min(risk_score, 100)
        
        return {
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'is_suspicious': risk_score > 50,
            'recommendation': DeviceFingerprintService._get_risk_recommendation(risk_score)
        }
    
    @staticmethod
    def _get_risk_recommendation(risk_score: int) -> str:
        """
        Возвращает рекомендацию на основе уровня риска
        """
        if risk_score >= 80:
            return 'Заблокировать устройство'
        elif risk_score >= 60:
            return 'Требуется дополнительная проверка'
        elif risk_score >= 40:
            return 'Усиленный мониторинг'
        else:
            return 'Нормальная активность'
    
    @staticmethod
    def mark_as_suspicious(fingerprint_hash: str, reason: str = None) -> bool:
        """
        Помечает отпечаток как подозрительный
        """
        try:
            fingerprint = DeviceFingerprint.objects.get(fingerprint_hash=fingerprint_hash)
            fingerprint.is_suspicious = True
            fingerprint.save()
            
            logger.warning(f"Отпечаток {fingerprint_hash[:8]}... помечен как подозрительный: {reason}")
            return True
            
        except DeviceFingerprint.DoesNotExist:
            logger.error(f"Отпечаток {fingerprint_hash} не найден")
            return False
        except Exception as e:
            logger.error(f"Ошибка при пометке отпечатка как подозрительного: {e}")
            return False
    
    @staticmethod
    def get_suspicious_fingerprints() -> List[DeviceFingerprint]:
        """
        Получает список подозрительных отпечатков
        """
        return DeviceFingerprint.objects.filter(
            is_suspicious=True
        ).order_by('-last_seen')
    
    @staticmethod
    def cleanup_old_fingerprints(days: int = 90) -> int:
        """
        Удаляет старые отпечатки устройств
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        deleted_count, _ = DeviceFingerprint.objects.filter(
            last_seen__lt=cutoff_date,
            is_suspicious=False  # Не удаляем подозрительные
        ).delete()
        
        logger.info(f"Удалено {deleted_count} старых отпечатков устройств")
        return deleted_count
    
    @staticmethod
    def get_fingerprint_statistics() -> Dict[str, Any]:
        """
        Получает статистику по отпечаткам устройств
        """
        from django.db.models import Count, Avg, Max
        
        from django.db import models
        
        stats = DeviceFingerprint.objects.aggregate(
            total_fingerprints=Count('id'),
            suspicious_count=Count('id', filter=models.Q(is_suspicious=True)),
            avg_usage=Avg('usage_count'),
            max_usage=Max('usage_count')
        )
        
        # Топ User Agents
        top_user_agents = DeviceFingerprint.objects.values('user_agent').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        stats['top_user_agents'] = list(top_user_agents)
        
        return stats