# -*- coding: utf-8 -*-
"""
Система безопасного логирования для отслеживания подозрительной активности.

Обеспечивает:
- Структурированное логирование событий безопасности
- Анализ подозрительной активности
- Алерты и уведомления
- Защиту от переполнения логов
"""

import json
import logging
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from collections import defaultdict, deque
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import HttpRequest

# Настройка логгера безопасности
security_logger = logging.getLogger('security')
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)
    security_logger.setLevel(logging.INFO)


class SecurityEvent:
    """
    Класс для представления события безопасности.
    """
    
    # Типы событий безопасности
    EVENT_TYPES = {
        'LOGIN_SUCCESS': 'Успешная авторизация',
        'LOGIN_FAILED': 'Неудачная попытка авторизации',
        'LOGIN_BLOCKED': 'Заблокированная попытка авторизации',
        'LOGOUT': 'Выход из системы',
        'PASSWORD_CHANGE': 'Смена пароля',
        'PASSWORD_RESET': 'Сброс пароля',
        'ACCOUNT_LOCKED': 'Блокировка аккаунта',
        'ACCOUNT_UNLOCKED': 'Разблокировка аккаунта',
        'PERMISSION_DENIED': 'Отказ в доступе',
        'SUSPICIOUS_REQUEST': 'Подозрительный запрос',
        'RATE_LIMIT_EXCEEDED': 'Превышение лимита запросов',
        'CSRF_ATTACK': 'Попытка CSRF атаки',
        'XSS_ATTACK': 'Попытка XSS атаки',
        'SQL_INJECTION': 'Попытка SQL инъекции',
        'FILE_UPLOAD_BLOCKED': 'Заблокированная загрузка файла',
        'ADMIN_ACCESS': 'Доступ к админ панели',
        'DATA_EXPORT': 'Экспорт данных',
        'DATA_IMPORT': 'Импорт данных',
        'CONFIG_CHANGE': 'Изменение конфигурации',
        'SECURITY_SCAN': 'Сканирование безопасности',
        # Telegram-специфичные события
        'TELEGRAM_AUTH_REQUEST': 'Запрос Telegram аутентификации',
        'TELEGRAM_AUTH_SUCCESS': 'Успешная Telegram аутентификация',
        'TELEGRAM_AUTH_FAILED': 'Неудачная Telegram аутентификация',
        'TELEGRAM_RATE_LIMIT': 'Превышение лимита Telegram запросов',
        'TELEGRAM_SUSPICIOUS_PATTERN': 'Подозрительный паттерн Telegram активности',
        'TELEGRAM_MULTIPLE_PHONES': 'Множественные номера телефонов с одного IP',
        'TELEGRAM_RAPID_REQUESTS': 'Быстрые последовательные Telegram запросы',
        'TELEGRAM_INVALID_TOKEN': 'Недействительный Telegram токен',
        'TELEGRAM_BOT_INTERACTION': 'Взаимодействие с Telegram ботом',
    }
    
    # Уровни критичности
    SEVERITY_LEVELS = {
        'LOW': 1,
        'MEDIUM': 2,
        'HIGH': 3,
        'CRITICAL': 4,
    }
    
    def __init__(self, 
                 event_type: str,
                 severity: str = 'MEDIUM',
                 user: Optional[Union[User, str]] = None,
                 ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None,
                 request_path: Optional[str] = None,
                 additional_data: Optional[Dict[str, Any]] = None,
                 description: Optional[str] = None):
        """
        Инициализирует событие безопасности.
        
        Args:
            event_type: Тип события
            severity: Уровень критичности
            user: Пользователь (объект User или строка)
            ip_address: IP адрес
            user_agent: User-Agent
            request_path: Путь запроса
            additional_data: Дополнительные данные
            description: Описание события
        """
        self.event_type = event_type
        self.severity = severity
        self.timestamp = timezone.now()
        self.user = user
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.request_path = request_path
        self.additional_data = additional_data or {}
        self.description = description or self.EVENT_TYPES.get(event_type, 'Неизвестное событие')
        
        # Генерируем уникальный ID события
        self.event_id = self._generate_event_id()
    
    def _generate_event_id(self) -> str:
        """
        Генерирует уникальный ID события.
        
        Returns:
            Уникальный ID события
        """
        data = f"{self.timestamp}{self.event_type}{self.ip_address}{self.user}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует событие в словарь.
        
        Returns:
            Словарь с данными события
        """
        user_info = None
        if isinstance(self.user, User):
            user_info = {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'is_staff': self.user.is_staff,
                'is_superuser': self.user.is_superuser,
            }
        elif isinstance(self.user, str):
            user_info = {'username': self.user}
        
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'severity': self.severity,
            'severity_level': self.SEVERITY_LEVELS.get(self.severity, 2),
            'timestamp': self.timestamp.isoformat(),
            'description': self.description,
            'user': user_info,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'request_path': self.request_path,
            'additional_data': self.additional_data,
        }
    
    def to_json(self) -> str:
        """
        Преобразует событие в JSON строку.
        
        Returns:
            JSON строка с данными события
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class SecurityLogger:
    """
    Основной класс для логирования событий безопасности.
    """
    
    def __init__(self):
        self.logger = security_logger
        self._event_cache = deque(maxlen=1000)  # Кеш последних событий
        self._lock = threading.Lock()
    
    def log_event(self, event: SecurityEvent) -> None:
        """
        Логирует событие безопасности.
        
        Args:
            event: Событие для логирования
        """
        with self._lock:
            # Добавляем в кеш
            self._event_cache.append(event)
            
            # Логируем в зависимости от критичности
            event_data = event.to_dict()
            log_message = self._format_log_message(event_data)
            
            if event.severity == 'CRITICAL':
                self.logger.critical(log_message)
                self._send_alert(event)
            elif event.severity == 'HIGH':
                self.logger.error(log_message)
                self._send_alert(event)
            elif event.severity == 'MEDIUM':
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            # Сохраняем в кеш Django для быстрого доступа
            self._cache_event(event)
            
            # Анализируем на подозрительную активность
            self._analyze_suspicious_activity(event)
    
    def log_login_attempt(self, 
                         request: HttpRequest,
                         username: str,
                         success: bool,
                         reason: Optional[str] = None) -> None:
        """
        Логирует попытку авторизации.
        
        Args:
            request: HTTP запрос
            username: Имя пользователя
            success: Успешность попытки
            reason: Причина неудачи (если применимо)
        """
        event_type = 'LOGIN_SUCCESS' if success else 'LOGIN_FAILED'
        severity = 'LOW' if success else 'MEDIUM'
        
        additional_data = {}
        if not success and reason:
            additional_data['failure_reason'] = reason
        
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user=username,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            request_path=request.path,
            additional_data=additional_data
        )
        
        self.log_event(event)
    
    def log_permission_denied(self, 
                             request: HttpRequest,
                             user: Optional[User] = None,
                             resource: Optional[str] = None) -> None:
        """
        Логирует отказ в доступе.
        
        Args:
            request: HTTP запрос
            user: Пользователь
            resource: Ресурс, к которому был запрошен доступ
        """
        additional_data = {}
        if resource:
            additional_data['resource'] = resource
        
        event = SecurityEvent(
            event_type='PERMISSION_DENIED',
            severity='MEDIUM',
            user=user,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            request_path=request.path,
            additional_data=additional_data
        )
        
        self.log_event(event)
    
    def log_suspicious_request(self, 
                              request: HttpRequest,
                              attack_type: str,
                              details: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирует подозрительный запрос.
        
        Args:
            request: HTTP запрос
            attack_type: Тип атаки
            details: Детали атаки
        """
        additional_data = {
            'attack_type': attack_type,
            'method': request.method,
            'content_type': request.content_type,
        }
        
        if details:
            additional_data.update(details)
        
        # Определяем критичность в зависимости от типа атаки
        severity_map = {
            'XSS': 'HIGH',
            'SQL_INJECTION': 'CRITICAL',
            'CSRF': 'HIGH',
            'COMMAND_INJECTION': 'CRITICAL',
            'PATH_TRAVERSAL': 'HIGH',
            'RATE_LIMIT': 'MEDIUM',
        }
        
        severity = severity_map.get(attack_type.upper(), 'MEDIUM')
        
        event = SecurityEvent(
            event_type='SUSPICIOUS_REQUEST',
            severity=severity,
            user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            request_path=request.path,
            additional_data=additional_data
        )
        
        self.log_event(event)
    
    def log_rate_limit_exceeded(self, 
                               request: HttpRequest,
                               limit_type: str,
                               current_count: int,
                               limit: int) -> None:
        """
        Логирует превышение лимита запросов.
        
        Args:
            request: HTTP запрос
            limit_type: Тип лимита
            current_count: Текущее количество запросов
            limit: Лимит запросов
        """
        additional_data = {
            'limit_type': limit_type,
            'current_count': current_count,
            'limit': limit,
            'method': request.method,
        }
        
        event = SecurityEvent(
            event_type='RATE_LIMIT_EXCEEDED',
            severity='MEDIUM',
            user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            request_path=request.path,
            additional_data=additional_data
        )
        
        self.log_event(event)
    
    def log_telegram_auth_attempt(self, 
                                 request: HttpRequest,
                                 phone_number: Optional[str] = None,
                                 success: bool = True,
                                 failure_reason: Optional[str] = None,
                                 telegram_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирует попытку Telegram аутентификации.
        
        Args:
            request: HTTP запрос
            phone_number: Номер телефона (замаскированный)
            success: Успешность попытки
            failure_reason: Причина неудачи
            telegram_data: Дополнительные данные от Telegram
        """
        event_type = 'TELEGRAM_AUTH_SUCCESS' if success else 'TELEGRAM_AUTH_FAILED'
        severity = 'LOW' if success else 'MEDIUM'
        
        # Маскируем номер телефона для безопасности
        masked_phone = None
        if phone_number:
            masked_phone = phone_number[:3] + '*' * (len(phone_number) - 6) + phone_number[-3:] if len(phone_number) > 6 else '*' * len(phone_number)
        
        additional_data = {
            'masked_phone': masked_phone,
            'telegram_auth': True,
            'endpoint_type': 'telegram_auth'
        }
        
        if failure_reason:
            additional_data['failure_reason'] = failure_reason
            
        if telegram_data:
            # Фильтруем чувствительные данные
            safe_telegram_data = {k: v for k, v in telegram_data.items() 
                                if k not in ['auth_date', 'hash', 'id']}
            additional_data['telegram_data'] = safe_telegram_data
        
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            request_path=request.path,
            additional_data=additional_data
        )
        
        self.log_event(event)
    
    def log_telegram_suspicious_pattern(self, 
                                       request: HttpRequest,
                                       pattern_type: str,
                                       details: Dict[str, Any]) -> None:
        """
        Логирует подозрительный паттерн в Telegram активности.
        
        Args:
            request: HTTP запрос
            pattern_type: Тип подозрительного паттерна
            details: Детали паттерна
        """
        severity_map = {
            'multiple_phones': 'HIGH',
            'rapid_requests': 'MEDIUM',
            'invalid_token': 'HIGH',
            'suspicious_timing': 'MEDIUM',
            'bot_like_behavior': 'HIGH'
        }
        
        severity = severity_map.get(pattern_type, 'MEDIUM')
        
        additional_data = {
            'pattern_type': pattern_type,
            'telegram_security': True,
            'endpoint_type': 'telegram_auth',
            **details
        }
        
        event = SecurityEvent(
            event_type='TELEGRAM_SUSPICIOUS_PATTERN',
            severity=severity,
            user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            request_path=request.path,
            additional_data=additional_data
        )
        
        self.log_event(event)
    
    def log_telegram_rate_limit(self, 
                               request: HttpRequest,
                               limit_type: str,
                               current_count: int,
                               limit: int,
                               phone_number: Optional[str] = None) -> None:
        """
        Логирует превышение лимита для Telegram endpoints.
        
        Args:
            request: HTTP запрос
            limit_type: Тип лимита (phone_based, ip_based, etc.)
            current_count: Текущее количество запросов
            limit: Лимит запросов
            phone_number: Номер телефона (если применимо)
        """
        # Маскируем номер телефона
        masked_phone = None
        if phone_number:
            masked_phone = phone_number[:3] + '*' * (len(phone_number) - 6) + phone_number[-3:] if len(phone_number) > 6 else '*' * len(phone_number)
        
        additional_data = {
            'limit_type': limit_type,
            'current_count': current_count,
            'limit': limit,
            'masked_phone': masked_phone,
            'telegram_rate_limit': True,
            'endpoint_type': 'telegram_auth',
            'method': request.method,
        }
        
        event = SecurityEvent(
            event_type='TELEGRAM_RATE_LIMIT',
            severity='MEDIUM',
            user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            request_path=request.path,
            additional_data=additional_data
        )
        
        self.log_event(event)
    
    def get_telegram_security_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Получает статистику безопасности для Telegram endpoints.
        
        Args:
            hours: Количество часов для анализа
        
        Returns:
            Статистика Telegram безопасности
        """
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        with self._lock:
            telegram_events = [
                e for e in self._event_cache 
                if e.timestamp >= cutoff_time and 
                (e.event_type.startswith('TELEGRAM_') or 
                 (e.additional_data and e.additional_data.get('telegram_auth')))
            ]
        
        stats = {
            'total_telegram_events': len(telegram_events),
            'auth_attempts': 0,
            'auth_successes': 0,
            'auth_failures': 0,
            'rate_limit_violations': 0,
            'suspicious_patterns': 0,
            'unique_ips': set(),
            'unique_phones': set(),
            'top_suspicious_ips': defaultdict(int),
            'pattern_types': defaultdict(int),
            'hourly_distribution': defaultdict(int)
        }
        
        for event in telegram_events:
            # Подсчитываем по типам событий
            if event.event_type in ['TELEGRAM_AUTH_SUCCESS', 'TELEGRAM_AUTH_FAILED']:
                stats['auth_attempts'] += 1
                if event.event_type == 'TELEGRAM_AUTH_SUCCESS':
                    stats['auth_successes'] += 1
                else:
                    stats['auth_failures'] += 1
            
            elif event.event_type == 'TELEGRAM_RATE_LIMIT':
                stats['rate_limit_violations'] += 1
            
            elif event.event_type == 'TELEGRAM_SUSPICIOUS_PATTERN':
                stats['suspicious_patterns'] += 1
                if event.additional_data and 'pattern_type' in event.additional_data:
                    stats['pattern_types'][event.additional_data['pattern_type']] += 1
            
            # Собираем уникальные IP и телефоны
            if event.ip_address:
                stats['unique_ips'].add(event.ip_address)
                if event.event_type == 'TELEGRAM_SUSPICIOUS_PATTERN':
                    stats['top_suspicious_ips'][event.ip_address] += 1
            
            if event.additional_data and event.additional_data.get('masked_phone'):
                stats['unique_phones'].add(event.additional_data['masked_phone'])
            
            # Почасовое распределение
            hour_key = event.timestamp.strftime('%Y-%m-%d %H:00')
            stats['hourly_distribution'][hour_key] += 1
        
        # Преобразуем sets в counts и сортируем топы
        stats['unique_ips'] = len(stats['unique_ips'])
        stats['unique_phones'] = len(stats['unique_phones'])
        stats['top_suspicious_ips'] = dict(sorted(stats['top_suspicious_ips'].items(), 
                                                 key=lambda x: x[1], reverse=True)[:10])
        stats['pattern_types'] = dict(stats['pattern_types'])
        stats['hourly_distribution'] = dict(stats['hourly_distribution'])
        
        # Вычисляем дополнительные метрики
        if stats['auth_attempts'] > 0:
            stats['auth_success_rate'] = stats['auth_successes'] / stats['auth_attempts']
            stats['auth_failure_rate'] = stats['auth_failures'] / stats['auth_attempts']
        else:
            stats['auth_success_rate'] = 0
            stats['auth_failure_rate'] = 0
        
        return stats
    
    def get_recent_events(self, 
                         limit: int = 100,
                         event_type: Optional[str] = None,
                         severity: Optional[str] = None,
                         user: Optional[str] = None,
                         ip_address: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получает последние события безопасности.
        
        Args:
            limit: Максимальное количество событий
            event_type: Фильтр по типу события
            severity: Фильтр по критичности
            user: Фильтр по пользователю
            ip_address: Фильтр по IP адресу
        
        Returns:
            Список событий
        """
        with self._lock:
            events = list(self._event_cache)
        
        # Применяем фильтры
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        if user:
            events = [e for e in events if str(e.user) == user]
        
        if ip_address:
            events = [e for e in events if e.ip_address == ip_address]
        
        # Сортируем по времени (новые первыми)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Ограничиваем количество
        events = events[:limit]
        
        return [event.to_dict() for event in events]
    
    def get_security_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Получает статистику безопасности за указанный период.
        
        Args:
            hours: Количество часов для анализа
        
        Returns:
            Статистика безопасности
        """
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_events = [
                e for e in self._event_cache 
                if e.timestamp >= cutoff_time
            ]
        
        stats = {
            'total_events': len(recent_events),
            'events_by_type': defaultdict(int),
            'events_by_severity': defaultdict(int),
            'events_by_hour': defaultdict(int),
            'top_ips': defaultdict(int),
            'top_users': defaultdict(int),
            'attack_attempts': 0,
            'failed_logins': 0,
            'blocked_requests': 0,
        }
        
        for event in recent_events:
            stats['events_by_type'][event.event_type] += 1
            stats['events_by_severity'][event.severity] += 1
            
            hour_key = event.timestamp.strftime('%Y-%m-%d %H:00')
            stats['events_by_hour'][hour_key] += 1
            
            if event.ip_address:
                stats['top_ips'][event.ip_address] += 1
            
            if event.user:
                stats['top_users'][str(event.user)] += 1
            
            # Подсчитываем специальные метрики
            if event.event_type in ['SUSPICIOUS_REQUEST', 'CSRF_ATTACK', 'XSS_ATTACK', 'SQL_INJECTION']:
                stats['attack_attempts'] += 1
            
            if event.event_type == 'LOGIN_FAILED':
                stats['failed_logins'] += 1
            
            if event.event_type in ['RATE_LIMIT_EXCEEDED', 'FILE_UPLOAD_BLOCKED']:
                stats['blocked_requests'] += 1
        
        # Преобразуем defaultdict в обычные словари
        stats['events_by_type'] = dict(stats['events_by_type'])
        stats['events_by_severity'] = dict(stats['events_by_severity'])
        stats['events_by_hour'] = dict(stats['events_by_hour'])
        stats['top_ips'] = dict(sorted(stats['top_ips'].items(), key=lambda x: x[1], reverse=True)[:10])
        stats['top_users'] = dict(sorted(stats['top_users'].items(), key=lambda x: x[1], reverse=True)[:10])
        
        return stats
    
    def _format_log_message(self, event_data: Dict[str, Any]) -> str:
        """
        Форматирует сообщение для лога.
        
        Args:
            event_data: Данные события
        
        Returns:
            Отформатированное сообщение
        """
        user_info = event_data.get('user', {})
        username = user_info.get('username', 'Anonymous') if user_info else 'Anonymous'
        
        message_parts = [
            f"[{event_data['event_type']}]",
            f"User: {username}",
            f"IP: {event_data.get('ip_address', 'Unknown')}",
            f"Path: {event_data.get('request_path', 'Unknown')}",
            f"Description: {event_data['description']}"
        ]
        
        if event_data.get('additional_data'):
            additional = json.dumps(event_data['additional_data'], ensure_ascii=False)
            message_parts.append(f"Additional: {additional}")
        
        return " | ".join(message_parts)
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Получает IP адрес клиента.
        
        Args:
            request: HTTP запрос
        
        Returns:
            IP адрес клиента
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        
        return ip
    
    def _cache_event(self, event: SecurityEvent) -> None:
        """
        Кеширует событие в Django cache.
        
        Args:
            event: Событие для кеширования
        """
        try:
            cache_key = f"security_event_{event.event_id}"
            cache.set(cache_key, event.to_dict(), timeout=3600)  # 1 час
        except Exception as e:
            self.logger.error(f"Failed to cache security event: {str(e)}")
    
    def _send_alert(self, event: SecurityEvent) -> None:
        """
        Отправляет алерт о критическом событии.
        
        Args:
            event: Событие для алерта
        """
        try:
            # Здесь можно добавить отправку email, SMS, Slack и т.д.
            alert_message = f"SECURITY ALERT: {event.description}\n"
            alert_message += f"Event Type: {event.event_type}\n"
            alert_message += f"Severity: {event.severity}\n"
            alert_message += f"User: {event.user}\n"
            alert_message += f"IP: {event.ip_address}\n"
            alert_message += f"Time: {event.timestamp}\n"
            
            if event.additional_data:
                alert_message += f"Details: {json.dumps(event.additional_data, ensure_ascii=False)}\n"
            
            # Логируем алерт
            self.logger.critical(f"SECURITY ALERT SENT: {alert_message}")
            
            # TODO: Добавить реальную отправку уведомлений
            # self._send_email_alert(alert_message)
            # self._send_slack_alert(alert_message)
            
        except Exception as e:
            self.logger.error(f"Failed to send security alert: {str(e)}")
    
    def _analyze_suspicious_activity(self, event: SecurityEvent) -> None:
        """
        Анализирует событие на предмет подозрительной активности.
        
        Args:
            event: Событие для анализа
        """
        try:
            # Анализируем частоту событий от одного IP
            if event.ip_address:
                self._check_ip_frequency(event)
            
            # Анализируем неудачные попытки входа
            if event.event_type == 'LOGIN_FAILED':
                self._check_brute_force_attempts(event)
            
            # Анализируем подозрительные запросы
            if event.event_type == 'SUSPICIOUS_REQUEST':
                self._check_attack_patterns(event)
                
        except Exception as e:
            self.logger.error(f"Failed to analyze suspicious activity: {str(e)}")
    
    def _check_ip_frequency(self, event: SecurityEvent) -> None:
        """
        Проверяет частоту событий от IP адреса.
        
        Args:
            event: Событие для проверки
        """
        if not event.ip_address:
            return
        
        cache_key = f"ip_frequency_{event.ip_address}"
        current_count = cache.get(cache_key, 0)
        current_count += 1
        
        # Устанавливаем счетчик на 1 час
        cache.set(cache_key, current_count, timeout=3600)
        
        # Если превышен лимит, создаем алерт
        if current_count > 100:  # Более 100 событий в час
            alert_event = SecurityEvent(
                event_type='SUSPICIOUS_REQUEST',
                severity='HIGH',
                ip_address=event.ip_address,
                description=f"Высокая активность с IP {event.ip_address}: {current_count} событий за час",
                additional_data={'event_count': current_count, 'timeframe': '1 hour'}
            )
            self.log_event(alert_event)
    
    def _check_brute_force_attempts(self, event: SecurityEvent) -> None:
        """
        Проверяет попытки брутфорса.
        
        Args:
            event: Событие неудачного входа
        """
        if not event.ip_address:
            return
        
        cache_key = f"failed_login_{event.ip_address}"
        failed_attempts = cache.get(cache_key, 0)
        failed_attempts += 1
        
        # Устанавливаем счетчик на 15 минут
        cache.set(cache_key, failed_attempts, timeout=900)
        
        # Если превышен лимит, создаем алерт
        if failed_attempts >= 5:  # 5 неудачных попыток за 15 минут
            alert_event = SecurityEvent(
                event_type='LOGIN_BLOCKED',
                severity='HIGH',
                user=event.user,
                ip_address=event.ip_address,
                description=f"Возможная атака брутфорса с IP {event.ip_address}: {failed_attempts} неудачных попыток",
                additional_data={'failed_attempts': failed_attempts, 'timeframe': '15 minutes'}
            )
            self.log_event(alert_event)
    
    def _check_attack_patterns(self, event: SecurityEvent) -> None:
        """
        Проверяет паттерны атак.
        
        Args:
            event: Подозрительное событие
        """
        attack_type = event.additional_data.get('attack_type', '').upper()
        
        if attack_type in ['SQL_INJECTION', 'XSS', 'COMMAND_INJECTION']:
            # Для критических атак сразу создаем алерт высокой важности
            alert_event = SecurityEvent(
                event_type='SECURITY_SCAN',
                severity='CRITICAL',
                user=event.user,
                ip_address=event.ip_address,
                description=f"Обнаружена попытка {attack_type} атаки",
                additional_data={
                    'original_event_id': event.event_id,
                    'attack_type': attack_type,
                    'request_path': event.request_path
                }
            )
            self.log_event(alert_event)


# Глобальный экземпляр логгера безопасности
security_logger_instance = SecurityLogger()


# Удобные функции для быстрого использования
def log_security_event(event_type: str, 
                      request: Optional[HttpRequest] = None,
                      user: Optional[User] = None,
                      severity: str = 'MEDIUM',
                      description: Optional[str] = None,
                      additional_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Быстрое логирование события безопасности.
    
    Args:
        event_type: Тип события
        request: HTTP запрос
        user: Пользователь
        severity: Уровень критичности
        description: Описание события
        additional_data: Дополнительные данные
    """
    ip_address = None
    user_agent = None
    request_path = None
    
    if request:
        ip_address = security_logger_instance._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT')
        request_path = request.path
        
        if not user and hasattr(request, 'user'):
            user = request.user
    
    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request_path,
        description=description,
        additional_data=additional_data
    )
    
    security_logger_instance.log_event(event)


def log_login_attempt(request: HttpRequest, username: str, success: bool, reason: Optional[str] = None) -> None:
    """
    Логирует попытку авторизации.
    """
    security_logger_instance.log_login_attempt(request, username, success, reason)


def log_permission_denied(request: HttpRequest, user: Optional[User] = None, resource: Optional[str] = None) -> None:
    """
    Логирует отказ в доступе.
    """
    security_logger_instance.log_permission_denied(request, user, resource)


def log_suspicious_request(request: HttpRequest, attack_type: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Логирует подозрительный запрос.
    """
    security_logger_instance.log_suspicious_request(request, attack_type, details)


def log_rate_limit_exceeded(request: HttpRequest, limit_type: str, current_count: int, limit: int) -> None:
    """
    Логирует превышение лимита запросов.
    """
    security_logger_instance.log_rate_limit_exceeded(request, limit_type, current_count, limit)


def get_security_stats(hours: int = 24) -> Dict[str, Any]:
    """
    Получает статистику безопасности.
    """
    return security_logger_instance.get_security_stats(hours)


def get_recent_security_events(limit: int = 100, **filters) -> List[Dict[str, Any]]:
    """
    Получает последние события безопасности.
    """
    return security_logger_instance.get_recent_events(limit, **filters)