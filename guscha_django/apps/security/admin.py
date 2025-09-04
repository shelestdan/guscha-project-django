from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import SecurityReport, ThreatDetection, SecurityBlacklist, DeviceFingerprint, BehavioralAnalysis, SecuritySettings, SecurityLog


@admin.register(SecurityReport)
class SecurityReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'ip_address', 'risk_level', 'overall_risk_score',
        'threat_detected', 'created_at'
    ]
    
    list_filter = [
        'risk_level', 'threat_detected', 'recommended_action', 'automation_detected', 'created_at'
    ]
    
    search_fields = ['ip_address', 'user_agent', 'session_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('session_id', 'ip_address', 'user_agent', 'user')
        }),
        ('Анализ риска', {
            'fields': ('overall_risk_score', 'risk_level', 'threat_detected', 'recommended_action', 'analysis_confidence')
        }),
        ('Device Fingerprinting', {
            'fields': ('fingerprint_hash', 'fingerprint_confidence', 'automation_detected'),
            'classes': ('collapse',)
        }),
        ('Поведенческий анализ', {
            'fields': ('behavior_is_human', 'behavior_confidence', 'behavior_risk_score', 'total_interactions'),
            'classes': ('collapse',)
        }),
        ('Дополнительные данные', {
            'fields': ('raw_data', 'request_metadata'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ThreatDetection)
class ThreatDetectionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'security_report', 'threat_type', 'severity',
        'status', 'created_at'
    ]
    
    list_filter = [
        'threat_type', 'status', 'severity', 'created_at'
    ]
    
    search_fields = ['security_report__ip_address', 'threat_type', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('security_report', 'threat_type', 'severity')
        }),
        ('Детали угрозы', {
            'fields': ('description', 'status', 'resolved_at')
        }),
        ('Временные метки', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityBlacklist)
class SecurityBlacklistAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'blacklist_type', 'value', 'is_active',
        'expires_at', 'created_at'
    ]
    
    list_filter = [
        'blacklist_type', 'is_active', 'expires_at', 'created_at'
    ]
    
    search_fields = ['value', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('blacklist_type', 'value', 'is_active')
        }),
        ('Детали блокировки', {
            'fields': ('reason', 'expires_at')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DeviceFingerprint)
class DeviceFingerprintAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'fingerprint_hash', 'user',
        'risk_level', 'first_seen'
    ]
    
    list_filter = [
        'risk_level', 'is_suspicious', 'first_seen'
    ]
    
    search_fields = ['fingerprint_hash', 'user_agent', 'user__username']
    readonly_fields = ['first_seen', 'last_seen']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('fingerprint_hash', 'user')
        }),
        ('Информация об устройстве', {
            'fields': ('user_agent', 'screen_resolution', 'timezone_offset')
        }),
        ('Анализ риска', {
            'fields': ('risk_level', 'risk_score', 'is_suspicious')
        }),
        ('Статистика использования', {
            'fields': ('usage_count', 'first_seen', 'last_seen'),
            'classes': ('collapse',)
        })
    )


@admin.register(BehavioralAnalysis)
class BehavioralAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session_id', 'user', 'analysis_type',
        'risk_level', 'created_at'
    ]
    
    list_filter = [
        'analysis_type', 'risk_level', 'is_bot_like', 'is_suspicious', 'created_at'
    ]
    
    search_fields = ['session_id', 'user__username', 'ip_address']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('session_id', 'user', 'ip_address', 'analysis_type')
        }),
        ('Анализ риска', {
            'fields': ('risk_level', 'risk_score', 'is_bot_like', 'is_suspicious')
        }),
        ('Временные данные', {
            'fields': ('analysis_start', 'analysis_end', 'created_at'),
            'classes': ('collapse',)
        }),
        ('Поведенческие метрики', {
            'fields': ('mouse_velocity_avg', 'typing_speed', 'additional_metrics'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'description', 'is_active', 'updated_at'
    ]
    
    list_filter = [
        'is_active', 'updated_at'
    ]
    
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Настройки блокировки', {
            'fields': ('max_failed_attempts', 'lockout_duration')
        }),
        ('Настройки мониторинга', {
            'fields': ('enable_ip_monitoring', 'enable_device_fingerprinting', 'enable_behavioral_analysis')
        }),
        ('Пороги риска', {
            'fields': ('risk_threshold_low', 'risk_threshold_medium', 'risk_threshold_high')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'event_type', 'severity', 'message', 'ip_address', 'created_at'
    ]
    
    list_filter = [
        'event_type', 'severity', 'status', 'created_at'
    ]
    
    search_fields = ['message', 'ip_address', 'user_agent', 'username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('event_type', 'severity', 'status', 'message')
        }),
        ('Пользователь и сессия', {
            'fields': ('user', 'username', 'session_id')
        }),
        ('Контекст запроса', {
            'fields': ('ip_address', 'user_agent', 'request_method', 'request_path')
        }),
        ('Дополнительные данные', {
            'fields': ('additional_data', 'risk_score'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )