from django.utils import timezone
from django.db import transaction, models
from typing import Dict, Any, List, Optional
import logging
import json
import statistics

from ..models import BehavioralAnalysis, SecurityReport

logger = logging.getLogger(__name__)


class BehavioralAnalysisService:
    """
    Сервис для анализа поведенческих паттернов пользователей
    """
    
    @staticmethod
    def create_analysis(session_id: str, ip_address: str, analysis_type: str = 'mouse_movement',
                       mouse_velocity_avg: float = None, typing_speed: float = None,
                       mouse_acceleration_avg: float = None, scroll_velocity_avg: float = None) -> BehavioralAnalysis:
        """
        Создает новый анализ поведения
        """
        try:
            with transaction.atomic():
                now = timezone.now()
                analysis = BehavioralAnalysis.objects.create(
                    session_id=session_id,
                    ip_address=ip_address,
                    analysis_type=analysis_type,
                    mouse_velocity_avg=mouse_velocity_avg,
                    typing_speed=typing_speed,
                    mouse_acceleration_avg=mouse_acceleration_avg,
                    scroll_velocity_avg=scroll_velocity_avg,
                    analysis_start=now,
                    analysis_end=now
                )
                
                logger.info(f"Создан анализ поведения для сессии {session_id}")
                return analysis
                
        except Exception as e:
            logger.error(f"Ошибка создания анализа поведения: {e}")
            raise
    
    @staticmethod
    def calculate_risk_score(analysis: BehavioralAnalysis) -> float:
        """
        Вычисляет риск-скор на основе поведенческих метрик
        """
        risk_score = 0.0
        
        # Анализ скорости мыши
        if analysis.mouse_velocity_avg > 1000:  # Слишком быстрые движения
            risk_score += 20.0
        elif analysis.mouse_velocity_avg < 10:  # Слишком медленные движения
            risk_score += 15.0
        
        # Анализ скорости печати
        if analysis.typing_speed > 200:  # Нечеловечески быстрая печать
            risk_score += 30.0
        elif analysis.typing_speed < 10:  # Слишком медленная печать
            risk_score += 10.0
        
        # Анализ частоты кликов
        if analysis.click_frequency > 10:  # Слишком частые клики
            risk_score += 25.0
        
        # Анализ скорости прокрутки
        if analysis.scroll_speed > 500:  # Слишком быстрая прокрутка
            risk_score += 15.0
        
        return min(risk_score, 100.0)  # Ограничиваем максимальным значением 100
    
    @staticmethod
    def get_analysis_by_session(session_id: str) -> Optional[BehavioralAnalysis]:
        """
        Получает анализ поведения по ID сессии
        """
        try:
            return BehavioralAnalysis.objects.filter(session_id=session_id).first()
        except Exception as e:
            logger.error(f"Ошибка получения анализа поведения: {e}")
            return None
    
    @staticmethod
    def get_suspicious_analyses(threshold: float = 50.0) -> List[BehavioralAnalysis]:
        """
        Получает подозрительные анализы поведения
        """
        analyses = BehavioralAnalysis.objects.all()
        suspicious = []
        
        for analysis in analyses:
            risk_score = BehavioralAnalysisService.calculate_risk_score(analysis)
            if risk_score >= threshold:
                suspicious.append(analysis)
        
        return suspicious
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """
        Получает статистику по анализам поведения
        """
        from django.db.models import Count, Avg, Max
        
        stats = BehavioralAnalysis.objects.aggregate(
            total_analyses=Count('id'),
            avg_mouse_velocity=Avg('mouse_velocity_avg'),
            avg_typing_speed=Avg('typing_speed'),
            avg_click_frequency=Avg('click_frequency'),
            max_mouse_velocity=Max('mouse_velocity_avg'),
            max_typing_speed=Max('typing_speed')
        )
        
        return stats
    
    @staticmethod
    def cleanup_old_analyses(days: int = 30) -> int:
        """
        Удаляет старые анализы поведения
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        deleted_count, _ = BehavioralAnalysis.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Удалено {deleted_count} старых анализов поведения")
        return deleted_count
    
    @staticmethod
    def cleanup_old_analyses(days: int = 30) -> int:
        """
        Удаляет старые анализы поведения
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        deleted_count, _ = BehavioralAnalysis.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Удалено {deleted_count} старых анализов поведения")
        return deleted_count
    
    @staticmethod
    def get_behavioral_statistics() -> Dict[str, Any]:
        """
        Получает статистику поведенческого анализа
        """
        from django.db.models import Count, Avg, Max, Min
        
        stats = BehavioralAnalysis.objects.aggregate(
            total_analyses=Count('id'),
            high_risk_count=Count('id', filter=models.Q(overall_risk_score__gte=70)),
            avg_risk_score=Avg('overall_risk_score'),
            max_risk_score=Max('overall_risk_score'),
            min_risk_score=Min('overall_risk_score')
        )
        
        # Распределение по уровням риска
        risk_distribution = {
            'low': BehavioralAnalysis.objects.filter(overall_risk_score__lt=30).count(),
            'medium': BehavioralAnalysis.objects.filter(overall_risk_score__gte=30, overall_risk_score__lt=70).count(),
            'high': BehavioralAnalysis.objects.filter(overall_risk_score__gte=70).count()
        }
        
        stats['risk_distribution'] = risk_distribution
        
        return stats