from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.security_report_view import SecurityReportView, SecurityStatsView

app_name = 'security'

# API маршруты
urlpatterns = [
    # Отправка отчетов о безопасности
    path('api/security/report/', SecurityReportView.as_view(), name='security_report'),
    
    # Статистика безопасности (только для администраторов)
    path('api/security/stats/', SecurityStatsView.as_view(), name='security_stats'),
]