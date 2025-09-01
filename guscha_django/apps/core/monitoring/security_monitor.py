"""Security Monitoring and Alerting System

This module provides comprehensive security monitoring, threat detection,
and automated alerting capabilities for the Django application.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from django.core.cache import cache
from django.conf import settings
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from apps.core.validation.security_logging import SecurityLogger


@dataclass
class SecurityThreat:
    """Represents a detected security threat"""
    threat_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    source_ip: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[int] = None
    endpoint: Optional[str] = None
    count: int = 1


@dataclass
class SecurityMetrics:
    """Security metrics for monitoring"""
    failed_logins: int = 0
    rate_limit_violations: int = 0
    suspicious_requests: int = 0
    blocked_ips: int = 0
    csrf_failures: int = 0
    permission_denials: int = 0
    total_requests: int = 0
    unique_ips: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class ThreatDetector:
    """Advanced threat detection engine"""
    
    def __init__(self):
        self.failed_login_threshold = getattr(settings, 'SECURITY_FAILED_LOGIN_THRESHOLD', 5)
        self.suspicious_request_threshold = getattr(settings, 'SECURITY_SUSPICIOUS_THRESHOLD', 10)
        self.rate_limit_threshold = getattr(settings, 'SECURITY_RATE_LIMIT_THRESHOLD', 20)
        self.time_window = getattr(settings, 'SECURITY_TIME_WINDOW', 300)  # 5 minutes
        
        # In-memory threat tracking
        self.ip_activity = defaultdict(lambda: deque(maxlen=100))
        self.user_activity = defaultdict(lambda: deque(maxlen=50))
        self.endpoint_activity = defaultdict(lambda: deque(maxlen=200))
        self.lock = Lock()
    
    def detect_brute_force(self, ip: str, user_id: Optional[int] = None) -> Optional[SecurityThreat]:
        """Detect brute force attacks"""
        current_time = time.time()
        
        with self.lock:
            # Track IP-based attempts
            self.ip_activity[ip].append(current_time)
            recent_attempts = [t for t in self.ip_activity[ip] if current_time - t < self.time_window]
            
            if len(recent_attempts) >= self.failed_login_threshold:
                return SecurityThreat(
                    threat_type='brute_force_attack',
                    severity='high',
                    source_ip=ip,
                    user_agent='',
                    timestamp=datetime.now(),
                    details={
                        'attempts_count': len(recent_attempts),
                        'time_window': self.time_window,
                        'user_id': user_id
                    },
                    count=len(recent_attempts)
                )
        return None
    
    def detect_rate_limit_abuse(self, ip: str, endpoint: str) -> Optional[SecurityThreat]:
        """Detect rate limit abuse patterns"""
        cache_key = f'rate_abuse:{ip}:{endpoint}'
        current_violations = cache.get(cache_key, 0)
        
        if current_violations >= self.rate_limit_threshold:
            return SecurityThreat(
                threat_type='rate_limit_abuse',
                severity='medium',
                source_ip=ip,
                user_agent='',
                timestamp=datetime.now(),
                endpoint=endpoint,
                details={
                    'violations_count': current_violations,
                    'endpoint': endpoint
                },
                count=current_violations
            )
        return None
    
    def detect_suspicious_patterns(self, request: HttpRequest) -> List[SecurityThreat]:
        """Detect various suspicious patterns"""
        threats = []
        ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # SQL Injection patterns
        if self._detect_sql_injection(request):
            threats.append(SecurityThreat(
                threat_type='sql_injection_attempt',
                severity='critical',
                source_ip=ip,
                user_agent=user_agent,
                timestamp=datetime.now(),
                details={'path': request.path, 'method': request.method}
            ))
        
        # XSS patterns
        if self._detect_xss_attempt(request):
            threats.append(SecurityThreat(
                threat_type='xss_attempt',
                severity='high',
                source_ip=ip,
                user_agent=user_agent,
                timestamp=datetime.now(),
                details={'path': request.path, 'method': request.method}
            ))
        
        # Path traversal
        if self._detect_path_traversal(request):
            threats.append(SecurityThreat(
                threat_type='path_traversal_attempt',
                severity='high',
                source_ip=ip,
                user_agent=user_agent,
                timestamp=datetime.now(),
                details={'path': request.path}
            ))
        
        # Suspicious user agents
        if self._detect_suspicious_user_agent(user_agent):
            threats.append(SecurityThreat(
                threat_type='suspicious_user_agent',
                severity='low',
                source_ip=ip,
                user_agent=user_agent,
                timestamp=datetime.now(),
                details={'user_agent': user_agent}
            ))
        
        return threats
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def _detect_sql_injection(self, request: HttpRequest) -> bool:
        """Detect SQL injection patterns"""
        sql_patterns = [
            "' OR '1'='1", "' OR 1=1", "'; DROP TABLE", "'; DELETE FROM",
            "UNION SELECT", "' UNION", "/*", "*/", "@@version",
            "information_schema", "sysobjects", "syscolumns"
        ]
        
        query_string = request.GET.urlencode().lower()
        post_data = str(request.POST).lower() if hasattr(request, 'POST') else ''
        path = request.path.lower()
        
        combined_data = f"{query_string} {post_data} {path}"
        
        return any(pattern.lower() in combined_data for pattern in sql_patterns)
    
    def _detect_xss_attempt(self, request: HttpRequest) -> bool:
        """Detect XSS attempt patterns"""
        xss_patterns = [
            "<script", "javascript:", "onload=", "onerror=", "onclick=",
            "<iframe", "<object", "<embed", "eval(", "alert(",
            "document.cookie", "window.location"
        ]
        
        query_string = request.GET.urlencode().lower()
        post_data = str(request.POST).lower() if hasattr(request, 'POST') else ''
        
        combined_data = f"{query_string} {post_data}"
        
        return any(pattern.lower() in combined_data for pattern in xss_patterns)
    
    def _detect_path_traversal(self, request: HttpRequest) -> bool:
        """Detect path traversal attempts"""
        path_patterns = ["../", "..\\\\", "%2e%2e%2f", "%2e%2e\\\\"]
        path = request.path.lower()
        query_string = request.GET.urlencode().lower()
        
        combined_data = f"{path} {query_string}"
        
        return any(pattern in combined_data for pattern in path_patterns)
    
    def _detect_suspicious_user_agent(self, user_agent: str) -> bool:
        """Detect suspicious user agents"""
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'nessus',
            'burpsuite', 'owasp', 'w3af', 'acunetix'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(agent in user_agent_lower for agent in suspicious_agents)


class SecurityMonitor:
    """Main security monitoring system"""
    
    def __init__(self):
        self.logger = SecurityLogger()
        self.threat_detector = ThreatDetector()
        self.metrics = SecurityMetrics()
        self.active_threats = defaultdict(list)
        self.blocked_ips = set()
        self.lock = Lock()
        
        # Configuration
        self.enable_email_alerts = getattr(settings, 'SECURITY_EMAIL_ALERTS', True)
        self.alert_recipients = getattr(settings, 'SECURITY_ALERT_RECIPIENTS', [])
        self.auto_block_enabled = getattr(settings, 'SECURITY_AUTO_BLOCK', True)
        self.block_duration = getattr(settings, 'SECURITY_BLOCK_DURATION', 3600)  # 1 hour
    
    def process_request(self, request: HttpRequest) -> Tuple[bool, List[SecurityThreat]]:
        """Process incoming request for security threats"""
        threats = []
        should_block = False
        
        ip = self._get_client_ip(request)
        
        # Check if IP is already blocked
        if self._is_ip_blocked(ip):
            should_block = True
            return should_block, threats
        
        # Update metrics
        self._update_metrics(request)
        
        # Detect threats
        detected_threats = self.threat_detector.detect_suspicious_patterns(request)
        threats.extend(detected_threats)
        
        # Process each threat
        for threat in threats:
            self._handle_threat(threat)
            
            # Auto-block for critical threats
            if threat.severity == 'critical' and self.auto_block_enabled:
                self._block_ip(threat.source_ip)
                should_block = True
        
        return should_block, threats
    
    def report_failed_login(self, request: HttpRequest, username: str, user_id: Optional[int] = None):
        """Report failed login attempt"""
        ip = self._get_client_ip(request)
        
        # Detect brute force
        threat = self.threat_detector.detect_brute_force(ip, user_id)
        if threat:
            threat.details['username'] = username
            self._handle_threat(threat)
            
            if self.auto_block_enabled:
                self._block_ip(ip)
        
        self.metrics.failed_logins += 1
    
    def report_rate_limit_violation(self, request: HttpRequest, endpoint: str):
        """Report rate limit violation"""
        ip = self._get_client_ip(request)
        
        # Update cache counter
        cache_key = f'rate_abuse:{ip}:{endpoint}'
        current_count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, current_count, 300)  # 5 minutes
        
        # Detect abuse pattern
        threat = self.threat_detector.detect_rate_limit_abuse(ip, endpoint)
        if threat:
            self._handle_threat(threat)
        
        self.metrics.rate_limit_violations += 1
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        with self.lock:
            return {
                'metrics': {
                    'failed_logins': self.metrics.failed_logins,
                    'rate_limit_violations': self.metrics.rate_limit_violations,
                    'suspicious_requests': self.metrics.suspicious_requests,
                    'blocked_ips': len(self.blocked_ips),
                    'total_requests': self.metrics.total_requests,
                    'timestamp': self.metrics.timestamp.isoformat()
                },
                'active_threats': len(self.active_threats),
                'blocked_ips': list(self.blocked_ips),
                'threat_summary': self._get_threat_summary()
            }
    
    def _handle_threat(self, threat: SecurityThreat):
        """Handle detected security threat"""
        with self.lock:
            # Store threat
            self.active_threats[threat.source_ip].append(threat)
            
            # Log threat
            self.logger.log_suspicious_request(
                None,  # We don't have request object here
                threat.threat_type,
                threat.details
            )
            
            # Send alert for high/critical threats
            if threat.severity in ['high', 'critical'] and self.enable_email_alerts:
                self._send_security_alert(threat)
    
    def _block_ip(self, ip: str):
        """Block IP address"""
        with self.lock:
            self.blocked_ips.add(ip)
            cache.set(f'blocked_ip:{ip}', True, self.block_duration)
            
            # Log blocking
            logging.getLogger('security').warning(
                f"IP {ip} has been automatically blocked due to security threats"
            )
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return cache.get(f'blocked_ip:{ip}', False) or ip in self.blocked_ips
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def _update_metrics(self, request: HttpRequest):
        """Update security metrics"""
        with self.lock:
            self.metrics.total_requests += 1
            
            # Track unique IPs
            ip = self._get_client_ip(request)
            cache_key = f'unique_ip:{ip}'
            if not cache.get(cache_key):
                cache.set(cache_key, True, 86400)  # 24 hours
                self.metrics.unique_ips += 1
    
    def _get_threat_summary(self) -> Dict[str, int]:
        """Get summary of threat types"""
        summary = defaultdict(int)
        for threats in self.active_threats.values():
            for threat in threats:
                summary[threat.threat_type] += 1
        return dict(summary)
    
    def _send_security_alert(self, threat: SecurityThreat):
        """Send security alert email"""
        if not self.alert_recipients:
            return
        
        try:
            subject = f"[SECURITY ALERT] {threat.threat_type.upper()} - {threat.severity.upper()}"
            
            context = {
                'threat': threat,
                'timestamp': threat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'details': threat.details
            }
            
            message = render_to_string('security/alert_email.txt', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=self.alert_recipients,
                fail_silently=True
            )
            
        except Exception as e:
            logging.getLogger('security').error(
                f"Failed to send security alert: {e}"
            )


# Global security monitor instance
security_monitor = SecurityMonitor()