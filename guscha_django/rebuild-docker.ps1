#!/usr/bin/env pwsh
# Скрипт для пересборки Docker контейнеров с исправленными настройками статических файлов

Write-Host "🔄 Остановка и удаление существующих контейнеров..." -ForegroundColor Yellow
docker-compose down

Write-Host "🗑️ Удаление старых образов..." -ForegroundColor Yellow
docker rmi guscha_django-django 2>$null
docker rmi guscha_django-telegram-bot 2>$null

Write-Host "📦 Сборка статических файлов Django..." -ForegroundColor Green
python manage.py collectstatic --noinput

Write-Host "🐳 Сборка новых Docker образов..." -ForegroundColor Green
docker-compose build --no-cache

Write-Host "🚀 Запуск контейнеров..." -ForegroundColor Green
docker-compose up -d

Write-Host "⏳ Ожидание запуска сервисов..." -ForegroundColor Blue
Start-Sleep -Seconds 10

Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose ps

Write-Host "" 
Write-Host "✅ Готово! Админка доступна по адресам:" -ForegroundColor Green
Write-Host "   🌐 http://localhost/admin/" -ForegroundColor White
Write-Host "   🌐 http://127.0.0.1/admin/" -ForegroundColor White
Write-Host ""
Write-Host "📝 Логи можно посмотреть командой: docker-compose logs -f" -ForegroundColor Gray