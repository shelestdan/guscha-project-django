# Скрипт для быстрой пересборки с оптимизированным Dockerfile
# PowerShell скрипт для Windows

Write-Host "=== Остановка контейнеров ===" -ForegroundColor Yellow
docker-compose -f docker-compose.optimized.yml down

Write-Host "=== Удаление старых образов ===" -ForegroundColor Yellow
docker rmi guscha_django-django 2>$null
docker rmi guscha_django_django 2>$null

Write-Host "=== Очистка неиспользуемых образов и volumes ===" -ForegroundColor Yellow
docker image prune -f
docker volume prune -f

Write-Host "=== Сборка оптимизированного образа ===" -ForegroundColor Green
docker-compose -f docker-compose.optimized.yml build --no-cache django

Write-Host "=== Запуск контейнеров ===" -ForegroundColor Green
docker-compose -f docker-compose.optimized.yml up -d

Write-Host "=== Сбор статических файлов ===" -ForegroundColor Cyan
docker-compose -f docker-compose.optimized.yml exec django python manage.py collectstatic --noinput

Write-Host "=== Проверка статуса ===" -ForegroundColor Cyan
docker-compose -f docker-compose.optimized.yml ps

Write-Host "=== Логи Django контейнера ===" -ForegroundColor Cyan
docker-compose -f docker-compose.optimized.yml logs django

Write-Host "=== Готово! ===" -ForegroundColor Green
Write-Host "Приложение доступно по адресу: http://localhost" -ForegroundColor White
Write-Host "Для просмотра логов в реальном времени: docker-compose -f docker-compose.optimized.yml logs -f django" -ForegroundColor Gray