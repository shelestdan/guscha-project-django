# PowerShell-скрипт для сборки фронтенда и его размещения в бэкенде для production

# --- Цвета для вывода ---
$ColorInfo = [System.ConsoleColor]::Cyan
$ColorSuccess = [System.ConsoleColor]::Green
$ColorError = [System.ConsoleColor]::Red
$ColorWarning = [System.ConsoleColor]::Yellow
$ColorDefault = [System.ConsoleColor]::Gray

# --- Пути (НАДЕЖНАЯ ВЕРСИЯ) ---
# $PSScriptRoot - это встроенная переменная PowerShell, которая всегда указывает
# на директорию, в которой находится сам .ps1 файл. Это делает скрипт
# независимым от того, откуда его запускают.
$ProjectRoot = Get-Item (Join-Path $PSScriptRoot "guscha_project")
$FrontendDir = Join-Path $ProjectRoot.FullName "guscha-frontend"
$BuildDir = Join-Path $FrontendDir "build"
$DeployDir = Join-Path $ProjectRoot.FullName "backend/src/static"

# --- Функции ---
function Write-Log {
    param (
        [string]$Message,
        [System.ConsoleColor]$Color = $ColorDefault
    )
    Write-Host $Message -ForegroundColor $Color
}

# --- Начало выполнения ---
Write-Log "----------------------------------------------------" $ColorInfo
Write-Log "🚀 Начало сборки и развертывания фронтенда для Guscha..." $ColorInfo
Write-Log "----------------------------------------------------" $ColorInfo

# 1. Переход в директорию фронтенда
Write-Log "[1/5] Переход в директорию фронтенда: $FrontendDir"
try {
    Set-Location $FrontendDir
}
catch {
    Write-Log "[ОШИБКА] Не удалось найти директорию фронтенда: $FrontendDir" $ColorError
    exit 1
}

# 2. Установка зависимостей
Write-Log "[2/5] Установка npm-зависимостей (npm install)... Это может занять некоторое время." $ColorWarning
# Используем --legacy-peer-deps для совместимости, как было определено ранее. [память:30030232553782635]
npm install --legacy-peer-deps

# Проверка результата установки
if ($LASTEXITCODE -ne 0) {
    Write-Log "[ОШИБКА] Установка зависимостей завершилась с ошибкой. Пожалуйста, проверьте логи выше." $ColorError
    exit 1
}
Write-Log "[2/5] Зависимости успешно установлены!" $ColorSuccess

# 3. Сборка проекта
Write-Log "[3/5] Запуск сборки проекта (npm run build)... Это может занять несколько минут." $ColorWarning
npm run build

# Проверка результата сборки
if ($LASTEXITCODE -ne 0) {
    Write-Log "[ОШИБКА] Сборка проекта завершилась с ошибкой. Пожалуйста, проверьте логи выше." $ColorError
    exit 1
}

Write-Log "[3/5] Сборка успешно завершена!" $ColorSuccess

# 4. Очистка старых файлов и копирование новой версии
Write-Log "[4/5] Очистка старой версии из $DeployDir и копирование новых файлов."
if (Test-Path $DeployDir) {
    Remove-Item -Recurse -Force (Join-Path $DeployDir "*")
    Write-Log "     Старая версия удалена." $ColorSuccess
} else {
    Write-Log "     Директория для развертывания не найдена, создаем новую: $DeployDir" $ColorWarning
    New-Item -ItemType Directory -Force -Path $DeployDir
}

try {
    # Эта команда PowerShell копирует СОДЕРЖИМОЕ $BuildDir в $DeployDir
    Copy-Item -Path $BuildDir\/* -Destination $DeployDir -Recurse -Force
    Write-Log "     Файлы успешно скопированы." $ColorSuccess
}
catch {
    Write-Log "[ОШИБКА] Не удалось скопировать файлы. Проверьте права доступа и наличие директории `build`." $ColorError
    exit 1
}

# 5. ФИНАЛЬНАЯ ПРОВЕРКА И ИСПРАВЛЕНИЕ СТРУКТУРЫ
$NestedStaticDir = Join-Path $DeployDir "static"
if (Test-Path $NestedStaticDir) {
    Write-Log "[5/5] Обнаружена вложенная папка 'static'. Исправляю структуру..." $ColorWarning
    # Перемещаем все из static/static/* в static/*
    Move-Item -Path $NestedStaticDir\/* -Destination $DeployDir -Force
    # Удаляем теперь уже пустую папку static/static
    Remove-Item -Path $NestedStaticDir -Recurse -Force
    Write-Log "     Структура файлов исправлена." $ColorSuccess
}

Write-Log "----------------------------------------------------" $ColorSuccess
Write-Log "✅ ПРОЦЕСС ЗАВЕРШЕН!" $ColorSuccess
Write-Log "   Теперь вы можете запустить production-сервер:"
Write-Log "   cd guscha_project/backend" $ColorInfo
Write-Log "   python start_production_windows.py" $ColorInfo
Write-Log "----------------------------------------------------" $ColorSuccess 