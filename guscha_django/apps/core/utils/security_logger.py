import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.utils import timezone


class SecurityLogger:
    """
    Централизованный класс для security logging с поддержкой
    структурированного логирования и различных типов событий безопасности.
    """
    
    def __init__(self):
        self.security_logger = logging.getLogger('security')
        self.monitoring_logger = logging.getLogger('security.monitoring')
        self.audit_logger = logging.getLogger('security.audit')
        self.threats_logger = logging.getLogger('security.threats')
        self.auth_logger = logging.getLogger('security.authentication')
        self.authz_logger = logging.getLogger('security.authorization')
        self.ratelimit_logger = logging.getLogger('security.ratelimit')
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Получить IP адрес клиента с учетом прокси."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _get_user_info(self, user: Optional[User]) -> str:
        """Получить информацию о пользователе для логирования."""
        if not user or user.is_anonymous:
            return 'anonymous'
        return f'{user.username} (ID: {user.id})'
    
    def _create_log_context(self, request: HttpRequest, user: Optional[User] = None, 
                           action: str = '', **kwargs) -> Dict[str, Any]:
        """Создать контекст для логирования."""
        context = {
            'ip': self._get_client_ip(request),
            'user': self._get_user_info(user or getattr(request, 'user', None)),
            'path': request.path,
            'method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
            'timestamp': timezone.now().isoformat(),
            'action': action,
        }
        context.update(kwargs)
        return context
    
    def log_security_event(self, request: HttpRequest, event_type: str, 
                          message: str, level: str = 'INFO', **kwargs):
        """Логировать общее событие безопасности."""
        context = self._create_log_context(request, **kwargs)
        context['event_type'] = event_type
        
        log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
        
        if level.upper() == 'WARNING':
            self.security_logger.warning(log_message, extra=context)
        elif level.upper() == 'ERROR':
            self.security_logger.error(log_message, extra=context)
        elif level.upper() == 'CRITICAL':
            self.security_logger.critical(log_message, extra=context)
        else:
            self.security_logger.info(log_message, extra=context)
    
    def log_threat_detected(self, request: HttpRequest, threat_type: str, 
                           severity: str, details: Dict[str, Any]):
        """Логировать обнаруженную угрозу."""
        context = self._create_log_context(request)
        context.update({
            'threat_type': threat_type,
            'severity': severity,
            'details': details,
        })
        
        message = f"THREAT DETECTED: {threat_type} (Severity: {severity})"
        log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
        
        if severity.upper() in ['HIGH', 'CRITICAL']:
            self.threats_logger.critical(log_message, extra=context)
        else:
            self.threats_logger.warning(log_message, extra=context)
    
    def log_authentication_event(self, request: HttpRequest, event_type: str, 
                                user: Optional[User] = None, success: bool = True, 
                                details: Optional[Dict[str, Any]] = None):
        """Логировать события аутентификации."""
        context = self._create_log_context(request, user, event_type)
        context.update({
            'success': success,
            'details': details or {},
        })
        
        status = 'SUCCESS' if success else 'FAILED'
        message = f"AUTHENTICATION {status}: {event_type}"
        log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
        
        if success:
            self.auth_logger.info(log_message, extra=context)
        else:
            self.auth_logger.warning(log_message, extra=context)
    
    def log_authorization_event(self, request: HttpRequest, resource: str, 
                               action: str, user: Optional[User] = None, 
                               granted: bool = True, reason: str = ''):
        """Логировать события авторизации."""
        context = self._create_log_context(request, user, action)
        context.update({
            'resource': resource,
            'granted': granted,
            'reason': reason,
        })
        
        status = 'GRANTED' if granted else 'DENIED'
        message = f"AUTHORIZATION {status}: {action} on {resource}"
        if reason:
            message += f" (Reason: {reason})"
        
        log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
        
        if granted:
            self.authz_logger.info(log_message, extra=context)
        else:
            self.authz_logger.warning(log_message, extra=context)
    
    def log_rate_limit_event(self, request: HttpRequest, limit_type: str, 
                            current_count: int, limit: int, blocked: bool = False):
        """Логировать события rate limiting."""
        context = self._create_log_context(request, action='rate_limit_check')
        context.update({
            'limit_type': limit_type,
            'current_count': current_count,
            'limit': limit,
            'blocked': blocked,
            'usage_percentage': round((current_count / limit) * 100, 2) if limit > 0 else 0,
        })
        
        if blocked:
            message = f"RATE LIMIT EXCEEDED: {limit_type} ({current_count}/{limit})"
            log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
            self.ratelimit_logger.warning(log_message, extra=context)
        else:
            message = f"Rate limit check: {limit_type} ({current_count}/{limit})"
            log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
            self.ratelimit_logger.info(log_message, extra=context)
    
    def log_audit_event(self, request: HttpRequest, action: str, 
                       resource: str, user: Optional[User] = None, 
                       changes: Optional[Dict[str, Any]] = None, 
                       metadata: Optional[Dict[str, Any]] = None):
        """Логировать события аудита для чувствительных операций."""
        context = self._create_log_context(request, user, action)
        context.update({
            'resource': resource,
            'changes': changes or {},
            'metadata': metadata or {},
        })
        
        message = f"AUDIT: {action} on {resource}"
        log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
        
        self.audit_logger.info(log_message, extra=context)
    
    def log_monitoring_event(self, request: HttpRequest, metric_name: str, 
                           value: Any, threshold: Optional[Any] = None, 
                           alert: bool = False):
        """Логировать события мониторинга метрик безопасности."""
        context = self._create_log_context(request, action='monitoring')
        context.update({
            'metric_name': metric_name,
            'value': value,
            'threshold': threshold,
            'alert': alert,
        })
        
        message = f"MONITORING: {metric_name} = {value}"
        if threshold is not None:
            message += f" (Threshold: {threshold})"
        
        log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
        
        if alert:
            self.monitoring_logger.warning(log_message, extra=context)
        else:
            self.monitoring_logger.info(log_message, extra=context)
    
    def log_suspicious_activity(self, request: HttpRequest, activity_type: str, 
                               indicators: Dict[str, Any], risk_score: int = 0):
        """Логировать подозрительную активность."""
        context = self._create_log_context(request, action='suspicious_activity')
        context.update({
            'activity_type': activity_type,
            'indicators': indicators,
            'risk_score': risk_score,
        })
        
        message = f"SUSPICIOUS ACTIVITY: {activity_type} (Risk Score: {risk_score})"
        log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
        
        if risk_score >= 80:
            self.threats_logger.critical(log_message, extra=context)
        elif risk_score >= 60:
            self.threats_logger.warning(log_message, extra=context)
        else:
            self.monitoring_logger.info(log_message, extra=context)
    
    def log_access_denied(self, request: HttpRequest, reason: str, 
                         details: Optional[Dict[str, Any]] = None):
        """Логировать отказ в доступе."""
        context = self._create_log_context(request, action='access_denied')
        context.update({
            'reason': reason,
            'details': details or {},
        })
        
        message = f"ACCESS DENIED: {reason}"
        log_message = f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
        
        self.authz_logger.warning(log_message, extra=context)


# Глобальный экземпляр для использования в приложении
security_logger = SecurityLogger()


# Декораторы для автоматического логирования
def log_security_event(event_type: str, level: str = 'INFO'):
    """Декоратор для автоматического логирования событий безопасности."""
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            try:
                result = func(request, *args, **kwargs)
                security_logger.log_security_event(
                    request, event_type, 
                    f"Function {func.__name__} executed successfully", 
                    level
                )
                return result
            except Exception as e:
                security_logger.log_security_event(
                    request, event_type, 
                    f"Function {func.__name__} failed: {str(e)}", 
                    'ERROR'
                )
                raise
        return wrapper
    return decorator


def log_audit_action(action: str, resource: str):
    """Декоратор для автоматического логирования действий аудита."""
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            
            # Логируем попытку действия
            security_logger.log_audit_event(
                request, f"{action}_attempt", resource, user,
                metadata={'function': func.__name__}
            )
            
            try:
                result = func(request, *args, **kwargs)
                
                # Логируем успешное выполнение
                security_logger.log_audit_event(
                    request, f"{action}_success", resource, user,
                    metadata={'function': func.__name__, 'result': 'success'}
                )
                
                return result
            except Exception as e:
                # Логируем ошибку
                security_logger.log_audit_event(
                    request, f"{action}_error", resource, user,
                    metadata={'function': func.__name__, 'error': str(e)}
                )
                raise
        return wrapper
    return decorator