from django.urls import path
from .views import IndexView
from . import admin_api

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    
    # API для админки
    path('sales-data/', admin_api.sales_data, name='admin_sales_data'),
    path('products-data/', admin_api.products_data, name='admin_products_data'),
    path('revenue-data/', admin_api.revenue_data, name='admin_revenue_data'),
    path('dashboard-stats/', admin_api.dashboard_stats, name='admin_dashboard_stats'),
    path('recent-activity/', admin_api.recent_activity, name='admin_recent_activity'),
    

]