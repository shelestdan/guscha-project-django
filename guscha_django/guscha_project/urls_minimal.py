"""
Минимальные URL-маршруты для быстрого запуска проекта.
"""

from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home_view(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Guscha Project</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f5f5f5;
                color: #333;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                padding: 40px;
                text-align: center;
                max-width: 600px;
                width: 90%;
            }
            h1 {
                color: #4a6fa5;
                margin-bottom: 20px;
            }
            p {
                font-size: 18px;
                line-height: 1.6;
                margin-bottom: 30px;
            }
            .status {
                background-color: #e8f5e9;
                color: #2e7d32;
                padding: 10px 15px;
                border-radius: 4px;
                font-weight: bold;
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Guscha Project</h1>
            <p>Проект успешно запущен и готов к работе!</p>
            <div class="status">Статус: Онлайн</div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content)

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('health/', health_check, name='health'),
]