from django.shortcuts import render
from django.views.generic import TemplateView
import time


class IndexView(TemplateView):
    """Представление для главной страницы"""
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['timestamp'] = int(time.time())
        return context
