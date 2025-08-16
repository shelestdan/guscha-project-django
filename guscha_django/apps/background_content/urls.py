from django.urls import path
from . import views

app_name = 'background_content'

urlpatterns = [
    # API для получения активного фонового контента
    path('active/', views.get_active_background, name='active_background'),
    
    # API для списка всего контента
    path('list/', views.BackgroundContentListView.as_view(), name='content_list'),
    
    # API для детальной информации о контенте
    path('detail/<int:pk>/', views.BackgroundContentDetailView.as_view(), name='content_detail'),
    
    # API для активации контента
    path('activate/<int:pk>/', views.activate_background, name='activate_content'),
    
    # API для фоновых изображений
    path('images/', views.get_background_images, name='background_images'),
    
    # API для слайдшоу
    path('slideshows/', views.get_slideshows, name='slideshows'),
    path('slideshows/<int:pk>/', views.get_slideshow_detail, name='slideshow_detail'),
    
    # API для фоновых видео
    path('videos/', views.get_background_videos, name='background_videos'),
]