from celery.schedules import crontab
from django.conf import settings
from .settings.security_settings import get_security_setting

# Настройки периодических задач для мониторинга безопасности
SECURITY_CELERY_BEAT_SCHEDULE = {
    # Мониторинг безопасности каждые 5 минут
    'security-monitoring': {
        'task': 'apps.security.tasks.run_security_monitoring',
        'schedule': crontab(minute='*/5'),  # Каждые 5 минут
        'options': {
            'expires': 300,  # Задача истекает через 5 минут
            'retry': True,
            'retry_policy': {
                'max_retries': 3,
                'interval_start': 60,
                'interval_step': 60,
                'interval_max': 300,
            }
        }
    },
    
    # Очистка старых данных каждый день в 2:00
    'security-cleanup': {
        'task': 'apps.security.tasks.cleanup_old_security_data',
        'schedule': crontab(hour=2, minute=0),  # Каждый день в 2:00
        'options': {
            'expires': 3600,  # Задача истекает через час
            'retry': True,
            'retry_policy': {
                'max_retries': 2,
                'interval_start': 300,
                'interval_step': 300,
                'interval_max': 900,
            }
        }
    },
    
    # Анализ трендов безопасности каждые 6 часов
    'security-trends-analysis': {
        'task': 'apps.security.tasks.analyze_security_trends',
        'schedule': crontab(minute=0, hour='*/6'),  # Каждые 6 часов
        'options': {
            'expires': 1800,  # Задача истекает через 30 минут
            'retry': True,
            'retry_policy': {
                'max_retries': 3,
                'interval_start': 120,
                'interval_step': 120,
                'interval_max': 600,
            }
        }
    },
    
    # Обновление данных об угрозах каждый час
    'threat-intelligence-update': {
        'task': 'apps.security.tasks.update_threat_intelligence',
        'schedule': crontab(minute=30),  # Каждый час в 30 минут
        'options': {
            'expires': 1800,  # Задача истекает через 30 минут
            'retry': True,
            'retry_policy': {
                'max_retries': 2,
                'interval_start': 180,
                'interval_step': 180,
                'interval_max': 600,
            }
        }
    },
    
    # Ежедневный отчет по безопасности в 8:00
    'daily-security-report': {
        'task': 'apps.security.tasks.generate_security_report',
        'schedule': crontab(hour=8, minute=0),  # Каждый день в 8:00
        'options': {
            'expires': 3600,  # Задача истекает через час
            'retry': True,
            'retry_policy': {
                'max_retries': 2,
                'interval_start': 300,
                'interval_step': 300,
                'interval_max': 900,
            }
        }
    }
}

# Настройки маршрутизации задач
SECURITY_CELERY_ROUTES = {
    'apps.security.tasks.run_security_monitoring': {
        'queue': 'security_monitoring',
        'routing_key': 'security.monitoring'
    },
    'apps.security.tasks.cleanup_old_security_data': {
        'queue': 'security_maintenance',
        'routing_key': 'security.maintenance'
    },
    'apps.security.tasks.analyze_security_trends': {
        'queue': 'security_analysis',
        'routing_key': 'security.analysis'
    },
    'apps.security.tasks.update_threat_intelligence': {
        'queue': 'security_intelligence',
        'routing_key': 'security.intelligence'
    },
    'apps.security.tasks.generate_security_report': {
        'queue': 'security_reports',
        'routing_key': 'security.reports'
    }
}

# Настройки приоритетов задач
SECURITY_TASK_PRIORITIES = {
    'apps.security.tasks.run_security_monitoring': 8,  # Высокий приоритет
    'apps.security.tasks.cleanup_old_security_data': 3,  # Низкий приоритет
    'apps.security.tasks.analyze_security_trends': 5,  # Средний приоритет
    'apps.security.tasks.update_threat_intelligence': 6,  # Выше среднего
    'apps.security.tasks.generate_security_report': 4  # Ниже среднего
}

# Настройки ограничений скорости
SECURITY_TASK_ANNOTATIONS = {
    'apps.security.tasks.run_security_monitoring': {
        'rate_limit': '12/m',  # Максимум 12 раз в минуту
        'time_limit': 300,  # Максимум 5 минут на выполнение
        'soft_time_limit': 240,  # Мягкий лимит 4 минуты
    },
    'apps.security.tasks.cleanup_old_security_data': {
        'rate_limit': '1/h',  # Максимум раз в час
        'time_limit': 1800,  # Максимум 30 минут на выполнение
        'soft_time_limit': 1500,  # Мягкий лимит 25 минут
    },
    'apps.security.tasks.analyze_security_trends': {
        'rate_limit': '4/h',  # Максимум 4 раза в час
        'time_limit': 900,  # Максимум 15 минут на выполнение
        'soft_time_limit': 720,  # Мягкий лимит 12 минут
    },
    'apps.security.tasks.update_threat_intelligence': {
        'rate_limit': '1/m',  # Максимум раз в минуту
        'time_limit': 600,  # Максимум 10 минут на выполнение
        'soft_time_limit': 480,  # Мягкий лимит 8 минут
    },
    'apps.security.tasks.generate_security_report': {
        'rate_limit': '1/d',  # Максимум раз в день
        'time_limit': 1200,  # Максимум 20 минут на выполнение
        'soft_time_limit': 900,  # Мягкий лимит 15 минут
    }
}


def get_security_celery_config():
    """
    Возвращает конфигурацию Celery для системы безопасности
    """
    # Проверяем, включен ли мониторинг
    monitoring_enabled = get_security_setting('SECURITY_MONITORING_ENABLED', True)
    
    config = {
        'beat_schedule': {},
        'task_routes': SECURITY_CELERY_ROUTES.copy(),
        'task_annotations': SECURITY_TASK_ANNOTATIONS.copy()
    }
    
    if monitoring_enabled:
        # Добавляем задачи мониторинга
        config['beat_schedule'].update(SECURITY_CELERY_BEAT_SCHEDULE)
        
        # Настраиваем приоритеты
        for task, priority in SECURITY_TASK_PRIORITIES.items():
            if task not in config['task_annotations']:
                config['task_annotations'][task] = {}
            config['task_annotations'][task]['priority'] = priority
    
    # Настройки из конфигурации безопасности
    monitoring_interval = get_security_setting('SECURITY_MONITORING_INTERVAL_MINUTES', 5)
    cleanup_hour = get_security_setting('SECURITY_CLEANUP_HOUR', 2)
    report_hour = get_security_setting('SECURITY_REPORT_HOUR', 8)
    
    # Обновляем расписание на основе настроек
    if 'security-monitoring' in config['beat_schedule']:
        config['beat_schedule']['security-monitoring']['schedule'] = crontab(
            minute=f'*/{monitoring_interval}'
        )
    
    if 'security-cleanup' in config['beat_schedule']:
        config['beat_schedule']['security-cleanup']['schedule'] = crontab(
            hour=cleanup_hour, minute=0
        )
    
    if 'daily-security-report' in config['beat_schedule']:
        config['beat_schedule']['daily-security-report']['schedule'] = crontab(
            hour=report_hour, minute=0
        )
    
    return config


def update_celery_config(celery_app):
    """
    Обновляет конфигурацию Celery для включения задач безопасности
    """
    security_config = get_security_celery_config()
    
    # Обновляем beat_schedule
    current_beat_schedule = getattr(celery_app.conf, 'beat_schedule', {})
    current_beat_schedule.update(security_config['beat_schedule'])
    celery_app.conf.beat_schedule = current_beat_schedule
    
    # Обновляем task_routes
    current_task_routes = getattr(celery_app.conf, 'task_routes', {})
    current_task_routes.update(security_config['task_routes'])
    celery_app.conf.task_routes = current_task_routes
    
    # Обновляем task_annotations
    current_task_annotations = getattr(celery_app.conf, 'task_annotations', {})
    for task, annotations in security_config['task_annotations'].items():
        if task not in current_task_annotations:
            current_task_annotations[task] = {}
        current_task_annotations[task].update(annotations)
    celery_app.conf.task_annotations = current_task_annotations
    
    return celery_app


# Дополнительные настройки для разработки и отладки
if getattr(settings, 'DEBUG', False):
    # В режиме отладки запускаем мониторинг чаще
    SECURITY_CELERY_BEAT_SCHEDULE['security-monitoring']['schedule'] = crontab(minute='*/2')
    
    # Добавляем задачу для тестирования
    SECURITY_CELERY_BEAT_SCHEDULE['security-test-monitoring'] = {
        'task': 'apps.security.tasks.run_security_monitoring',
        'schedule': crontab(minute='*/10'),  # Каждые 10 минут
        'kwargs': {'test_mode': True},
        'options': {
            'expires': 300,
            'retry': False
        }
    }


# Настройки для мониторинга производительности задач
SECURITY_MONITORING_CONFIG = {
    'task_success_rate_threshold': 0.95,  # Минимальный процент успешных задач
    'task_avg_duration_threshold': 60,  # Максимальная средняя длительность в секундах
    'task_failure_alert_threshold': 5,  # Количество неудач для отправки алерта
    'queue_length_threshold': 100,  # Максимальная длина очереди
    'worker_availability_threshold': 0.8  # Минимальный процент доступных воркеров
}