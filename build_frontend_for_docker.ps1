#!/usr/bin/env pwsh
# Скрипт для сборки фронтенда перед Docker сборкой

Write-Host "🚀 Сборка фронтенда для Docker..." -ForegroundColor Green

# Переходим в директорию фронтенда
Set-Location "guscha_django_frontend"

if (-not (Test-Path "package.json")) {
    Write-Host "❌ Файл package.json не найден!" -ForegroundColor Red
    exit 1
}

# Очистка предыдущей сборки
Write-Host "🧹 Очистка предыдущей сборки..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
if (Test-Path "node_modules") {
    Remove-Item -Recurse -Force "node_modules"
}

# Установка зависимостей
Write-Host "📦 Установка зависимостей..." -ForegroundColor Yellow
npm ci

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при установке зависимостей!" -ForegroundColor Red
    exit 1
}

# Сборка продакшн версии (игнорируем предупреждения ESLint)
Write-Host "🔨 Сборка продакшн версии..." -ForegroundColor Green
$env:CI = "false"
$env:ESLINT_NO_DEV_ERRORS = "true"
$env:DISABLE_ESLINT_PLUGIN = "true"
npx react-scripts build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при сборке фронтенда!" -ForegroundColor Red
    exit 1
}

# Проверка результата сборки
if (Test-Path "build\index.html") {
    Write-Host "✅ Фронтенд успешно собран!" -ForegroundColor Green
    Write-Host "📁 Файлы сборки:" -ForegroundColor Cyan
    Get-ChildItem "build" -Recurse | Select-Object Name, Length | Format-Table
} else {
    Write-Host "❌ Файл index.html не найден в build директории!" -ForegroundColor Red
    exit 1
}

# Копирование в Django static_root
Set-Location ".."
Set-Location "guscha_django"

Write-Host "📋 Копирование статических файлов в Django..." -ForegroundColor Yellow

# Создаем директорию static_root если её нет
if (-not (Test-Path "static_root")) {
    New-Item -ItemType Directory -Path "static_root"
}

# Очищаем старые файлы
if (Test-Path "static_root\*") {
    Remove-Item -Recurse -Force "static_root\*"
}

# Копируем новые файлы
Copy-Item -Recurse -Force "..\guscha_django_frontend\build\*" "static_root\"

Write-Host "✅ Статические файлы скопированы в static_root!" -ForegroundColor Green
Write-Host "🚀 Теперь можно запускать Docker сборку!" -ForegroundColor Green

# Возвращаемся в корневую директорию
Set-Location ".."