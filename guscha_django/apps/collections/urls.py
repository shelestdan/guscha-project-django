from django.urls import path
from . import views

app_name = 'collections'

urlpatterns = [
    # API endpoints (для /api/collections/ префикса)
    path('', views.CollectionAPIView.as_view(), name='api_list'),
    path('<slug:slug>/images/', views.collection_images_api, name='api_images'),
]