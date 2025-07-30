# Скрипт для сборки React-приложения и копирования его в статические файлы Django

# Определение путей
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $ScriptDir "guscha_django_frontend"
$DjangoDir = Join-Path $ScriptDir "guscha_django"
$BuildDir = Join-Path $FrontendDir "build"
$StaticDir = Join-Path $DjangoDir "static_root"

# Функция для логирования с цветами
function Write-ColorLog {
    param(
        [string]$Message,
        [System.ConsoleColor]$ForegroundColor = [System.ConsoleColor]::White
    )
    
    $originalColor = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $originalColor
}

# Проверка существования директорий
if (-not (Test-Path $FrontendDir)) {
    Write-ColorLog "Ошибка: Директория фронтенда не найдена: $FrontendDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $DjangoDir)) {
    Write-ColorLog "Ошибка: Директория Django не найдена: $DjangoDir" -ForegroundColor Red
    exit 1
}

# Шаг 1: Сборка фронтенда
Write-ColorLog "`n==== Сборка фронтенда ====" -ForegroundColor Cyan
Push-Location $FrontendDir
try {
    # Установка зависимостей
    Write-ColorLog "`nУстановка npm зависимостей..." -ForegroundColor Yellow
    npm install
    
    # Сборка приложения с отключенным ESLint
    Write-ColorLog "`nСборка React-приложения..." -ForegroundColor Yellow
    $env:DISABLE_ESLINT_PLUGIN = 'true'
    npm run build
    
    if (-not (Test-Path $BuildDir)) {
        Write-ColorLog "Ошибка: Сборка не удалась, директория build не создана" -ForegroundColor Red
        exit 1
    }
    
    Write-ColorLog "`nСборка завершена успешно!" -ForegroundColor Green
} catch {
    Write-ColorLog "Ошибка при сборке фронтенда: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

# Шаг 2: Подготовка директорий Django
Write-ColorLog "`n==== Подготовка директорий ====" -ForegroundColor Cyan

# Создаем директорию для статических файлов, если она не существует
if (-not (Test-Path $StaticDir)) {
    New-Item -ItemType Directory -Path $StaticDir -Force | Out-Null
    Write-ColorLog "Создана директория для статических файлов: $StaticDir" -ForegroundColor Green
}

# Сохраняем axiosConfig.js
$AxiosConfigBackup = $null
$AxiosConfigPath = Join-Path $StaticDir "js\axiosConfig.js"
if (Test-Path $AxiosConfigPath) {
    $AxiosConfigBackup = Get-Content -Path $AxiosConfigPath -Raw
    Write-ColorLog "Сохранен существующий axiosConfig.js" -ForegroundColor Green
}

# Очищаем старые статические файлы
Write-ColorLog "`nОчистка старых статических файлов..." -ForegroundColor Yellow
if (Test-Path $StaticDir) {
    Get-ChildItem -Path $StaticDir -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
}

# Шаг 3: Копирование файлов
Write-ColorLog "`n==== Копирование файлов ====" -ForegroundColor Cyan

# Копируем все файлы из build в static
Copy-Item -Path "$BuildDir\*" -Destination $StaticDir -Recurse -Force
Write-ColorLog "Скопированы файлы из $BuildDir в $StaticDir" -ForegroundColor Green

# Создаем директорию static/js, если она не существует
$StaticJsDir = Join-Path $StaticDir "static\js"
if (-not (Test-Path $StaticJsDir)) {
    New-Item -ItemType Directory -Path $StaticJsDir -Force | Out-Null
}

# Правильный путь для axiosConfig.js должен быть в static/js
$AxiosConfigPath = Join-Path $StaticJsDir "axiosConfig.js"

# Восстанавливаем или копируем axiosConfig.js
if ($AxiosConfigBackup) {
    Set-Content -Path $AxiosConfigPath -Value $AxiosConfigBackup -Encoding UTF8
    Write-ColorLog "Восстановлен axiosConfig.js" -ForegroundColor Green
} else {
    # Копируем axiosConfig.js из существующего места
    $SourceAxiosConfig = Join-Path $DjangoDir "static_root\js\axiosConfig.js"
    if (Test-Path $SourceAxiosConfig) {
        Copy-Item -Path $SourceAxiosConfig -Destination $AxiosConfigPath -Force
        Write-ColorLog "Скопирован axiosConfig.js из $SourceAxiosConfig" -ForegroundColor Green
    } else {
        # Если не найден, ищем в других местах
        $AlternativeSource = Join-Path $DjangoDir "axiosConfig.js"
        if (Test-Path $AlternativeSource) {
            Copy-Item -Path $AlternativeSource -Destination $AxiosConfigPath -Force
            Write-ColorLog "Скопирован axiosConfig.js из $AlternativeSource" -ForegroundColor Green
        }
    }
}

# Шаг 4: Обновление index.html
Write-ColorLog "`n==== Обновление index.html ====" -ForegroundColor Cyan

$IndexHtmlPath = Join-Path $StaticDir "index.html"
if (Test-Path $IndexHtmlPath) {
    # Читаем содержимое index.html
    $IndexContent = Get-Content -Path $IndexHtmlPath -Raw
    
    # Добавляем скрипт axiosConfig.js после заголовка, если его там нет
    if ($IndexContent -notmatch 'axiosConfig.js') {
        $IndexContent = $IndexContent -replace '(</head>)', "<script src=`"/static/js/axiosConfig.js`"></script>`r`n`$1"
        Write-ColorLog "Добавлена ссылка на axiosConfig.js в index.html" -ForegroundColor Green
    }
    
    # Записываем обновленное содержимое
    Set-Content -Path $IndexHtmlPath -Value $IndexContent -Encoding UTF8
    Write-ColorLog "index.html обновлен" -ForegroundColor Green
}

# Итоговая информация
Write-ColorLog "`n==== Сборка завершена ====" -ForegroundColor Green
Write-ColorLog "Статические файлы готовы в директории: $StaticDir" -ForegroundColor Green
Write-ColorLog "`nДля запуска приложения используйте Docker Compose:" -ForegroundColor Cyan
Write-ColorLog "cd $DjangoDir" -ForegroundColor Yellow
Write-ColorLog "docker-compose up -d" -ForegroundColor Yellow
Write-ColorLog "`nПриложение будет доступно по адресу: http://localhost" -ForegroundColor Green

# Проверка наличия Docker Compose
Write-ColorLog "`n==== Проверка Docker ====" -ForegroundColor Cyan
try {
    docker-compose version | Out-Null
    Write-ColorLog "Docker Compose установлен и готов к работе" -ForegroundColor Green
} catch {
    Write-ColorLog "Docker Compose не найден. Убедитесь, что Docker Desktop запущен" -ForegroundColor Yellow
}
