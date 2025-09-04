from django.utils import timezone
from django.db import transaction
from typing import Dict, Any, List, Optional
import logging
import re

from ..models import SecurityReport, ThreatDetection, SecurityBlacklist

logger = logging.getLogger(__name__)


class ThreatAnalysisService:
    """
    Сервис для анализа угроз безопасности
    """
    
    # Паттерны для обнаружения угроз
    THREAT_PATTERNS = {
        'bot_activity': [
            r'bot|crawler|spider|scraper',
            r'automated|script|headless'
        ],
        'brute_force': [
            r'multiple.*failed.*login',
            r'rapid.*authentication.*attempts'
        ],
        'suspicious_pattern': [
            r'sql.*injection',
            r'xss|cross.*site.*scripting',
            r'path.*traversal'
        ]
    }
    
    @staticmethod
    def analyze_security_report(report: SecurityReport) -> List[ThreatDetection]:
        """
        Анализирует отчет безопасности и создает записи об угрозах
        """
        threats = []
        
        try:
            # Анализ User Agent
            ua_threats = ThreatAnalysisService._analyze_user_agent(report)
            threats.extend(ua_threats)
            
            # Анализ поведенческих паттернов
            behavioral_threats = ThreatAnalysisService._analyze_behavioral_patterns(report)
            threats.extend(behavioral_threats)
            
            # Анализ частоты запросов
            frequency_threats = ThreatAnalysisService._analyze_request_frequency(report)
            threats.extend(frequency_threats)
            
            # Сохранение обнаруженных угроз
            with transaction.atomic():
                for threat_data in threats:
                    ThreatDetection.objects.create(
                        security_report=report,
                        **threat_data
                    )
            
            logger.info(f"Обнаружено {len(threats)} угроз для отчета {report.id}")
            
        except Exception as e:
            logger.error(f"Ошибка анализа угроз для отчета {report.id}: {e}")
        
        return threats
    
    @staticmethod
    def _analyze_user_agent(report: SecurityReport) -> List[Dict[str, Any]]:
        """
        Анализирует User Agent на предмет угроз
        """
        threats = []
        user_agent = report.user_agent.lower()
        
        for threat_type, patterns in ThreatAnalysisService.THREAT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_agent, re.IGNORECASE):
                    threats.append({
                        'threat_type': threat_type,
                        'risk_score': 60,
                        'description': f'Обнаружен подозрительный User Agent: {pattern}'
                    })
                    break
        
        return threats
    
    @staticmethod
    def _analyze_behavioral_patterns(report: SecurityReport) -> List[Dict[str, Any]]:
        """
        Анализирует поведенческие паттерны
        """
        threats = []
        metadata = report.metadata or {}
        
        # Проверка на honeypot
        if metadata.get('honeypot_triggered'):
            threats.append({
                'threat_type': 'honeypot_trigger',
                'risk_score': 90,
                'description': 'Сработал honeypot - обнаружена автоматизация'
            })
        
        # Проверка времени заполнения формы
        form_time = metadata.get('form_fill_time', 0)
        if form_time < 2:  # Менее 2 секунд
            threats.append({
                'threat_type': 'automation_detected',
                'risk_score': 75,
                'description': f'Слишком быстрое заполнение формы: {form_time}с'
            })
        
        return threats
    
    @staticmethod
    def _analyze_request_frequency(report: SecurityReport) -> List[Dict[str, Any]]:
        """
        Анализирует частоту запросов с IP
        """
        threats = []
        
        # Получаем количество отчетов за последний час
        hour_ago = timezone.now() - timezone.timedelta(hours=1)
        recent_reports = SecurityReport.objects.filter(
            ip_address=report.ip_address,
            created_at__gte=hour_ago
        ).count()
        
        if recent_reports > 50:  # Более 50 запросов в час
            threats.append({
                'threat_type': 'mass_registration',
                'risk_score': 80,
                'description': f'Массовая активность: {recent_reports} запросов за час'
            })
        
        return threats
    
    @staticmethod
    def get_threat_statistics() -> Dict[str, Any]:
        """
        Получает статистику по угрозам
        """
        from django.db.models import Count, Avg
        
        from django.db import models
        
        stats = ThreatDetection.objects.aggregate(
            total_threats=Count('id'),
            avg_risk_score=Avg('risk_score'),
            resolved_count=Count('id', filter=models.Q(is_resolved=True))
        )
        
        # Статистика по типам угроз
        threat_types = ThreatDetection.objects.values('threat_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['threat_types'] = list(threat_types)
        
        return stats
    
    @staticmethod
    def resolve_threat(threat_id: int, resolved_by: str = None) -> bool:
        """
        Помечает угрозу как решенную
        """
        try:
            threat = ThreatDetection.objects.get(id=threat_id)
            threat.is_resolved = True
            threat.resolved_at = timezone.now()
            threat.save()
            
            logger.info(f"Угроза {threat_id} помечена как решенная")
            return True
            
        except ThreatDetection.DoesNotExist:
            logger.error(f"Угроза {threat_id} не найдена")
            return False
        except Exception as e:
            logger.error(f"Ошибка при решении угрозы {threat_id}: {e}")
            return False