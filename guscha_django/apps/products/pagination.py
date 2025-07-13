from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Стандартная пагинация для результатов API"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100