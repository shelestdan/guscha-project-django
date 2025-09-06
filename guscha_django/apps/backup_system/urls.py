from django.urls import path
from . import views

app_name = 'backup_system'

urlpatterns = [
    # Базовые URL для системы резервного копирования
    # Управление осуществляется через админку Django
    # Команды: python manage.py dbbackup, listbackups, dbrestore
]