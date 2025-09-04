from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from typing import Dict, Any, Optional, List
import logging
import json

from ..models import SecurityReport, ThreatDetection

logger = logging.getLogger(__name__)


class SecurityReportService:
    """
    Сервис для работы с отчетами безопасности
    """
    
    @staticmethod
    def create_report(session_id: str, ip_address: str, user_agent: str, 
                     fingerprint_hash: str = None, risk_level: str = 'low',
                     overall_risk_score: int = 0, raw_data: Dict[str, Any] = None) -> SecurityReport:
        """
        Создает новый отчет о безопасности
        """
        try:
            with transaction.atomic():
                report = SecurityReport.objects.create(
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    fingerprint_hash=fingerprint_hash,
                    risk_level=risk_level,
                    overall_risk_score=overall_risk_score,
                    raw_data=raw_data or {}
                )
                
                logger.info(f"Создан отчет безопасности {report.id} для IP {ip_address}")
                return report
                
        except Exception as e:
            logger.error(f"Ошибка создания отчета безопасности: {e}")
            raise
    
    @staticmethod
    def get_reports_by_ip(ip_address: str, hours: int = 24) -> List[SecurityReport]:
        """
        Получает отчеты по IP адресу за указанный период
        """
        since = timezone.now() - timezone.timedelta(hours=hours)
        return SecurityReport.objects.filter(
            ip_address=ip_address,
            created_at__gte=since
        ).order_by('-created_at')
    
    @staticmethod
    def get_high_risk_reports(risk_threshold: int = 70) -> List[SecurityReport]:
        """
        Получает отчеты с высоким уровнем риска
        """
        return SecurityReport.objects.filter(
            overall_risk_score__gte=risk_threshold
        ).order_by('-overall_risk_score', '-created_at')
    
    @staticmethod
    def analyze_ip_activity(ip_address: str) -> Dict[str, Any]:
        """
        Анализирует активность IP адреса
        """
        reports = SecurityReportService.get_reports_by_ip(ip_address, hours=24)
        
        if not reports:
            return {
                'total_reports': 0,
                'avg_risk_score': 0,
                'max_risk_score': 0,
                'risk_levels': [],
                'is_suspicious': False
            }
        
        risk_scores = [r.overall_risk_score for r in reports]
        risk_levels = list(set(r.risk_level for r in reports))
        
        analysis = {
            'total_reports': len(reports),
            'avg_risk_score': sum(risk_scores) / len(risk_scores),
            'max_risk_score': max(risk_scores),
            'risk_levels': risk_levels,
            'is_suspicious': len(reports) > 10 or max(risk_scores) > 80
        }
        
        return analysis
    
    @staticmethod
    def cleanup_old_reports(days: int = 30) -> int:
        """
        Удаляет старые отчеты
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        deleted_count, _ = SecurityReport.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Удалено {deleted_count} старых отчетов безопасности")
        return deleted_count