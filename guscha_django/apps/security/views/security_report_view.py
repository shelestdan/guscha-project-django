from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
import json
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db import transaction

from ..models import SecurityReport, ThreatDetection
from ..services.security_analysis_service import SecurityAnalysisService
from ..utils.rate_limiting import RateLimiter

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SecurityReportView(View):
    """
    API endpoint для получения отчетов о безопасности от фронтенда
    """
    
    def __init__(self):
        super().__init__()
        self.security_service = SecurityAnalysisService()
        self.rate_limiter = RateLimiter()
    
    def post(self, request):
        """
        Обрабатывает отчет о безопасности от клиента
        """
        try:
            # Проверка rate limiting
            client_ip = self.get_client_ip(request)
            if not self.rate_limiter.is_allowed(f"security_report:{client_ip}", limit=10, window=60):
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': 'Слишком много запросов. Попробуйте позже.'
                }, status=429)
            
            # Парсинг данных
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': 'Invalid JSON',
                    'message': 'Некорректный формат данных'
                }, status=400)
            
            # Валидация обязательных полей
            required_fields = ['timestamp', 'sessionId', 'risk', 'fingerprint', 'behavior']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return JsonResponse({
                    'error': 'Missing required fields',
                    'message': f'Отсутствуют обязательные поля: {", ".join(missing_fields)}'
                }, status=400)
            
            # Дополнительная информация о запросе
            request_info = {
                'ip_address': client_ip,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referer': request.META.get('HTTP_REFERER', ''),
                'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
                'x_forwarded_for': request.META.get('HTTP_X_FORWARDED_FOR', ''),
                'x_real_ip': request.META.get('HTTP_X_REAL_IP', '')
            }
            
            # Анализ безопасности
            analysis_result = self.security_service.analyze_security_data(data)
            
            # Сохранение отчета в базу данных
            with transaction.atomic():
                security_report = self.save_security_report(data, request_info, analysis_result)
                
                # Если обнаружена угроза, создаем запись об угрозе
                if analysis_result.get('threat_detected'):
                    self.create_threat_detection(security_report, analysis_result)
            
            # Логирование
            self.log_security_event(data, request_info, analysis_result)
            
            # Ответ клиенту
            response_data = {
                'status': 'success',
                'message': 'Отчет о безопасности обработан',
                'report_id': security_report.id,
                'analysis': {
                    'risk_level': analysis_result.get('risk_level'),
                    'threat_detected': analysis_result.get('threat_detected', False),
                    'recommended_action': analysis_result.get('recommended_action'),
                    'confidence': analysis_result.get('confidence', 0)
                }
            }
            
            # Если требуется блокировка, добавляем соответствующую информацию
            if analysis_result.get('should_block'):
                response_data['block_required'] = True
                response_data['block_reason'] = analysis_result.get('block_reason')
                response_data['block_duration'] = analysis_result.get('block_duration')
            
            return JsonResponse(response_data, status=201)
            
        except Exception as e:
            logger.error(f"Ошибка обработки отчета о безопасности: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'Internal server error',
                'message': 'Внутренняя ошибка сервера'
            }, status=500)
    
    def get_client_ip(self, request):
        """
        Получает IP адрес клиента с учетом прокси
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def save_security_report(self, data, request_info, analysis_result):
        """
        Сохраняет отчет о безопасности в базу данных
        """
        try:
            security_report = SecurityReport.objects.create(
                session_id=data['sessionId'],
                ip_address=request_info['ip_address'],
                user_agent=request_info['user_agent'],
                
                # Данные fingerprinting
                fingerprint_hash=data['fingerprint'].get('hash'),
                fingerprint_confidence=data['fingerprint'].get('confidence', 0),
                browser_info=data['fingerprint'].get('components', {}).get('browser', {}),
                screen_info=data['fingerprint'].get('components', {}).get('screen', {}),
                timezone_info=data['fingerprint'].get('components', {}).get('timezone', {}),
                automation_detected=bool(
                    data['fingerprint'].get('components', {}).get('automation', {}).get('webdriver') or
                    data['fingerprint'].get('components', {}).get('automation', {}).get('phantom') or
                    data['fingerprint'].get('components', {}).get('automation', {}).get('selenium')
                ),
                
                # Данные поведенческого анализа
                behavior_is_human=data['behavior'].get('isHuman'),
                behavior_confidence=data['behavior'].get('confidence', 0),
                behavior_risk_score=data['behavior'].get('riskScore', 0),
                total_interactions=data['behavior'].get('interactions', 0),
                suspicious_patterns_count=len(data['behavior'].get('patterns', [])),
                high_risk_patterns_count=len([
                    p for p in data['behavior'].get('patterns', []) 
                    if p.get('severity') == 'high'
                ]),
                
                # Общий анализ риска
                overall_risk_score=data['risk'].get('overall', 0),
                risk_level=data['risk'].get('level', 'unknown'),
                
                # Результаты анализа
                threat_detected=analysis_result.get('threat_detected', False),
                recommended_action=analysis_result.get('recommended_action', 'allow'),
                analysis_confidence=analysis_result.get('confidence', 0),
                
                # Дополнительные данные
                raw_data=data,
                request_metadata=request_info
            )
            
            return security_report
            
        except Exception as e:
            logger.error(f"Ошибка сохранения отчета о безопасности: {str(e)}", exc_info=True)
            raise
    
    def create_threat_detection(self, security_report, analysis_result):
        """
        Создает запись об обнаруженной угрозе
        """
        try:
            threat_types = analysis_result.get('threat_types', [])
            threat_severity = analysis_result.get('threat_severity', 'medium')
            
            threat_detection = ThreatDetection.objects.create(
                security_report=security_report,
                threat_type=', '.join(threat_types) if threat_types else 'unknown',
                severity=threat_severity,
                confidence=analysis_result.get('confidence', 0),
                description=analysis_result.get('threat_description', ''),
                recommended_action=analysis_result.get('recommended_action', 'monitor'),
                metadata={
                    'analysis_details': analysis_result,
                    'detection_timestamp': datetime.now().isoformat()
                }
            )
            
            # Отправляем уведомление если угроза критическая
            if threat_severity in ['high', 'critical']:
                self.send_threat_notification(threat_detection)
            
            return threat_detection
            
        except Exception as e:
            logger.error(f"Ошибка создания записи об угрозе: {str(e)}", exc_info=True)
            raise
    
    def send_threat_notification(self, threat_detection):
        """
        Отправляет уведомление о критической угрозе
        """
        try:
            # Здесь можно добавить отправку email, Slack, Telegram и т.д.
            logger.critical(
                f"КРИТИЧЕСКАЯ УГРОЗА ОБНАРУЖЕНА: {threat_detection.threat_type} "
                f"от IP {threat_detection.security_report.ip_address}"
            )
            
            # Можно добавить интеграцию с системами мониторинга
            # например, отправка в Sentry, DataDog и т.д.
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об угрозе: {str(e)}", exc_info=True)
    
    def log_security_event(self, data, request_info, analysis_result):
        """
        Логирует событие безопасности
        """
        log_data = {
            'event_type': 'security_report',
            'session_id': data['sessionId'],
            'ip_address': request_info['ip_address'],
            'risk_score': data['risk'].get('overall', 0),
            'risk_level': data['risk'].get('level', 'unknown'),
            'threat_detected': analysis_result.get('threat_detected', False),
            'automation_detected': bool(
                data['fingerprint'].get('components', {}).get('automation', {}).get('webdriver') or
                data['fingerprint'].get('components', {}).get('automation', {}).get('phantom') or
                data['fingerprint'].get('components', {}).get('automation', {}).get('selenium')
            ),
            'behavior_human': data['behavior'].get('isHuman'),
            'total_interactions': data['behavior'].get('interactions', 0)
        }
        
        if analysis_result.get('threat_detected'):
            logger.warning(f"Угроза безопасности: {log_data}")
        else:
            logger.info(f"Отчет о безопасности: {log_data}")


@method_decorator(csrf_exempt, name='dispatch')
class SecurityStatsView(View):
    """
    API endpoint для получения статистики безопасности
    """
    
    @require_http_methods(["GET"])
    def get(self, request):
        """
        Возвращает статистику безопасности
        """
        try:
            # Проверка прав доступа (только для администраторов)
            if not request.user.is_authenticated or not request.user.is_staff:
                return JsonResponse({
                    'error': 'Access denied',
                    'message': 'Недостаточно прав доступа'
                }, status=403)
            
            # Параметры запроса
            hours = int(request.GET.get('hours', 24))
            since = datetime.now() - timedelta(hours=hours)
            
            # Кэширование результатов
            cache_key = f'security_stats_{hours}h'
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return JsonResponse(cached_stats)
            
            # Получение статистики
            stats = {
                'period': f'{hours} hours',
                'total_reports': SecurityReport.objects.filter(created_at__gte=since).count(),
                'threats_detected': ThreatDetection.objects.filter(
                    created_at__gte=since
                ).count(),
                'automation_detected': SecurityReport.objects.filter(
                    created_at__gte=since,
                    automation_detected=True
                ).count(),
                'high_risk_reports': SecurityReport.objects.filter(
                    created_at__gte=since,
                    risk_level__in=['high', 'critical']
                ).count(),
                'unique_ips': SecurityReport.objects.filter(
                    created_at__gte=since
                ).values('ip_address').distinct().count(),
                'risk_distribution': self.get_risk_distribution(since),
                'threat_types': self.get_threat_types_distribution(since),
                'top_suspicious_ips': self.get_top_suspicious_ips(since)
            }
            
            # Кэшируем на 5 минут
            cache.set(cache_key, stats, 300)
            
            return JsonResponse(stats)
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики безопасности: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'Internal server error',
                'message': 'Внутренняя ошибка сервера'
            }, status=500)
    
    def get_risk_distribution(self, since):
        """
        Получает распределение по уровням риска
        """
        from django.db.models import Count
        
        distribution = SecurityReport.objects.filter(
            created_at__gte=since
        ).values('risk_level').annotate(
            count=Count('id')
        ).order_by('risk_level')
        
        return {item['risk_level']: item['count'] for item in distribution}
    
    def get_threat_types_distribution(self, since):
        """
        Получает распределение по типам угроз
        """
        from django.db.models import Count
        
        distribution = ThreatDetection.objects.filter(
            created_at__gte=since
        ).values('threat_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return {item['threat_type']: item['count'] for item in distribution}
    
    def get_top_suspicious_ips(self, since, limit=10):
        """
        Получает топ подозрительных IP адресов
        """
        from django.db.models import Count, Avg
        
        suspicious_ips = SecurityReport.objects.filter(
            created_at__gte=since,
            overall_risk_score__gte=50
        ).values('ip_address').annotate(
            report_count=Count('id'),
            avg_risk_score=Avg('overall_risk_score'),
            threat_count=Count('threatdetection')
        ).order_by('-avg_risk_score', '-report_count')[:limit]
        
        return list(suspicious_ips)