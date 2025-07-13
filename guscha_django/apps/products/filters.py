from django.db.models import Q
from django_filters import rest_framework as filters
from .models import Product, Category


class ProductFilter(filters.FilterSet):
    """Фильтр для товаров"""
    category = filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        field_name='category',
        to_field_name='slug'
    )
    category_id = filters.NumberFilter(field_name='category__id')
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_active = filters.BooleanFilter(field_name='is_active')
    is_featured = filters.BooleanFilter(field_name='is_featured')
    in_stock = filters.BooleanFilter(method='filter_in_stock')
    has_sizes = filters.BooleanFilter(method='filter_has_sizes')
    size = filters.CharFilter(method='filter_by_size')
    search = filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Product
        fields = [
            'category', 'category_id', 'min_price', 'max_price',
            'is_active', 'is_featured', 'in_stock', 'has_sizes',
            'size', 'search'
        ]
    
    def filter_in_stock(self, queryset, name, value):
        """Фильтрация по наличию на складе"""
        if value:
            return queryset.filter(
                Q(track_inventory=False) | 
                Q(stock_quantity__gt=0) | 
                Q(allow_backorder=True)
            )
        else:
            return queryset.filter(
                track_inventory=True,
                stock_quantity=0,
                allow_backorder=False
            )
    
    def filter_has_sizes(self, queryset, name, value):
        """Фильтрация по наличию размеров"""
        if value:
            return queryset.filter(sizes__isnull=False).distinct()
        else:
            return queryset.filter(sizes__isnull=True)
    
    def filter_by_size(self, queryset, name, value):
        """Фильтрация по конкретному размеру"""
        return queryset.filter(sizes__name=value).distinct()
    
    def filter_search(self, queryset, name, value):
        """Поиск по товарам"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(sku__icontains=value) |
            Q(search_keywords__icontains=value)
        ).distinct()