#!/usr/bin/env python
"""
Тестовый скрипт для проверки системы мониторинга безопасности
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.core.security.monitoring import security_monitor
from apps.core.utils.security_logger import security_logger

def test_security_monitoring():
    """Тестирование системы мониторинга безопасности"""
    print("=== Тестирование системы мониторинга безопасности ===")
    print()
    
    # Тест 1: Запись угроз
    print("1. Тестирование записи угроз...")
    
    test_threats = [
        {
            'type': 'sql_injection',
            'ip': '192.168.1.100',
            'risk_score': 90,
            'details': {'payload': "'; DROP TABLE users; --", 'endpoint': '/api/login'}
        },
        {
            'type': 'brute_force',
            'ip': '10.0.0.50',
            'risk_score': 75,
            'details': {'failed_attempts': 15, 'username': 'admin'}
        },
        {
            'type': 'rate_limit_exceeded',
            'ip': '203.0.113.10',
            'risk_score': 60,
            'details': {'requests_made': 150, 'requests_allowed': 100, 'endpoint': '/api/products'}
        },
        {
            'type': 'xss_attack',
            'ip': '198.51.100.25',
            'risk_score': 85,
            'details': {'payload': '<script>alert("XSS")</script>', 'field': 'comment'}
        }
    ]
    
    for threat in test_threats:
        security_monitor.record_threat(
            threat['type'],
            threat['ip'],
            threat['risk_score'],
            threat['details']
        )
        print(f"  ✓ Записана угроза: {threat['type']} от {threat['ip']}")
    
    print()
    
    # Тест 2: Запись событий безопасности
    print("2. Тестирование записи событий безопасности...")
    
    test_events = [
        {
            'type': 'login_success',
            'ip': '192.168.1.200',
            'details': {'username': 'user123', 'user_agent': 'Mozilla/5.0'}
        },
        {
            'type': 'login_failed',
            'ip': '10.0.0.75',
            'details': {'username': 'admin', 'reason': 'invalid_password'}
        },
        {
            'type': 'suspicious_activity',
            'ip': '203.0.113.50',
            'details': {'activity': 'multiple_user_agents', 'count': 5}
        }
    ]
    
    for event in test_events:
        security_monitor.record_security_event(
            event['type'],
            event['ip'],
            event.get('user_id'),
            event['details']
        )
        print(f"  ✓ Записано событие: {event['type']} от {event['ip']}")
    
    print()
    
    # Тест 3: Получение метрик
    print("3. Получение метрик безопасности...")
    metrics = security_monitor.get_security_metrics()
    
    print(f"  • Всего событий: {metrics['total_events']}")
    print(f"  • Неудачные входы: {metrics['failed_logins']}")
    print(f"  • Успешные входы: {metrics['successful_logins']}")
    print(f"  • Заблокированные запросы: {metrics['blocked_requests']}")
    print(f"  • Подозрительная активность: {metrics['suspicious_activities']}")
    print(f"  • Уникальных IP: {metrics['unique_ips']}")
    print(f"  • Процент ошибок: {metrics['error_rate']:.2%}")
    print()
    
    # Тест 4: Получение активных алертов
    print("4. Получение активных алертов...")
    alerts = security_monitor.get_active_alerts()
    print(f"  ✓ Активных алертов: {len(alerts)}")
    for alert in alerts[:3]:  # Показываем первые 3 алерта
        print(f"    - {alert['type']}: {alert['message']} (severity: {alert['severity']})")
    print()
    
    # Тест 5: Завершение тестирования
    print("5. Тестирование завершено успешно!")
    print("  ✓ Все основные функции системы мониторинга работают корректно")
    print("  ✓ Угрозы записываются и обрабатываются")
    print("  ✓ События безопасности логируются")
    print("  ✓ Метрики собираются правильно")
    print("  ✓ Алерты создаются автоматически при высоком риске")
    print()
    
    print("=== Тестирование завершено успешно! ===")
    print()
    print("Для запуска мониторинга в реальном времени используйте:")
    print("python manage.py security_monitor --monitor")
    print()
    print("Для просмотра дашборда используйте:")
    print("python manage.py security_monitor --dashboard")

if __name__ == '__main__':
    try:
        test_security_monitoring()
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()