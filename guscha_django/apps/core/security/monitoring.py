"""Система мониторинга безопасности в реальном времени."""

import json
import time
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from threading import Lock
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone


class SecurityMonitor:
    """Система мониторинга безопасности в реальном времени."""
    
    def __init__(self):
        self.threat_cache = defaultdict(lambda: deque(maxlen=1000))
        self.metrics_cache = defaultdict(lambda: deque(maxlen=1000))
        self.alert_cache = deque(maxlen=100)
        self.lock = Lock()
        
        # Пороговые значения для алертов
        self.thresholds = {
            'failed_logins_per_minute': 10,
            'suspicious_requests_per_minute': 20,
            'high_risk_score_threshold': 80,
            'blocked_ips_threshold': 5,
            'error_rate_threshold': 0.1,  # 10%
        }
    
    def record_threat(self, threat_type: str, ip_address: str, 
                     risk_score: int, details: Dict[str, Any]):
        """Записать обнаруженную угрозу."""
        with self.lock:
            timestamp = timezone.now()
            threat_data = {
                'timestamp': timestamp.isoformat(),
                'type': threat_type,
                'ip_address': ip_address,
                'risk_score': risk_score,
                'details': details
            }
            
            # Добавляем в кэш угроз
            self.threat_cache[threat_type].append(threat_data)
            
            # Проверяем на необходимость создания алерта
            self._check_threat_alerts(threat_type, ip_address, risk_score)
            
            # Сохраняем в Redis для персистентности
            cache_key = f"security_threat_{threat_type}_{int(timestamp.timestamp())}"
            cache.set(cache_key, threat_data, timeout=86400)  # 24 часа
    
    def record_security_event(self, event_type: str, ip_address: str, 
                            user_id: Optional[int], details: Dict[str, Any]):
        """Записать событие безопасности."""
        with self.lock:
            timestamp = timezone.now()
            event_data = {
                'timestamp': timestamp.isoformat(),
                'type': event_type,
                'ip_address': ip_address,
                'user_id': user_id,
                'details': details
            }
            
            # Добавляем в кэш метрик
            self.metrics_cache[event_type].append(event_data)
            
            # Проверяем на аномалии
            self._check_anomalies(event_type, ip_address)
            
            # Сохраняем в Redis
            cache_key = f"security_event_{event_type}_{int(timestamp.timestamp())}"
            cache.set(cache_key, event_data, timeout=86400)
    
    def get_threat_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Получить сводку угроз за указанный период."""
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        summary = {
            'total_threats': 0,
            'high_risk_threats': 0,
            'threat_types': defaultdict(int),
            'top_attacking_ips': defaultdict(int),
            'average_risk_score': 0,
            'time_window': time_window_minutes
        }
        
        total_risk_score = 0
        
        with self.lock:
            for threat_type, threats in self.threat_cache.items():
                for threat in threats:
                    threat_time = datetime.fromisoformat(threat['timestamp'])
                    if threat_time.replace(tzinfo=pytz.UTC) >= cutoff_time:
                        summary['total_threats'] += 1
                        summary['threat_types'][threat_type] += 1
                        summary['top_attacking_ips'][threat['ip_address']] += 1
                        
                        risk_score = threat['risk_score']
                        total_risk_score += risk_score
                        
                        if risk_score >= self.thresholds['high_risk_score_threshold']:
                            summary['high_risk_threats'] += 1
        
        if summary['total_threats'] > 0:
            summary['average_risk_score'] = total_risk_score / summary['total_threats']
        
        # Сортируем топ IP по количеству атак
        summary['top_attacking_ips'] = dict(
            sorted(summary['top_attacking_ips'].items(), 
                  key=lambda x: x[1], reverse=True)[:10]
        )
        
        return summary
    
    def get_security_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Получить метрики безопасности за указанный период."""
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        metrics = {
            'total_events': 0,
            'failed_logins': 0,
            'successful_logins': 0,
            'blocked_requests': 0,
            'suspicious_activities': 0,
            'unique_ips': set(),
            'error_rate': 0,
            'time_window': time_window_minutes
        }
        
        total_requests = 0
        error_requests = 0
        
        with self.lock:
            for event_type, events in self.metrics_cache.items():
                for event in events:
                    event_time = datetime.fromisoformat(event['timestamp'])
                    if event_time.replace(tzinfo=pytz.UTC) >= cutoff_time:
                        metrics['total_events'] += 1
                        metrics['unique_ips'].add(event['ip_address'])
                        
                        total_requests += 1
                        
                        if event_type == 'failed_login':
                            metrics['failed_logins'] += 1
                        elif event_type == 'successful_login':
                            metrics['successful_logins'] += 1
                        elif event_type == 'blocked_request':
                            metrics['blocked_requests'] += 1
                        elif event_type == 'suspicious_activity':
                            metrics['suspicious_activities'] += 1
                        
                        # Считаем ошибки (статус коды 4xx, 5xx)
                        status_code = event['details'].get('status_code', 200)
                        if status_code >= 400:
                            error_requests += 1
        
        metrics['unique_ips'] = len(metrics['unique_ips'])
        
        if total_requests > 0:
            metrics['error_rate'] = error_requests / total_requests
        
        return metrics
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Получить активные алерты."""
        with self.lock:
            return list(self.alert_cache)
    
    def _check_threat_alerts(self, threat_type: str, ip_address: str, risk_score: int):
        """Проверить необходимость создания алерта для угрозы."""
        alert_created = False
        
        # Алерт для высокого риска
        if risk_score >= self.thresholds['high_risk_score_threshold']:
            self._create_alert(
                'HIGH_RISK_THREAT',
                f'Обнаружена угроза высокого риска: {threat_type} от {ip_address}',
                {'threat_type': threat_type, 'ip_address': ip_address, 'risk_score': risk_score},
                severity='critical',
                ip_address=ip_address
            )
            alert_created = True
        
        # Проверяем частоту угроз от одного IP
        recent_threats = self._count_recent_events_by_ip(
            self.threat_cache, ip_address, minutes=1
        )
        
        if recent_threats >= 5:  # 5 угроз за минуту от одного IP
            self._create_alert(
                'THREAT_BURST',
                f'Множественные угрозы от IP {ip_address}: {recent_threats} за минуту',
                {'ip_address': ip_address, 'threat_count': recent_threats},
                severity='high',
                ip_address=ip_address
            )
            alert_created = True
        
        return alert_created
    
    def _check_anomalies(self, event_type: str, ip_address: str):
        """Проверить аномалии в событиях безопасности."""
        # Проверяем частоту неудачных попыток входа
        if event_type == 'failed_login':
            recent_failures = self._count_recent_events_by_ip(
                {'failed_login': self.metrics_cache['failed_login']}, 
                ip_address, minutes=1
            )
            
            if recent_failures >= self.thresholds['failed_logins_per_minute']:
                self._create_alert(
                    'BRUTE_FORCE_ATTACK',
                    f'Возможная брутфорс атака от IP {ip_address}: {recent_failures} неудачных попыток за минуту',
                    {'ip_address': ip_address, 'failed_attempts': recent_failures},
                    severity='high',
                    ip_address=ip_address
                )
    
    def _count_recent_events_by_ip(self, cache_dict: Dict, ip_address: str, 
                                  minutes: int = 1) -> int:
        """Подсчитать количество событий от IP за указанный период."""
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        count = 0
        
        for events in cache_dict.values():
            for event in events:
                if (event['ip_address'] == ip_address and 
                    datetime.fromisoformat(event['timestamp']).replace(tzinfo=pytz.UTC) >= cutoff_time):
                    count += 1
        
        return count
    
    def _create_alert(self, alert_type: str, message: str, 
                     details: Dict[str, Any], severity: str = 'medium', 
                     ip_address: str = None, user_id: int = None):
        """Создать алерт безопасности."""
        alert = {
            'id': f"{alert_type}_{int(time.time())}",
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': timezone.now().isoformat(),
            'details': details,
            'acknowledged': False
        }
        
        self.alert_cache.append(alert)
        
        # Сохраняем в Redis
        cache_key = f"security_alert_{alert['id']}"
        cache.set(cache_key, alert, timeout=86400)
        
        # Логируем критические алерты
        if severity == 'critical':
            from apps.core.utils.security_logger import security_logger
            security_logger.threats_logger.critical(
                f"SECURITY ALERT: {message}", 
                extra={
                    'alert_data': alert,
                    'ip': ip_address or 'unknown',
                    'user': f'user_id:{user_id}' if user_id else 'anonymous',
                    'path': 'security_monitoring'
                }
            )
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Подтвердить обработку алерта."""
        with self.lock:
            for alert in self.alert_cache:
                if alert['id'] == alert_id:
                    alert['acknowledged'] = True
                    alert['acknowledged_at'] = timezone.now().isoformat()
                    
                    # Обновляем в Redis
                    cache_key = f"security_alert_{alert_id}"
                    cache.set(cache_key, alert, timeout=86400)
                    
                    return True
        return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Получить данные для dashboard безопасности."""
        return {
            'threat_summary_1h': self.get_threat_summary(60),
            'threat_summary_24h': self.get_threat_summary(1440),
            'security_metrics_1h': self.get_security_metrics(60),
            'security_metrics_24h': self.get_security_metrics(1440),
            'active_alerts': self.get_active_alerts(),
            'system_status': self._get_system_status()
        }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Получить статус системы безопасности."""
        metrics_1h = self.get_security_metrics(60)
        threats_1h = self.get_threat_summary(60)
        
        # Определяем общий статус безопасности
        status = 'normal'
        if threats_1h['high_risk_threats'] > 0:
            status = 'critical'
        elif threats_1h['total_threats'] > 10:
            status = 'warning'
        elif metrics_1h['error_rate'] > self.thresholds['error_rate_threshold']:
            status = 'warning'
        
        return {
            'overall_status': status,
            'monitoring_active': True,
            'last_update': timezone.now().isoformat(),
            'cache_size': {
                'threats': sum(len(cache) for cache in self.threat_cache.values()),
                'events': sum(len(cache) for cache in self.metrics_cache.values()),
                'alerts': len(self.alert_cache)
            }
        }


# Глобальный экземпляр монитора
security_monitor = SecurityMonitor()