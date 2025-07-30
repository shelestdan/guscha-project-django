from django.contrib import admin
# from django.contrib.admin import AdminSite
# from django.urls import path
# from .admin_views import custom_admin_index

# Переопределяем метод index для стандартного админ-сайта
# original_index = admin.site.index

# def custom_index_wrapper(request, extra_context=None):
#     """
#     Обертка для кастомного индекса админки
#     """
#     return custom_admin_index(request)

# Заменяем стандартный index на наш кастомный
# admin.site.index = custom_index_wrapper
# admin.site.index_template = 'admin/index.html'
