from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class IndexView(TemplateView):
    """Представление для главной страницы"""
    template_name = 'index.html'


class ActiveBackgroundAPIView(APIView):
    """API для получения активного фона"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Возвращаем заглушку для активного фона
        # В будущем здесь можно добавить логику для получения активного фона из базы данных
        return Response({
            'background_image': None,
            'background_color': '#f8f9fa',
            'is_active': False
        })
