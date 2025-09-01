"""Security Monitoring Configuration

This module contains configuration settings for the security monitoring system.
"""

from typing import Dict, List, Any
from datetime import timedelta

# Threat Detection Configuration
THREAT_DETECTION_CONFIG = {
    # Brute Force Detection
    'brute_force': {
        'enabled': True,
        'max_attempts': 5,
        'time_window': 300,  # 5 minutes
        'block_duration': 3600,  # 1 hour
        'severity': 'high'
    },
    
    # Rate Limit Abuse Detection
    'rate_abuse': {
        'enabled': True,
        'max_violations': 10,
        'time_window': 600,  # 10 minutes
        'block_duration': 1800,  # 30 minutes
        'severity': 'medium'
    },
    
    # SQL Injection Detection
    'sql_injection': {
        'enabled': True,
        'patterns': [
            r'(union|select|insert|update|delete|drop|create|alter)\s+',
            r'(or|and)\s+\d+\s*=\s*\d+',
            r'(\';|\"\s*;|\s*;\s*--)',
            r'(exec|execute|sp_|xp_)',
            r'(information_schema|sysobjects|syscolumns)'
        ],
        'severity': 'critical',
        'block_immediately': True
    },
    
    # XSS Detection
    'xss': {
        'enabled': True,
        'patterns': [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ],
        'severity': 'high',
        'block_immediately': False
    },
    
    # Path Traversal Detection
    'path_traversal': {
        'enabled': True,
        'patterns': [
            r'\.\./+',
            r'\\\.\.\\',
            r'%2e%2e%2f',
            r'%2e%2e\\',
            r'\.\.%2f'
        ],
        'severity': 'high',
        'block_immediately': True
    },
    
    # Suspicious User Agent Detection
    'suspicious_user_agent': {
        'enabled': True,
        'patterns': [
            r'sqlmap',
            r'nikto',
            r'nmap',
            r'masscan',
            r'nessus',
            r'openvas',
            r'w3af',
            r'burp',
            r'owasp',
            r'dirbuster',
            r'gobuster'
        ],
        'severity': 'medium',
        'block_immediately': False
    }
}

# Security Metrics Configuration
METRICS_CONFIG = {
    'collection_interval': 60,  # seconds
    'retention_period': 7 * 24 * 3600,  # 7 days in seconds
    'cache_timeout': 300,  # 5 minutes
    
    # Metrics to collect
    'metrics': [
        'total_requests',
        'unique_ips',
        'failed_logins',
        'rate_limit_violations',
        'suspicious_requests',
        'blocked_ips',
        'auth_failures',
        'permission_denials',
        'errors_400',
        'errors_401',
        'errors_403',
        'errors_404',
        'errors_500'
    ]
}

# Alert Configuration
ALERT_CONFIG = {
    'email_alerts': {
        'enabled': True,
        'recipients': [],  # Will be populated from settings
        'rate_limit': 300,  # Max one email per 5 minutes per alert type
        'templates': {
            'threat_detected': 'security/threat_alert.html',
            'ip_blocked': 'security/ip_blocked.html',
            'system_health': 'security/health_alert.html'
        }
    },
    
    'webhook_alerts': {
        'enabled': False,
        'url': None,
        'timeout': 10,
        'retry_attempts': 3
    },
    
    'log_alerts': {
        'enabled': True,
        'log_level': 'WARNING',
        'include_details': True
    }
}

# IP Blocking Configuration
BLOCKING_CONFIG = {
    'auto_block': {
        'enabled': True,
        'threshold_score': 100,  # Cumulative threat score
        'default_duration': 3600,  # 1 hour
        'max_duration': 24 * 3600,  # 24 hours
        'escalation_factor': 2  # Multiply duration for repeat offenders
    },
    
    'whitelist': {
        'enabled': True,
        'ips': [
            '127.0.0.1',
            '::1',
            # Add your trusted IPs here
        ],
        'networks': [
            '10.0.0.0/8',
            '172.16.0.0/12',
            '192.168.0.0/16'
        ]
    },
    
    'blacklist': {
        'enabled': True,
        'ips': [],  # Permanently blocked IPs
        'auto_update': False,
        'sources': []  # External blacklist sources
    }
}

# Monitoring Configuration
MONITORING_CONFIG = {
    'real_time': {
        'enabled': True,
        'update_interval': 5,  # seconds
        'max_events_display': 100
    },
    
    'health_checks': {
        'enabled': True,
        'interval': 300,  # 5 minutes
        'thresholds': {
            'error_rate': 10,  # percent
            'failed_login_rate': 20,  # percent
            'blocked_ip_count': 50,
            'threat_score': 500
        }
    },
    
    'reporting': {
        'enabled': True,
        'daily_reports': True,
        'weekly_reports': True,
        'export_formats': ['json', 'csv'],
        'retention_days': 30
    }
}

# Cache Configuration
CACHE_CONFIG = {
    'prefixes': {
        'metrics': 'security_metrics',
        'threats': 'security_threats',
        'blocked_ips': 'blocked_ip',
        'rate_limits': 'rate_limit',
        'alerts': 'security_alerts'
    },
    
    'timeouts': {
        'metrics': 300,  # 5 minutes
        'threats': 1800,  # 30 minutes
        'blocked_ips': 3600,  # 1 hour
        'rate_limits': 60,  # 1 minute
        'alerts': 300  # 5 minutes
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    'security_logger': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': ['file', 'console'],
        'file_path': 'logs/security.log',
        'max_bytes': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5
    },
    
    'audit_logger': {
        'level': 'INFO',
        'format': '%(asctime)s - AUDIT - %(message)s',
        'handlers': ['file'],
        'file_path': 'logs/security_audit.log',
        'max_bytes': 50 * 1024 * 1024,  # 50MB
        'backup_count': 10
    }
}

# API Endpoints Configuration
API_ENDPOINTS_CONFIG = {
    'critical_endpoints': [
        '/api/accounts/login/',
        '/api/accounts/register/',
        '/api/accounts/password/reset/',
        '/api/accounts/password/change/',
        '/api/payments/',
        '/admin/login/'
    ],
    
    'sensitive_endpoints': [
        '/api/accounts/profile/',
        '/api/accounts/settings/',
        '/api/orders/',
        '/api/transactions/'
    ],
    
    'public_endpoints': [
        '/api/products/',
        '/api/categories/',
        '/api/health/',
        '/api/status/'
    ]
}

# Security Headers Configuration
SECURITY_HEADERS_CONFIG = {
    'required_headers': {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    },
    
    'csp_policy': {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'"],  # Remove unsafe-inline in production
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", 'data:', 'https:'],
        'font-src': ["'self'"],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"]
    }
}

# Feature Flags
FEATURE_FLAGS = {
    'threat_detection': True,
    'auto_blocking': True,
    'email_alerts': True,
    'real_time_monitoring': True,
    'audit_logging': True,
    'metrics_collection': True,
    'health_monitoring': True,
    'security_headers': True,
    'rate_limiting': True,
    'input_validation': True
}

# Development/Testing Configuration
DEVELOPMENT_CONFIG = {
    'debug_mode': False,
    'test_mode': False,
    'mock_alerts': False,
    'reduced_thresholds': False,
    'verbose_logging': False
}

def get_config(section: str) -> Dict[str, Any]:
    """Get configuration for a specific section"""
    config_map = {
        'threats': THREAT_DETECTION_CONFIG,
        'metrics': METRICS_CONFIG,
        'alerts': ALERT_CONFIG,
        'blocking': BLOCKING_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'cache': CACHE_CONFIG,
        'logging': LOGGING_CONFIG,
        'api': API_ENDPOINTS_CONFIG,
        'headers': SECURITY_HEADERS_CONFIG,
        'features': FEATURE_FLAGS,
        'development': DEVELOPMENT_CONFIG
    }
    
    return config_map.get(section, {})

def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled"""
    return FEATURE_FLAGS.get(feature, False)

def get_threat_config(threat_type: str) -> Dict[str, Any]:
    """Get configuration for a specific threat type"""
    return THREAT_DETECTION_CONFIG.get(threat_type, {})

def get_cache_key(prefix: str, identifier: str) -> str:
    """Generate cache key with proper prefix"""
    cache_prefix = CACHE_CONFIG['prefixes'].get(prefix, prefix)
    return f"{cache_prefix}:{identifier}"

def get_cache_timeout(category: str) -> int:
    """Get cache timeout for a category"""
    return CACHE_CONFIG['timeouts'].get(category, 300)