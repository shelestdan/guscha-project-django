# Скрипт для быстрой пересборки и перезапуска Django контейнера
# PowerShell скрипт для Windows

Write-Host "=== Остановка контейнеров ===" -ForegroundColor Yellow
docker-compose down

Write-Host "=== Удаление старых образов ===" -ForegroundColor Yellow
docker rmi guscha_django-django 2>$null
docker rmi guscha_django_django 2>$null

Write-Host "=== Очистка неиспользуемых образов ===" -ForegroundColor Yellow
docker image prune -f

Write-Host "=== Сборка нового образа ===" -ForegroundColor Green
docker-compose build --no-cache django

Write-Host "=== Запуск контейнеров ===" -ForegroundColor Green
docker-compose up -d

Write-Host "=== Проверка статуса ===" -ForegroundColor Cyan
docker-compose ps

Write-Host "=== Логи Django контейнера ===" -ForegroundColor Cyan
docker-compose logs django

Write-Host "=== Готово! ===" -ForegroundColor Green
Write-Host "Приложение доступно по адресу: http://localhost" -ForegroundColor White