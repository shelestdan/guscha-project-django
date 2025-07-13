from django.urls import path
from .views import IndexView, ActiveBackgroundAPIView

app_name = 'core'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('active-background/', ActiveBackgroundAPIView.as_view(), name='active-background'),
]