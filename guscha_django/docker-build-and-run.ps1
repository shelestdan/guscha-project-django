#!/usr/bin/env pwsh
# Скрипт для сборки и запуска Docker контейнеров

Write-Host "🚀 Запуск сборки и развертывания Docker контейнеров..." -ForegroundColor Green

# Сначала собираем фронтенд
Write-Host "🔨 Сборка фронтенда..." -ForegroundColor Green
Set-Location ".."
& ".\build_frontend_for_docker.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при сборке фронтенда!" -ForegroundColor Red
    exit 1
}

# Возвращаемся в директорию Django
Set-Location "guscha_django"

# Остановка и удаление существующих контейнеров
Write-Host "🛑 Остановка существующих контейнеров..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# Удаление старых образов для пересборки
Write-Host "🗑️ Удаление старых образов..." -ForegroundColor Yellow
docker rmi guscha_django-django -f 2>$null
docker rmi guscha_django-telegram-bot -f 2>$null

# Очистка Docker кэша
Write-Host "🧹 Очистка Docker кэша..." -ForegroundColor Yellow
docker system prune -f

# Сборка образов с нуля
Write-Host "🔨 Сборка новых образов..." -ForegroundColor Green
docker-compose build --no-cache --pull

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при сборке образов!" -ForegroundColor Red
    exit 1
}

# Запуск контейнеров
Write-Host "🚀 Запуск контейнеров..." -ForegroundColor Green
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при запуске контейнеров!" -ForegroundColor Red
    exit 1
}

# Ожидание запуска сервисов
Write-Host "⏳ Ожидание запуска сервисов..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Проверка статуса контейнеров
Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose ps

# Показ логов
Write-Host "📋 Последние логи Django:" -ForegroundColor Cyan
docker-compose logs --tail=20 django

Write-Host "✅ Развертывание завершено!" -ForegroundColor Green
Write-Host "🌐 Приложение доступно по адресу: http://localhost" -ForegroundColor Green
Write-Host "🔧 Админ панель: http://localhost/admin/" -ForegroundColor Green
Write-Host "📊 Для просмотра логов: docker-compose logs -f" -ForegroundColor Yellow