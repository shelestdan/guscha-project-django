"""Security Monitor Management Command

This command provides comprehensive security monitoring, reporting,
and management capabilities for the Django application.
"""

import json
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone
from apps.core.security.monitoring import security_monitor
from apps.core.utils.security_logger import security_logger


class Command(BaseCommand):
    help = 'Security monitoring and management command'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current security status'
        )
        
        parser.add_argument(
            '--threats',
            action='store_true',
            help='Show active security threats'
        )
        
        parser.add_argument(
            '--metrics',
            action='store_true',
            help='Show security metrics'
        )
        
        parser.add_argument(
            '--blocked-ips',
            action='store_true',
            help='Show blocked IP addresses'
        )
        
        parser.add_argument(
            '--unblock-ip',
            type=str,
            help='Unblock specific IP address'
        )
        
        parser.add_argument(
            '--block-ip',
            type=str,
            help='Manually block IP address'
        )
        
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear security monitoring cache'
        )
        
        parser.add_argument(
            '--export-logs',
            type=str,
            help='Export security logs to file (JSON format)'
        )
        
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Start real-time monitoring (press Ctrl+C to stop)'
        )
        
        parser.add_argument(
            '--dashboard',
            action='store_true',
            help='Show security dashboard'
        )
        
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Monitoring interval in seconds (default: 30)'
        )
        
        parser.add_argument(
            '--alerts-only',
            action='store_true',
            help='Show only security alerts'
        )
        
        parser.add_argument(
            '--test-alerts',
            action='store_true',
            help='Test security alert system'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days for historical data (default: 7)'
        )
    
    def handle(self, *args, **options):
        """Handle command execution"""
        try:
            if options['status']:
                self.show_security_status()
            elif options['threats']:
                self.show_active_threats()
            elif options['metrics']:
                self.show_security_metrics(options['days'])
            elif options['blocked_ips']:
                self.show_blocked_ips()
            elif options['unblock_ip']:
                self.unblock_ip(options['unblock_ip'])
            elif options['block_ip']:
                self.block_ip(options['block_ip'])
            elif options['clear_cache']:
                self.clear_security_cache()
            elif options['export_logs']:
                self.export_security_logs(options['export_logs'], options['days'])
            elif options['monitor']:
                self.start_real_time_monitoring(options['interval'], options['alerts_only'])
            elif options['dashboard']:
                self.show_security_dashboard()
            elif options['test_alerts']:
                self.test_alert_system()
            else:
                self.show_help()
                
        except KeyboardInterrupt:
            self.stdout.write("\nMonitoring stopped by user.")
        except Exception as e:
            raise CommandError(f"Command failed: {e}")
    
    def show_security_status(self):
        """Show current security status"""
        self.stdout.write(self.style.SUCCESS("\nSecurity Status Report"))
        self.stdout.write("=" * 60)
        
        status = security_monitor.get_security_status()
        
        # Overall status
        metrics = status['metrics']
        self.stdout.write(f"\n📊 Overall Metrics:")
        self.stdout.write(f"   Total Requests: {metrics['total_requests']:,}")
        self.stdout.write(f"   Failed Logins: {metrics['failed_logins']:,}")
        self.stdout.write(f"   Rate Limit Violations: {metrics['rate_limit_violations']:,}")
        self.stdout.write(f"   Suspicious Requests: {metrics['suspicious_requests']:,}")
        self.stdout.write(f"   Blocked IPs: {metrics['blocked_ips']:,}")
        self.stdout.write(f"   Last Updated: {metrics['timestamp']}")
        
        # Active threats
        self.stdout.write(f"\n🚨 Active Threats: {status['active_threats']}")
        
        if status['threat_summary']:
            self.stdout.write("\n📋 Threat Summary:")
            for threat_type, count in status['threat_summary'].items():
                self.stdout.write(f"   {threat_type}: {count}")
        
        # System health
        self.stdout.write(f"\n💚 System Health:")
        health_score = self._calculate_health_score(metrics)
        health_status = "GOOD" if health_score > 80 else "WARNING" if health_score > 60 else "CRITICAL"
        color = self.style.SUCCESS if health_score > 80 else self.style.WARNING if health_score > 60 else self.style.ERROR
        self.stdout.write(f"   Health Score: {color(f'{health_score}/100 ({health_status})')}")
    
    def show_active_threats(self):
        """Show active security threats"""
        self.stdout.write(self.style.WARNING("\nActive Security Threats"))
        self.stdout.write("=" * 60)
        
        status = security_monitor.get_security_status()
        
        if not status['active_threats']:
            self.stdout.write(self.style.SUCCESS("✅ No active threats detected"))
            return
        
        # Show threats by IP
        for ip, threats in security_monitor.active_threats.items():
            self.stdout.write(f"\n🔍 IP Address: {ip}")
            for threat in threats[-5:]:  # Show last 5 threats
                severity_color = {
                    'low': self.style.SUCCESS,
                    'medium': self.style.WARNING,
                    'high': self.style.ERROR,
                    'critical': self.style.ERROR
                }.get(threat.severity, self.style.WARNING)
                
                self.stdout.write(
                    f"   {severity_color(threat.severity.upper())} | "
                    f"{threat.threat_type} | "
                    f"{threat.timestamp.strftime('%H:%M:%S')} | "
                    f"Count: {threat.count}"
                )
                
                if threat.details:
                    for key, value in threat.details.items():
                        self.stdout.write(f"     {key}: {value}")
    
    def show_security_metrics(self, days: int):
        """Show detailed security metrics"""
        self.stdout.write(self.style.SUCCESS(f"\nSecurity Metrics (Last {days} days)"))
        self.stdout.write("=" * 60)
        
        # Get metrics from cache
        metrics = {
            'total_requests': cache.get('security_metrics:total_requests', 0),
            'unique_ips': cache.get('security_metrics:unique_ips', 0),
            'auth_failures': cache.get('security_metrics:auth_failures', 0),
            'permission_denials': cache.get('security_metrics:permission_denials', 0),
            'errors_400': cache.get('security_metrics:errors:400', 0),
            'errors_401': cache.get('security_metrics:errors:401', 0),
            'errors_403': cache.get('security_metrics:errors:403', 0),
            'errors_404': cache.get('security_metrics:errors:404', 0),
            'errors_500': cache.get('security_metrics:errors:500', 0)
        }
        
        self.stdout.write(f"\n📈 Request Metrics:")
        self.stdout.write(f"   Total Requests: {metrics['total_requests']:,}")
        self.stdout.write(f"   Unique IPs: {metrics['unique_ips']:,}")
        self.stdout.write(f"   Avg Requests/IP: {metrics['total_requests'] / max(metrics['unique_ips'], 1):.1f}")
        
        self.stdout.write(f"\n🔐 Authentication Metrics:")
        self.stdout.write(f"   Auth Failures (401): {metrics['auth_failures']:,}")
        self.stdout.write(f"   Permission Denials (403): {metrics['permission_denials']:,}")
        
        self.stdout.write(f"\n❌ Error Metrics:")
        self.stdout.write(f"   Bad Requests (400): {metrics['errors_400']:,}")
        self.stdout.write(f"   Unauthorized (401): {metrics['errors_401']:,}")
        self.stdout.write(f"   Forbidden (403): {metrics['errors_403']:,}")
        self.stdout.write(f"   Not Found (404): {metrics['errors_404']:,}")
        self.stdout.write(f"   Server Errors (500): {metrics['errors_500']:,}")
        
        # Calculate error rate
        total_errors = sum([metrics[f'errors_{code}'] for code in [400, 401, 403, 404, 500]])
        error_rate = (total_errors / max(metrics['total_requests'], 1)) * 100
        
        error_color = self.style.SUCCESS if error_rate < 5 else self.style.WARNING if error_rate < 15 else self.style.ERROR
        self.stdout.write(f"\n📊 Error Rate: {error_color(f'{error_rate:.2f}%')}")
    
    def show_blocked_ips(self):
        """Show blocked IP addresses"""
        self.stdout.write(self.style.ERROR("\nBlocked IP Addresses"))
        self.stdout.write("=" * 60)
        
        blocked_ips = security_monitor.blocked_ips
        
        if not blocked_ips:
            self.stdout.write(self.style.SUCCESS("✅ No IP addresses are currently blocked"))
            return
        
        self.stdout.write(f"\n🚫 Total Blocked IPs: {len(blocked_ips)}")
        
        for ip in sorted(blocked_ips):
            # Check if still in cache
            cache_key = f'blocked_ip:{ip}'
            is_cached = cache.get(cache_key, False)
            status = "ACTIVE" if is_cached else "EXPIRED"
            
            status_color = self.style.ERROR if is_cached else self.style.WARNING
            self.stdout.write(f"   {ip} - {status_color(status)}")
    
    def unblock_ip(self, ip: str):
        """Unblock specific IP address"""
        self.stdout.write(f"\nUnblocking IP address: {ip}")
        
        # Remove from cache
        cache_key = f'blocked_ip:{ip}'
        cache.delete(cache_key)
        
        # Remove from active set
        if ip in security_monitor.blocked_ips:
            security_monitor.blocked_ips.remove(ip)
        
        self.stdout.write(self.style.SUCCESS(f"✅ IP {ip} has been unblocked"))
    
    def block_ip(self, ip: str):
        """Manually block IP address"""
        self.stdout.write(f"\nBlocking IP address: {ip}")
        
        # Add to cache
        cache_key = f'blocked_ip:{ip}'
        cache.set(cache_key, True, 3600)  # 1 hour
        
        # Add to active set
        security_monitor.blocked_ips.add(ip)
        
        self.stdout.write(self.style.SUCCESS(f"✅ IP {ip} has been blocked"))
    
    def clear_security_cache(self):
        """Clear security monitoring cache"""
        self.stdout.write("\nClearing security monitoring cache...")
        
        # Clear rate limiting cache
        cache_keys = [
            'security_metrics:*',
            'rate_limit:*',
            'rate_burst:*',
            'blocked_ip:*',
            'rate_abuse:*',
            'unique_ip:*'
        ]
        
        cleared_count = 0
        for pattern in cache_keys:
            # Note: This is a simplified approach. In production, you might want
            # to use Redis SCAN or similar for pattern-based deletion
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern(pattern)
                    cleared_count += 1
            except AttributeError:
                pass
        
        # Clear in-memory data
        security_monitor.active_threats.clear()
        security_monitor.blocked_ips.clear()
        
        self.stdout.write(self.style.SUCCESS(f"✅ Security cache cleared ({cleared_count} patterns)"))
    
    def export_security_logs(self, filename: str, days: int):
        """Export security logs to file"""
        self.stdout.write(f"\nExporting security logs to {filename}...")
        
        # Collect data
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'days_included': days,
            'security_status': security_monitor.get_security_status(),
            'blocked_ips': list(security_monitor.blocked_ips),
            'active_threats': {}
        }
        
        # Convert threats to serializable format
        for ip, threats in security_monitor.active_threats.items():
            export_data['active_threats'][ip] = [
                {
                    'threat_type': threat.threat_type,
                    'severity': threat.severity,
                    'timestamp': threat.timestamp.isoformat(),
                    'details': threat.details,
                    'count': threat.count
                }
                for threat in threats
            ]
        
        # Write to file
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Security logs exported to {filename}"))
            
        except Exception as e:
            raise CommandError(f"Failed to export logs: {e}")
    
    def start_real_time_monitoring(self):
        """Start real-time security monitoring"""
        self.stdout.write(self.style.SUCCESS("\n🔍 Starting Real-time Security Monitoring"))
        self.stdout.write("Press Ctrl+C to stop\n")
        
        last_metrics = {}
        
        try:
            while True:
                # Clear screen (simple approach)
                self.stdout.write("\033[2J\033[H")
                
                # Show current time
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.stdout.write(f"🕐 {current_time}\n")
                
                # Get current status
                status = security_monitor.get_security_status()
                metrics = status['metrics']
                
                # Show key metrics with changes
                self.stdout.write("📊 Key Metrics:")
                for key, value in metrics.items():
                    if key == 'timestamp':
                        continue
                    
                    change = ""
                    if key in last_metrics:
                        diff = value - last_metrics[key]
                        if diff > 0:
                            change = f" (+{diff})"
                        elif diff < 0:
                            change = f" ({diff})"
                    
                    self.stdout.write(f"   {key}: {value:,}{change}")
                
                # Show active threats
                if status['active_threats'] > 0:
                    self.stdout.write(f"\n🚨 Active Threats: {status['active_threats']}")
                    for threat_type, count in status['threat_summary'].items():
                        self.stdout.write(f"   {threat_type}: {count}")
                
                # Show blocked IPs
                if status['blocked_ips']:
                    self.stdout.write(f"\n🚫 Blocked IPs: {len(status['blocked_ips'])}")
                
                last_metrics = metrics.copy()
                
                # Wait before next update
                time.sleep(5)
                
        except KeyboardInterrupt:
            pass
    
    def test_alert_system(self):
        """Test security alert system"""
        self.stdout.write("\n🧪 Testing Security Alert System")
        self.stdout.write("=" * 60)
        
        # Test logging
        logger = SecurityLogger()
        
        self.stdout.write("\n1. Testing security event logging...")
        logger.log_security_event(
            'test_alert',
            'Testing security alert system',
            {'test': True, 'timestamp': datetime.now().isoformat()}
        )
        self.stdout.write(self.style.SUCCESS("   ✅ Security event logged"))
        
        # Test threat detection
        self.stdout.write("\n2. Testing threat detection...")
        from django.test import RequestFactory
        factory = RequestFactory()
        
        # Create a test request with suspicious content
        request = factory.get('/test/?q=<script>alert(1)</script>')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.META['HTTP_USER_AGENT'] = 'TestAgent/1.0'
        
        should_block, threats = security_monitor.process_request(request)
        
        if threats:
            self.stdout.write(self.style.SUCCESS(f"   ✅ Detected {len(threats)} threats"))
            for threat in threats:
                self.stdout.write(f"      - {threat.threat_type} ({threat.severity})")
        else:
            self.stdout.write(self.style.WARNING("   ⚠️  No threats detected in test request"))
        
        self.stdout.write("\n3. Testing metrics collection...")
        current_requests = cache.get('security_metrics:total_requests', 0)
        self.stdout.write(self.style.SUCCESS(f"   ✅ Current request count: {current_requests}"))
        
        self.stdout.write("\n✅ Alert system test completed")
    
    def show_help(self):
        """Show command help"""
        self.stdout.write("\n🛡️  Security Monitor Command Help")
        self.stdout.write("=" * 60)
        self.stdout.write("\nAvailable options:")
        self.stdout.write("  --status          Show current security status")
        self.stdout.write("  --threats         Show active security threats")
        self.stdout.write("  --metrics         Show security metrics")
        self.stdout.write("  --blocked-ips     Show blocked IP addresses")
        self.stdout.write("  --unblock-ip IP   Unblock specific IP address")
        self.stdout.write("  --block-ip IP     Manually block IP address")
        self.stdout.write("  --clear-cache     Clear security monitoring cache")
        self.stdout.write("  --export-logs F   Export security logs to file")
        self.stdout.write("  --monitor         Start real-time monitoring")
        self.stdout.write("  --test-alerts     Test security alert system")
        self.stdout.write("  --days N          Number of days for data (default: 7)")
        
        self.stdout.write("\nExamples:")
        self.stdout.write("  python manage.py security_monitor --status")
        self.stdout.write("  python manage.py security_monitor --monitor")
        self.stdout.write("  python manage.py security_monitor --unblock-ip 192.168.1.100")
        self.stdout.write("  python manage.py security_monitor --export-logs security_report.json")
    
    def _calculate_health_score(self, metrics: dict) -> int:
        """Calculate security health score (0-100)"""
        score = 100
        
        # Deduct points for security issues
        if metrics['failed_logins'] > 10:
            score -= min(20, metrics['failed_logins'] // 5)
        
        if metrics['rate_limit_violations'] > 50:
            score -= min(15, metrics['rate_limit_violations'] // 10)
        
        if metrics['suspicious_requests'] > 5:
            score -= min(25, metrics['suspicious_requests'] * 5)
        
        if metrics['blocked_ips'] > 0:
            score -= min(10, metrics['blocked_ips'] * 2)
        
        return max(0, score)
    
    def show_security_dashboard(self):
        """Show comprehensive security dashboard"""
        self._clear_screen()
        
        dashboard_data = security_monitor.get_dashboard_data()
        
        # Header
        self.stdout.write('=' * 80)
        self.stdout.write(
            self.style.SUCCESS(
                f'🛡️  SECURITY DASHBOARD - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )
        self.stdout.write('=' * 80)
        
        # System status
        system_status = dashboard_data['system_status']
        status_color = self._get_status_color(system_status['overall_status'])
        self.stdout.write(
            f"📊 System Status: {status_color(system_status['overall_status'].upper())}"
        )
        self.stdout.write(f"🔄 Last Update: {system_status['last_update']}")
        self.stdout.write('')
        
        # Threats summary
        threats_1h = dashboard_data['threat_summary_1h']
        self.stdout.write(self.style.WARNING('🚨 THREATS (Last Hour):'))
        self.stdout.write(f"   Total Threats: {threats_1h['total_threats']}")
        self.stdout.write(f"   High Risk: {threats_1h['high_risk_threats']}")
        self.stdout.write(f"   Average Risk Score: {threats_1h['average_risk_score']:.1f}")
        
        if threats_1h['top_attacking_ips']:
            self.stdout.write('   Top Attacking IPs:')
            for ip, count in list(threats_1h['top_attacking_ips'].items())[:5]:
                self.stdout.write(f"     • {ip}: {count} attacks")
        self.stdout.write('')
        
        # Security metrics
        metrics_1h = dashboard_data['security_metrics_1h']
        self.stdout.write(self.style.HTTP_INFO('📈 METRICS (Last Hour):'))
        self.stdout.write(f"   Total Events: {metrics_1h['total_events']}")
        self.stdout.write(f"   Failed Logins: {metrics_1h['failed_logins']}")
        self.stdout.write(f"   Successful Logins: {metrics_1h['successful_logins']}")
        self.stdout.write(f"   Blocked Requests: {metrics_1h['blocked_requests']}")
        self.stdout.write(f"   Suspicious Activity: {metrics_1h['suspicious_activities']}")
        self.stdout.write(f"   Unique IPs: {metrics_1h['unique_ips']}")
        self.stdout.write(f"   Error Rate: {metrics_1h['error_rate']:.1%}")
        self.stdout.write('')
        
        # Active alerts
        active_alerts = dashboard_data['active_alerts']
        if active_alerts:
            self.stdout.write(self.style.ERROR('🚨 ACTIVE ALERTS:'))
            for alert in active_alerts[-10:]:
                severity_color = self._get_severity_color(alert['severity'])
                ack_status = '✅' if alert['acknowledged'] else '❌'
                self.stdout.write(
                    f"   {ack_status} [{severity_color(alert['severity'].upper())}] "
                    f"{alert['message']} ({alert['timestamp']})"
                )
        else:
            self.stdout.write(self.style.SUCCESS('✅ No Active Alerts'))
        
        self.stdout.write('=' * 80)
    
    def start_real_time_monitoring(self, interval=30, alerts_only=False):
        """Start real-time security monitoring"""
        self.stdout.write(
            self.style.SUCCESS(
                f'🛡️  Starting security monitoring (interval: {interval}s)'
            )
        )
        
        try:
            while True:
                if alerts_only:
                    self._show_alerts_only()
                else:
                    self._show_monitoring_summary()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n⏹️  Monitoring stopped by user')
            )
    
    def _show_monitoring_summary(self):
        """Show monitoring summary"""
        threats = security_monitor.get_threat_summary(60)
        metrics = security_monitor.get_security_metrics(60)
        alerts = security_monitor.get_active_alerts()
        
        timestamp = timezone.now().strftime('%H:%M:%S')
        
        self.stdout.write(
            f"[{timestamp}] 🛡️  Threats: {threats['total_threats']} "
            f"| High Risk: {threats['high_risk_threats']} "
            f"| Events: {metrics['total_events']} "
            f"| Alerts: {len([a for a in alerts if not a['acknowledged']])}"
        )
        
        # Show new alerts
        unacknowledged_alerts = [a for a in alerts if not a['acknowledged']]
        if unacknowledged_alerts:
            for alert in unacknowledged_alerts[-3:]:
                severity_color = self._get_severity_color(alert['severity'])
                self.stdout.write(
                    f"  🚨 [{severity_color(alert['severity'].upper())}] {alert['message']}"
                )
    
    def _show_alerts_only(self):
        """Show only security alerts"""
        alerts = security_monitor.get_active_alerts()
        unacknowledged_alerts = [a for a in alerts if not a['acknowledged']]
        
        if unacknowledged_alerts:
            timestamp = timezone.now().strftime('%H:%M:%S')
            self.stdout.write(f"[{timestamp}] 🚨 NEW ALERTS:")
            
            for alert in unacknowledged_alerts:
                severity_color = self._get_severity_color(alert['severity'])
                self.stdout.write(
                    f"  [{severity_color(alert['severity'].upper())}] "
                    f"{alert['message']} ({alert['timestamp']})"
                )
                
                # Show details for critical alerts
                if alert['severity'] == 'critical':
                    details = json.dumps(alert['details'], indent=2, ensure_ascii=False)
                    self.stdout.write(f"    Details: {details}")
            
            self.stdout.write('')
    
    def _clear_screen(self):
        """Clear screen (works in most terminals)"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _get_status_color(self, status):
        """Get color for system status"""
        colors = {
            'normal': self.style.SUCCESS,
            'warning': self.style.WARNING,
            'critical': self.style.ERROR
        }
        return colors.get(status, self.style.NOTICE)
    
    def _get_severity_color(self, severity):
        """Get color for alert severity"""
        colors = {
            'low': self.style.SUCCESS,
            'medium': self.style.WARNING,
            'high': self.style.ERROR,
            'critical': self.style.ERROR
        }
        return colors.get(severity, self.style.NOTICE)