# Скрипт для сборки React-приложения и копирования его в статические файлы Django

# Определение путей на основе текущей директории скрипта
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $ScriptDir "guscha_django_frontend"
$DjangoDir = Join-Path $ScriptDir "guscha_django"
$BuildDir = Join-Path $FrontendDir "build"
$StaticDir = Join-Path $DjangoDir "static"
$TemplatesDir = Join-Path $DjangoDir "templates"

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
Write-ColorLog "Шаг 1/4: Сборка фронтенда..." -ForegroundColor Cyan
Push-Location $FrontendDir
try {
    # Установка зависимостей и сборка приложения
    Write-ColorLog "Установка npm зависимостей..." -ForegroundColor Yellow
    npm install
    
    Write-ColorLog "Сборка React-приложения..." -ForegroundColor Yellow
    npm run build
    
    if (-not (Test-Path $BuildDir)) {
        Write-ColorLog "Ошибка: Сборка не удалась, директория build не создана" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-ColorLog "Ошибка при сборке фронтенда: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

# Шаг 2: Подготовка директорий Django
Write-ColorLog "Шаг 2/4: Подготовка директорий Django..." -ForegroundColor Cyan

# Создаем директорию для статических файлов, если она не существует
if (-not (Test-Path $StaticDir)) {
    New-Item -ItemType Directory -Path $StaticDir -Force | Out-Null
    Write-ColorLog "Создана директория для статических файлов: $StaticDir" -ForegroundColor Green
}

# Создаем директорию для шаблонов, если она не существует
if (-not (Test-Path $TemplatesDir)) {
    New-Item -ItemType Directory -Path $TemplatesDir -Force | Out-Null
    Write-ColorLog "Создана директория для шаблонов: $TemplatesDir" -ForegroundColor Green
}

# Очищаем старые статические файлы (кроме axiosConfig.js)
Write-ColorLog "Очистка старых статических файлов..." -ForegroundColor Yellow
if (Test-Path $StaticDir) {
    # Сохраняем axiosConfig.js если он есть
    $AxiosConfigBackup = $null
    $AxiosConfigPath = Join-Path $StaticDir "js\axiosConfig.js"
    if (Test-Path $AxiosConfigPath) {
        $AxiosConfigBackup = Get-Content -Path $AxiosConfigPath -Raw
        Write-ColorLog "Сохранен существующий axiosConfig.js" -ForegroundColor Green
    }
    
    # Удаляем содержимое static директории
    Get-ChildItem -Path $StaticDir -Exclude "js" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    # Если директория js существует, удаляем все файлы кроме axiosConfig.js
    $JsDir = Join-Path $StaticDir "js"
    if (Test-Path $JsDir) {
        Get-ChildItem -Path $JsDir -Exclude "axiosConfig.js" | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    
    # Восстанавливаем axiosConfig.js
    if ($AxiosConfigBackup) {
        if (-not (Test-Path $JsDir)) {
            New-Item -ItemType Directory -Path $JsDir -Force | Out-Null
        }
        Set-Content -Path $AxiosConfigPath -Value $AxiosConfigBackup -Encoding UTF8
        Write-ColorLog "Восстановлен axiosConfig.js" -ForegroundColor Green
    }
}

# Шаг 3: Копирование файлов
Write-ColorLog "Шаг 3/4: Копирование файлов..." -ForegroundColor Cyan

# Копируем содержимое build/static/ в django/static/
$BuildStaticDir = Join-Path $BuildDir "static"
if (Test-Path $BuildStaticDir) {
    Copy-Item -Path "$BuildStaticDir\*" -Destination $StaticDir -Recurse -Force
    Write-ColorLog "Скопированы статические файлы из $BuildStaticDir в $StaticDir" -ForegroundColor Green
} else {
    Write-ColorLog "Предупреждение: Директория $BuildStaticDir не найдена" -ForegroundColor Yellow
}

# Копируем дополнительные статические файлы (favicon.ico, logo192.png, manifest.json)
$StaticFiles = @("favicon.ico", "logo192.png", "logo512.png", "manifest.json", "robots.txt")
foreach ($file in $StaticFiles) {
    $sourcePath = Join-Path $BuildDir $file
    $destPath = Join-Path $StaticDir $file
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $destPath -Force
        Write-ColorLog "Скопирован файл $file в $StaticDir" -ForegroundColor Green
    }
}

# Копируем index.html в корень static для Nginx
$IndexHtmlSource = Join-Path $BuildDir "index.html"
$IndexHtmlDest = Join-Path $StaticDir "index.html"
if (Test-Path $IndexHtmlSource) {
    Copy-Item -Path $IndexHtmlSource -Destination $IndexHtmlDest -Force
    Write-ColorLog "Скопирован index.html в $IndexHtmlDest" -ForegroundColor Green
} else {
    Write-ColorLog "Предупреждение: Файл $IndexHtmlSource не найден" -ForegroundColor Yellow
}

# Создаем директорию js, если она не существует
$JsDir = Join-Path $StaticDir "js"
if (-not (Test-Path $JsDir)) {
    New-Item -ItemType Directory -Path $JsDir -Force | Out-Null
    Write-ColorLog "Создана директория для JavaScript файлов: $JsDir" -ForegroundColor Green
}

# Копируем axiosConfig.js из Django папки, если он существует
$SourceAxiosConfig = Join-Path $DjangoDir "axiosConfig.js"
$DestAxiosConfig = Join-Path $JsDir "axiosConfig.js"
if (Test-Path $SourceAxiosConfig) {
    Copy-Item -Path $SourceAxiosConfig -Destination $DestAxiosConfig -Force
    Write-ColorLog "Скопирован axiosConfig.js из $SourceAxiosConfig в $DestAxiosConfig" -ForegroundColor Green
} else {
    Write-ColorLog "Предупреждение: axiosConfig.js не найден в $SourceAxiosConfig" -ForegroundColor Yellow
}

# Шаг 4: Обновление путей в index.html для Nginx
Write-ColorLog "Шаг 4/4: Обновление путей в index.html..." -ForegroundColor Cyan

if (Test-Path $IndexHtmlDest) {
    # Читаем содержимое index.html
    $IndexContent = Get-Content -Path $IndexHtmlDest -Raw
    
    # Добавляем скрипт axiosConfig.js после заголовка, если его там нет
    if ($IndexContent -notmatch 'axiosConfig.js') {
        $IndexContent = $IndexContent -replace '(</head>)', '<script src="/static/js/axiosConfig.js"></script>`n$1'
        Write-ColorLog "Добавлена ссылка на axiosConfig.js в index.html" -ForegroundColor Green
    }
    
    # Записываем обновленное содержимое
    Set-Content -Path $IndexHtmlDest -Value $IndexContent -Encoding UTF8
    Write-ColorLog "index.html обновлен" -ForegroundColor Green
}

Write-ColorLog "Сборка и копирование завершены успешно!" -ForegroundColor Green
Write-ColorLog "Статические файлы готовы в директории: $StaticDir" -ForegroundColor Green
Write-ColorLog "" -ForegroundColor White
Write-ColorLog "Для запуска приложения используйте Docker Compose:" -ForegroundColor Cyan
Write-ColorLog "cd $DjangoDir" -ForegroundColor Yellow
Write-ColorLog "docker-compose up -d" -ForegroundColor Yellow
Write-ColorLog "" -ForegroundColor White
Write-ColorLog "Приложение будет доступно по адресу: http://localhost" -ForegroundColor Green
