import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Avg, Q
from ..models.security_report import SecurityReport, ThreatDetection, SecurityBlacklist

logger = logging.getLogger(__name__)


class SecurityAnalysisService:
    """
    Сервис для анализа данных безопасности и обнаружения угроз
    """
    
    # Пороговые значения для определения риска
    RISK_THRESHOLDS = {
        'fingerprint_confidence': {
            'low': 30,
            'medium': 60,
            'high': 80
        },
        'behavior_risk_score': {
            'low': 30,
            'medium': 60,
            'high': 80
        },
        'overall_risk_score': {
            'minimal': 20,
            'low': 40,
            'medium': 60,
            'high': 80
        },
        'suspicious_patterns': {
            'low': 2,
            'medium': 5,
            'high': 10
        }
    }
    
    # Веса для расчета общего риска
    RISK_WEIGHTS = {
        'automation_detected': 40,
        'behavior_risk': 30,
        'fingerprint_confidence': 15,
        'suspicious_patterns': 10,
        'interaction_count': 5
    }
    
    def __init__(self):
        self.cache_timeout = 300  # 5 минут
    
    def analyze_security_data(self, security_data: Dict) -> Dict:
        """
        Анализирует данные безопасности и возвращает результат анализа
        """
        try:
            logger.info(f"Analyzing security data for session: {security_data.get('sessionId')}")
            
            # Извлекаем данные
            device_data = security_data.get('deviceFingerprint', {})
            behavior_data = security_data.get('behavioralAnalysis', {})
            metadata = security_data.get('metadata', {})
            
            # Проверяем черный список
            blacklist_check = self._check_blacklist(security_data)
            if blacklist_check['is_blocked']:
                return self._create_blocked_response(blacklist_check)
            
            # Анализируем отпечаток устройства
            fingerprint_analysis = self._analyze_device_fingerprint(device_data)
            
            # Анализируем поведение
            behavior_analysis = self._analyze_behavior(behavior_data)
            
            # Проверяем на автоматизацию
            automation_check = self._check_automation(device_data, behavior_data)
            
            # Рассчитываем общий риск
            overall_risk = self._calculate_overall_risk(
                fingerprint_analysis,
                behavior_analysis,
                automation_check
            )
            
            # Определяем угрозы
            threats = self._detect_threats(
                fingerprint_analysis,
                behavior_analysis,
                automation_check,
                overall_risk
            )
            
            # Рекомендуемое действие
            recommended_action = self._get_recommended_action(overall_risk, threats)
            
            # Формируем результат
            analysis_result = {
                'session_id': security_data.get('sessionId'),
                'timestamp': timezone.now().isoformat(),
                'fingerprint_analysis': fingerprint_analysis,
                'behavior_analysis': behavior_analysis,
                'automation_check': automation_check,
                'overall_risk': overall_risk,
                'threats': threats,
                'recommended_action': recommended_action,
                'blacklist_check': blacklist_check,
                'analysis_confidence': self._calculate_analysis_confidence(
                    fingerprint_analysis, behavior_analysis
                )
            }
            
            logger.info(f"Security analysis completed. Risk level: {overall_risk['level']}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing security data: {str(e)}")
            return self._create_error_response(str(e))
    
    def _check_blacklist(self, security_data: Dict) -> Dict:
        """
        Проверяет данные по черному списку
        """
        ip_address = security_data.get('metadata', {}).get('ipAddress')
        fingerprint_hash = security_data.get('deviceFingerprint', {}).get('hash')
        user_agent = security_data.get('metadata', {}).get('userAgent')
        
        blocked_items = []
        
        # Проверяем IP
        if ip_address and SecurityBlacklist.is_blocked('ip', ip_address):
            blocked_items.append({'type': 'ip', 'value': ip_address})
        
        # Проверяем отпечаток
        if fingerprint_hash and SecurityBlacklist.is_blocked('fingerprint', fingerprint_hash):
            blocked_items.append({'type': 'fingerprint', 'value': fingerprint_hash})
        
        # Проверяем User Agent
        if user_agent and SecurityBlacklist.is_blocked('user_agent', user_agent):
            blocked_items.append({'type': 'user_agent', 'value': user_agent})
        
        return {
            'is_blocked': len(blocked_items) > 0,
            'blocked_items': blocked_items,
            'reason': 'Найдено в черном списке' if blocked_items else None
        }
    
    def _analyze_device_fingerprint(self, device_data: Dict) -> Dict:
        """
        Анализирует отпечаток устройства
        """
        if not device_data:
            return {
                'confidence': 0,
                'risk_factors': ['Отсутствуют данные отпечатка'],
                'is_suspicious': True
            }
        
        confidence = device_data.get('confidence', 0)
        risk_factors = []
        
        # Проверяем уверенность в отпечатке
        if confidence < self.RISK_THRESHOLDS['fingerprint_confidence']['low']:
            risk_factors.append('Низкая уверенность в отпечатке устройства')
        
        # Проверяем на признаки автоматизации
        automation_indicators = device_data.get('automationIndicators', {})
        if automation_indicators.get('webdriver'):
            risk_factors.append('Обнаружен WebDriver')
        if automation_indicators.get('phantom'):
            risk_factors.append('Обнаружен PhantomJS')
        if automation_indicators.get('selenium'):
            risk_factors.append('Обнаружен Selenium')
        
        # Проверяем браузерную информацию
        browser_info = device_data.get('browser', {})
        if not browser_info.get('userAgent'):
            risk_factors.append('Отсутствует User Agent')
        
        # Проверяем экранную информацию
        screen_info = device_data.get('screen', {})
        if screen_info.get('width', 0) == 0 or screen_info.get('height', 0) == 0:
            risk_factors.append('Некорректные размеры экрана')
        
        # Проверяем Canvas отпечаток
        canvas_hash = device_data.get('canvas', {}).get('hash')
        if not canvas_hash:
            risk_factors.append('Отсутствует Canvas отпечаток')
        
        return {
            'confidence': confidence,
            'risk_factors': risk_factors,
            'is_suspicious': len(risk_factors) > 2 or confidence < 30,
            'automation_detected': len([f for f in risk_factors if 'WebDriver' in f or 'Selenium' in f or 'PhantomJS' in f]) > 0
        }
    
    def _analyze_behavior(self, behavior_data: Dict) -> Dict:
        """
        Анализирует поведенческие данные
        """
        if not behavior_data:
            return {
                'is_human': None,
                'confidence': 0,
                'risk_score': 100,
                'risk_factors': ['Отсутствуют поведенческие данные']
            }
        
        is_human = behavior_data.get('isHuman')
        confidence = behavior_data.get('confidence', 0)
        risk_score = behavior_data.get('riskScore', 0)
        
        risk_factors = []
        
        # Анализируем взаимодействия
        interactions = behavior_data.get('totalInteractions', 0)
        if interactions == 0:
            risk_factors.append('Отсутствие взаимодействий с интерфейсом')
        elif interactions < 5:
            risk_factors.append('Слишком мало взаимодействий')
        
        # Анализируем подозрительные паттерны
        suspicious_patterns = behavior_data.get('suspiciousPatterns', 0)
        if suspicious_patterns > self.RISK_THRESHOLDS['suspicious_patterns']['medium']:
            risk_factors.append(f'Много подозрительных паттернов: {suspicious_patterns}')
        
        # Анализируем высокорисковые паттерны
        high_risk_patterns = behavior_data.get('highRiskPatterns', 0)
        if high_risk_patterns > 0:
            risk_factors.append(f'Высокорисковые паттерны: {high_risk_patterns}')
        
        # Проверяем риск-скор
        if risk_score > self.RISK_THRESHOLDS['behavior_risk_score']['high']:
            risk_factors.append('Высокий риск-скор поведения')
        
        return {
            'is_human': is_human,
            'confidence': confidence,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'total_interactions': interactions,
            'suspicious_patterns': suspicious_patterns,
            'high_risk_patterns': high_risk_patterns
        }
    
    def _check_automation(self, device_data: Dict, behavior_data: Dict) -> Dict:
        """
        Проверяет признаки автоматизации
        """
        automation_indicators = []
        confidence = 0
        
        # Проверяем device fingerprint
        device_automation = device_data.get('automationIndicators', {})
        if device_automation.get('webdriver'):
            automation_indicators.append('WebDriver обнаружен')
            confidence += 30
        if device_automation.get('phantom'):
            automation_indicators.append('PhantomJS обнаружен')
            confidence += 25
        if device_automation.get('selenium'):
            automation_indicators.append('Selenium обнаружен')
            confidence += 35
        
        # Проверяем поведенческие признаки
        if behavior_data.get('isHuman') is False:
            automation_indicators.append('Поведение не соответствует человеку')
            confidence += 40
        
        behavior_risk = behavior_data.get('riskScore', 0)
        if behavior_risk > 80:
            automation_indicators.append('Очень высокий риск-скор поведения')
            confidence += 20
        
        # Проверяем отсутствие взаимодействий
        interactions = behavior_data.get('totalInteractions', 0)
        if interactions == 0:
            automation_indicators.append('Полное отсутствие взаимодействий')
            confidence += 15
        
        return {
            'detected': confidence > 50,
            'confidence': min(confidence, 100),
            'indicators': automation_indicators
        }
    
    def _calculate_overall_risk(self, fingerprint_analysis: Dict, 
                              behavior_analysis: Dict, 
                              automation_check: Dict) -> Dict:
        """
        Рассчитывает общий риск-скор
        """
        risk_score = 0
        
        # Автоматизация (самый высокий вес)
        if automation_check['detected']:
            risk_score += self.RISK_WEIGHTS['automation_detected']
        
        # Поведенческий риск
        behavior_risk = behavior_analysis.get('risk_score', 0)
        normalized_behavior_risk = (behavior_risk / 100) * self.RISK_WEIGHTS['behavior_risk']
        risk_score += normalized_behavior_risk
        
        # Уверенность в отпечатке (обратная зависимость)
        fingerprint_confidence = fingerprint_analysis.get('confidence', 100)
        fingerprint_risk = (100 - fingerprint_confidence) / 100 * self.RISK_WEIGHTS['fingerprint_confidence']
        risk_score += fingerprint_risk
        
        # Подозрительные паттерны
        suspicious_patterns = behavior_analysis.get('suspicious_patterns', 0)
        pattern_risk = min(suspicious_patterns / 10, 1) * self.RISK_WEIGHTS['suspicious_patterns']
        risk_score += pattern_risk
        
        # Количество взаимодействий (обратная зависимость)
        interactions = behavior_analysis.get('total_interactions', 0)
        interaction_risk = max(0, (10 - interactions) / 10) * self.RISK_WEIGHTS['interaction_count']
        risk_score += interaction_risk
        
        # Определяем уровень риска
        if risk_score >= self.RISK_THRESHOLDS['overall_risk_score']['high']:
            level = 'critical' if risk_score >= 90 else 'high'
        elif risk_score >= self.RISK_THRESHOLDS['overall_risk_score']['medium']:
            level = 'medium'
        elif risk_score >= self.RISK_THRESHOLDS['overall_risk_score']['low']:
            level = 'low'
        else:
            level = 'minimal'
        
        return {
            'score': round(risk_score, 2),
            'level': level,
            'components': {
                'automation': automation_check['detected'],
                'behavior_risk': behavior_risk,
                'fingerprint_confidence': fingerprint_confidence,
                'suspicious_patterns': suspicious_patterns,
                'interactions': interactions
            }
        }
    
    def _detect_threats(self, fingerprint_analysis: Dict, 
                       behavior_analysis: Dict, 
                       automation_check: Dict, 
                       overall_risk: Dict) -> List[Dict]:
        """
        Обнаруживает конкретные угрозы
        """
        threats = []
        
        # Угроза автоматизации
        if automation_check['detected']:
            threats.append({
                'type': 'automation',
                'severity': 'high' if automation_check['confidence'] > 80 else 'medium',
                'confidence': automation_check['confidence'],
                'description': f"Обнаружена автоматизация: {', '.join(automation_check['indicators'])}",
                'recommended_action': 'block'
            })
        
        # Угроза бота
        if (behavior_analysis.get('is_human') is False or 
            behavior_analysis.get('risk_score', 0) > 80):
            threats.append({
                'type': 'bot',
                'severity': 'high',
                'confidence': 100 - behavior_analysis.get('confidence', 0),
                'description': 'Поведение указывает на бота',
                'recommended_action': 'challenge'
            })
        
        # Подозрительное поведение
        if behavior_analysis.get('suspicious_patterns', 0) > 5:
            threats.append({
                'type': 'suspicious_behavior',
                'severity': 'medium',
                'confidence': 70,
                'description': f"Обнаружено {behavior_analysis['suspicious_patterns']} подозрительных паттернов",
                'recommended_action': 'monitor'
            })
        
        # Высокорисковый отпечаток
        if fingerprint_analysis.get('is_suspicious'):
            threats.append({
                'type': 'high_risk_fingerprint',
                'severity': 'medium',
                'confidence': 60,
                'description': f"Подозрительный отпечаток: {', '.join(fingerprint_analysis['risk_factors'])}",
                'recommended_action': 'monitor'
            })
        
        # Общий высокий риск
        if overall_risk['level'] in ['high', 'critical']:
            threats.append({
                'type': 'fraud_attempt',
                'severity': 'critical' if overall_risk['level'] == 'critical' else 'high',
                'confidence': overall_risk['score'],
                'description': f"Высокий общий риск-скор: {overall_risk['score']}",
                'recommended_action': 'block' if overall_risk['level'] == 'critical' else 'challenge'
            })
        
        return threats
    
    def _get_recommended_action(self, overall_risk: Dict, threats: List[Dict]) -> str:
        """
        Определяет рекомендуемое действие на основе анализа
        """
        if overall_risk['level'] == 'critical':
            return 'block'
        
        # Проверяем наличие критических угроз
        for threat in threats:
            if threat['severity'] == 'critical':
                return 'block'
            elif threat['severity'] == 'high' and threat['type'] in ['automation', 'bot']:
                return 'challenge'
        
        if overall_risk['level'] == 'high':
            return 'challenge'
        elif overall_risk['level'] == 'medium':
            return 'monitor'
        else:
            return 'allow'
    
    def _calculate_analysis_confidence(self, fingerprint_analysis: Dict, 
                                     behavior_analysis: Dict) -> float:
        """
        Рассчитывает уверенность в анализе
        """
        fingerprint_confidence = fingerprint_analysis.get('confidence', 0)
        behavior_confidence = behavior_analysis.get('confidence', 0)
        
        # Средневзвешенная уверенность
        total_confidence = (fingerprint_confidence * 0.4 + behavior_confidence * 0.6)
        
        # Снижаем уверенность при отсутствии данных
        if not fingerprint_analysis or fingerprint_confidence == 0:
            total_confidence *= 0.7
        if not behavior_analysis or behavior_confidence == 0:
            total_confidence *= 0.5
        
        return round(total_confidence, 2)
    
    def _create_blocked_response(self, blacklist_check: Dict) -> Dict:
        """
        Создает ответ для заблокированного пользователя
        """
        return {
            'session_id': None,
            'timestamp': timezone.now().isoformat(),
            'blocked': True,
            'reason': blacklist_check['reason'],
            'blocked_items': blacklist_check['blocked_items'],
            'recommended_action': 'block',
            'overall_risk': {'score': 100, 'level': 'critical'},
            'analysis_confidence': 100
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """
        Создает ответ при ошибке анализа
        """
        return {
            'session_id': None,
            'timestamp': timezone.now().isoformat(),
            'error': True,
            'error_message': error_message,
            'recommended_action': 'allow',  # При ошибке разрешаем по умолчанию
            'overall_risk': {'score': 0, 'level': 'minimal'},
            'analysis_confidence': 0
        }
    
    def get_security_statistics(self, days: int = 7) -> Dict:
        """
        Получает статистику безопасности за указанный период
        """
        cache_key = f'security_stats_{days}'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Общая статистика отчетов
        reports = SecurityReport.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        total_reports = reports.count()
        
        # Распределение по уровням риска
        risk_distribution = reports.values('risk_level').annotate(
            count=Count('id')
        ).order_by('risk_level')
        
        # Обнаруженные угрозы
        threats = ThreatDetection.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        threat_types = threats.values('threat_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Топ подозрительных IP
        suspicious_ips = reports.filter(
            threat_detected=True
        ).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Статистика автоматизации
        automation_detected = reports.filter(automation_detected=True).count()
        
        # Средние показатели
        avg_risk_score = reports.aggregate(Avg('overall_risk_score'))['overall_risk_score__avg'] or 0
        avg_confidence = reports.aggregate(Avg('analysis_confidence'))['analysis_confidence__avg'] or 0
        
        stats = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'total_reports': total_reports,
            'risk_distribution': list(risk_distribution),
            'threat_types': list(threat_types),
            'suspicious_ips': list(suspicious_ips),
            'automation_detected': automation_detected,
            'averages': {
                'risk_score': round(avg_risk_score, 2),
                'confidence': round(avg_confidence, 2)
            },
            'generated_at': timezone.now().isoformat()
        }
        
        # Кешируем на 5 минут
        cache.set(cache_key, stats, self.cache_timeout)
        
        return stats
    
    def add_to_blacklist(self, blacklist_type: str, value: str, 
                        reason: str, description: str = '', 
                        expires_at: Optional[datetime] = None,
                        created_by: Optional[object] = None) -> bool:
        """
        Добавляет запись в черный список
        """
        try:
            SecurityBlacklist.objects.create(
                blacklist_type=blacklist_type,
                value=value,
                reason=reason,
                description=description,
                expires_at=expires_at,
                created_by=created_by
            )
            
            logger.info(f"Added to blacklist: {blacklist_type}={value}, reason={reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to blacklist: {str(e)}")
            return False