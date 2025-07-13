import django_filters
from .models import Order


class OrderFilter(django_filters.FilterSet):
    """
    Фильтры для заказов
    """
    status = django_filters.ChoiceFilter(
        choices=Order.STATUS_CHOICES,
        field_name='status',
        lookup_expr='exact'
    )
    
    min_total = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte'
    )
    
    max_total = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte'
    )
    
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Order
        fields = ['status', 'min_total', 'max_total', 'created_after', 'created_before']