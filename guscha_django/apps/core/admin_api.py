# API для получения данных дашборда админки
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from apps.products.models import Product
from apps.orders.models import Order

User = get_user_model()

@staff_member_required
def sales_data(request):
    """Возвращает данные для графика продаж"""
    # Получаем данные за последние 6 месяцев
    end_date = timezone.now()
    start_date = end_date - timedelta(days=180)
    
    # Группируем заказы по месяцам
    orders_by_month = Order.objects.filter(
        created_at__gte=start_date,
        status='completed'
    ).extra(
        select={'month': "strftime('%%Y-%%m', created_at)"}
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Формируем данные для графика
    labels = []
    sales = []
    
    for item in orders_by_month:
        month_date = datetime.strptime(item['month'], '%Y-%m')
        month_name = month_date.strftime('%b')
        labels.append(month_name)
        sales.append(item['count'])
    
    # Если данных нет вообще, добавляем пустые данные
    if len(labels) == 0:
        labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн']
        sales = [0, 0, 0, 0, 0, 0]
    
    return JsonResponse({
        'labels': labels,
        'sales': sales
    })

@staff_member_required
def products_data(request):
    """Возвращает данные для графика популярных товаров"""
    # Получаем топ-5 самых заказываемых товаров
    popular_products = Product.objects.annotate(
        order_count=Count('orderitem')
    ).filter(
        order_count__gt=0
    ).order_by('-order_count')[:5]
    
    labels = []
    values = []
    
    for product in popular_products:
        labels.append(product.name[:20] + '...' if len(product.name) > 20 else product.name)
        values.append(product.order_count)
    
    # Если данных нет вообще, добавляем пустые данные
    if len(labels) == 0:
        labels = ['Нет данных']
        values = [1]
    
    return JsonResponse({
        'labels': labels,
        'values': values
    })

@staff_member_required
def revenue_data(request):
    """Возвращает данные для графика выручки по дням недели"""
    # Получаем данные за последние 7 дней
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=6)
    
    revenue_by_day = []
    labels = []
    
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        
        # Получаем выручку за день
        daily_revenue = Order.objects.filter(
            created_at__date=current_date,
            status='completed'
        ).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        revenue_by_day.append(float(daily_revenue))
        
        # Название дня недели
        day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        labels.append(day_names[current_date.weekday()])
    
    # Оставляем реальные данные даже если они нулевые
    # if sum(revenue_by_day) == 0:
    #     revenue_by_day = [1200, 1900, 800, 1500, 2000, 1800, 2400]
    
    return JsonResponse({
        'labels': labels,
        'revenue': revenue_by_day
    })

@staff_member_required
def dashboard_stats(request):
    """Возвращает общую статистику для дашборда"""
    # Подсчитываем общую статистику
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    
    # Общая выручка
    total_revenue = Order.objects.filter(
        status='completed'
    ).aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # Статистика за последний месяц
    last_month = timezone.now() - timedelta(days=30)
    
    new_users_month = User.objects.filter(
        date_joined__gte=last_month
    ).count()
    
    new_orders_month = Order.objects.filter(
        created_at__gte=last_month
    ).count()
    
    revenue_month = Order.objects.filter(
        created_at__gte=last_month,
        status='completed'
    ).aggregate(
        total=Sum('total')
    )['total'] or 0
    
    return JsonResponse({
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'new_users_month': new_users_month,
        'new_orders_month': new_orders_month,
        'revenue_month': float(revenue_month),
        'growth_users': calculate_growth_percentage(new_users_month, total_users),
        'growth_orders': calculate_growth_percentage(new_orders_month, total_orders),
        'growth_revenue': calculate_growth_percentage(float(revenue_month), float(total_revenue))
    })

def calculate_growth_percentage(current, total):
    """Вычисляет процент роста"""
    if total == 0:
        return 0
    return round((current / total) * 100, 1)

@staff_member_required
def recent_activity(request):
    """Возвращает последнюю активность"""
    # Последние заказы
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Новые пользователи
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    # Новые товары
    recent_products = Product.objects.order_by('-created_at')[:5]
    
    orders_data = []
    for order in recent_orders:
        orders_data.append({
            'id': order.id,
            'user': order.user.email if order.user else 'Гость',
            'total': float(order.total),
            'status': order.status,
            'created_at': order.created_at.strftime('%d.%m.%Y %H:%M')
        })
    
    users_data = []
    for user in recent_users:
        users_data.append({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.strftime('%d.%m.%Y %H:%M')
        })
    
    products_data = []
    for product in recent_products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'created_at': product.created_at.strftime('%d.%m.%Y %H:%M')
        })
    
    return JsonResponse({
        'recent_orders': orders_data,
        'recent_users': users_data,
        'recent_products': products_data
    })