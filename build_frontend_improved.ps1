# Параметры скрипта
param(
    [switch]$SkipBuild,        # Пропустить сборку фронтенда
    [switch]$SkipDocker,       # Пропустить перезапуск Docker
    [switch]$DevMode,          # Режим разработки (без Docker)
    [switch]$Verbose           # Подробное логирование
)

# Улучшенный скрипт для сборки React-приложения с полной интеграцией Docker-контейнеров
# Обеспечивает бесшовное обновление фронтенда в продакшене

# Определение путей на основе текущей директории скрипта
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $ScriptDir "guscha_django_frontend"
$DjangoDir = Join-Path $ScriptDir "guscha_django"
$BuildDir = Join-Path $FrontendDir "build"
$StaticDir = Join-Path $DjangoDir "static"
$StaticRootDir = Join-Path $DjangoDir "static_root"
$TemplatesDir = Join-Path $DjangoDir "templates"

# Функции для логирования и утилит
function Write-ColorLog {
    param(
        [string]$Message,
        [System.ConsoleColor]$ForegroundColor = [System.ConsoleColor]::White,
        [switch]$NoNewline
    )
    
    $originalColor = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($NoNewline) {
        Write-Host $Message -NoNewline
    } else {
        Write-Output $Message
    }
    $host.UI.RawUI.ForegroundColor = $originalColor
}

function Write-Step {
    param([string]$StepNumber, [string]$Description)
    Write-ColorLog "" -ForegroundColor Cyan
    Write-ColorLog "=== Шаг $StepNumber`: $Description ===" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-ColorLog "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-ColorLog "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-ColorLog "✗ $Message" -ForegroundColor Red
}

function Test-DockerRunning {
    try {
        docker ps > $null 2>&1
        return $true
    } catch {
        return $false
    }
}

function Wait-ForContainer {
    param([string]$ContainerName, [int]$TimeoutSeconds = 30)
    
    Write-ColorLog "Ожидание запуска контейнера $ContainerName..." -ForegroundColor Yellow
    $elapsed = 0
    
    while ($elapsed -lt $TimeoutSeconds) {
        $status = docker ps --filter "name=$ContainerName" --filter "status=running" --format "{{.Names}}" 2>$null
        if ($status -eq $ContainerName) {
            Write-Success "Контейнер $ContainerName запущен"
            return $true
        }
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-ColorLog "." -NoNewline -ForegroundColor Yellow
    }
    
    Write-Error "Таймаут ожидания запуска контейнера $ContainerName"
    return $false
}

# Начальные проверки
Write-ColorLog "🚀 Запуск улучшенного скрипта сборки фронтенда" -ForegroundColor Magenta
Write-ColorLog "Время начала: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

if ($Verbose) {
    Write-ColorLog "Параметры:" -ForegroundColor Gray
    Write-ColorLog "  - SkipBuild: $SkipBuild" -ForegroundColor Gray
    Write-ColorLog "  - SkipDocker: $SkipDocker" -ForegroundColor Gray
    Write-ColorLog "  - DevMode: $DevMode" -ForegroundColor Gray
    Write-ColorLog "  - Verbose: $Verbose" -ForegroundColor Gray
}

# Проверка существования директорий
if (-not (Test-Path $FrontendDir)) {
    Write-Error "Директория фронтенда не найдена: $FrontendDir"
    exit 1
}

if (-not (Test-Path $DjangoDir)) {
    Write-Error "Директория Django не найдена: $DjangoDir"
    exit 1
}

# Проверка Docker (если не в режиме разработки)
if (-not $DevMode -and -not $SkipDocker) {
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker не запущен или недоступен"
        Write-ColorLog "Запустите Docker Desktop или используйте параметр -DevMode" -ForegroundColor Yellow
        exit 1
    }
    Write-Success "Docker доступен"
}

Write-Success "Все предварительные проверки пройдены"

# Шаг 1: Сборка фронтенда
if (-not $SkipBuild) {
    Write-Step "1" "Сборка React-фронтенда"
    Push-Location $FrontendDir
    try {
        # Проверка package.json
        if (-not (Test-Path "package.json")) {
            Write-Error "package.json не найден в $FrontendDir"
            exit 1
        }
        
        # Установка зависимостей
        Write-ColorLog "Установка npm зависимостей..." -ForegroundColor Yellow
        $npmInstallResult = npm install 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Ошибка установки зависимостей: $npmInstallResult"
            exit 1
        }
        Write-Success "Зависимости установлены"
        
        # Сборка приложения
        Write-ColorLog "Сборка React-приложения..." -ForegroundColor Yellow
        $npmBuildResult = npm run build 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Ошибка сборки: $npmBuildResult"
            exit 1
        }
        
        if (-not (Test-Path $BuildDir)) {
            Write-Error "Сборка не удалась, директория build не создана"
            exit 1
        }
        
        # Проверка содержимого сборки
        $buildFiles = Get-ChildItem $BuildDir -Recurse | Measure-Object
        Write-Success "Сборка завершена успешно ($($buildFiles.Count) файлов)"
        
    } catch {
        Write-Error "Ошибка при сборке фронтенда: $_"
        exit 1
    } finally {
        Pop-Location
    }
} else {
    Write-Step "1" "Пропуск сборки фронтенда (параметр -SkipBuild)"
    if (-not (Test-Path $BuildDir)) {
        Write-Error "Директория build не найдена, но сборка пропущена"
        exit 1
    }
    Write-Success "Используется существующая сборка"
}

# Шаг 2: Подготовка директорий Django
Write-Step "2" "Подготовка директорий Django"

# Создаем необходимые директории
@($StaticDir, $StaticRootDir, $TemplatesDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Success "Создана директория: $_"
    }
}

# Проверка прав доступа
try {
    $testFile = Join-Path $StaticRootDir "test_write.tmp"
    "test" | Out-File -FilePath $testFile -Encoding UTF8
    Remove-Item $testFile -Force
    Write-Success "Права доступа к директориям проверены"
} catch {
    Write-Error "Нет прав записи в $StaticRootDir`: $_"
    exit 1
}

# Очистка и резервное копирование
Write-ColorLog "Очистка старых статических файлов..." -ForegroundColor Yellow

# Функция для сохранения важных файлов
function Backup-ImportantFiles {
    param([string]$SourceDir)
    
    $backups = @{}
    $importantFiles = @(
        "js\axiosConfig.js",
        "admin\*"  # Сохраняем админские файлы Django
    )
    
    foreach ($pattern in $importantFiles) {
        $files = Get-ChildItem -Path $SourceDir -Filter $pattern -Recurse -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            $relativePath = $file.FullName.Substring($SourceDir.Length + 1)
            if ($file.PSIsContainer -eq $false) {
                $backups[$relativePath] = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
            }
        }
    }
    
    return $backups
}

# Резервное копирование важных файлов из обеих директорий
$staticBackups = @{}
$staticRootBackups = @{}

if (Test-Path $StaticDir) {
    $staticBackups = Backup-ImportantFiles $StaticDir
    Write-Success "Сохранено $($staticBackups.Count) важных файлов из static/"
}

if (Test-Path $StaticRootDir) {
    $staticRootBackups = Backup-ImportantFiles $StaticRootDir
    Write-Success "Сохранено $($staticRootBackups.Count) важных файлов из static_root/"
}

# Очистка директорий
@($StaticDir, $StaticRootDir) | ForEach-Object {
    if (Test-Path $_) {
        Get-ChildItem -Path $_ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Success "Очищена директория: $_"
    }
}

# Шаг 3: Копирование файлов
Write-Step "3" "Копирование файлов фронтенда"

# Функция для копирования файлов с проверкой
function Copy-WithValidation {
    param([string]$Source, [string]$Destination, [string]$Description)
    
    if (Test-Path $Source) {
        try {
            Copy-Item -Path $Source -Destination $Destination -Recurse -Force
            $fileCount = (Get-ChildItem -Path $Destination -Recurse -File | Measure-Object).Count
            Write-Success "$Description ($fileCount файлов)"
            return $true
        } catch {
            Write-Error "Ошибка копирования $Description`: $_"
            return $false
        }
    } else {
        Write-Warning "Источник не найден: $Source"
        return $false
    }
}

# Копирование в static/ (для разработки)
Write-ColorLog "Копирование в static/ (режим разработки)..." -ForegroundColor Yellow
$BuildStaticDir = Join-Path $BuildDir "static"
if (Test-Path $BuildStaticDir) {
    Copy-WithValidation "$BuildStaticDir\*" $StaticDir "Статические файлы в static/"
}

# Копирование в static_root/ (для продакшена)
Write-ColorLog "Копирование в static_root/ (режим продакшена)..." -ForegroundColor Yellow

# Копирование React файлов в static_root/ (корень для nginx)
$ReactFiles = @("favicon.ico", "logo192.png", "logo512.png", "manifest.json", "robots.txt", "index.html")
foreach ($file in $ReactFiles) {
    $sourcePath = Join-Path $BuildDir $file
    
    # Копируем в static/ для разработки
    $destPathStatic = Join-Path $StaticDir $file
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $destPathStatic -Force
    }
    
    # Копируем в static_root/ для продакшена
    $destPathRoot = Join-Path $StaticRootDir $file
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $destPathRoot -Force
    }
}

# Копирование статических ресурсов React в static_root/static/
$StaticRootStaticDir = Join-Path $StaticRootDir "static"
if (-not (Test-Path $StaticRootStaticDir)) {
    New-Item -ItemType Directory -Path $StaticRootStaticDir -Force | Out-Null
}

if (Test-Path $BuildStaticDir) {
    Copy-WithValidation "$BuildStaticDir\*" $StaticRootStaticDir "Статические ресурсы в static_root/static/"
}

Write-Success "Все файлы React скопированы в обе директории"

# Восстановление важных файлов
function Restore-ImportantFiles {
    param([string]$TargetDir, [hashtable]$Backups)
    
    foreach ($relativePath in $Backups.Keys) {
        $targetPath = Join-Path $TargetDir $relativePath
        $targetDirPath = Split-Path $targetPath -Parent
        
        if (-not (Test-Path $targetDirPath)) {
            New-Item -ItemType Directory -Path $targetDirPath -Force | Out-Null
        }
        
        try {
            Set-Content -Path $targetPath -Value $Backups[$relativePath] -Encoding UTF8
            Write-Success "Восстановлен: $relativePath"
        } catch {
            Write-Warning "Не удалось восстановить $relativePath`: $_"
        }
    }
}

# Восстановление важных файлов
if ($staticBackups.Count -gt 0) {
    Write-ColorLog "Восстановление важных файлов в static/..." -ForegroundColor Yellow
    Restore-ImportantFiles $StaticDir $staticBackups
}

if ($staticRootBackups.Count -gt 0) {
    Write-ColorLog "Восстановление важных файлов в static_root/..." -ForegroundColor Yellow
    Restore-ImportantFiles $StaticRootDir $staticRootBackups
}

# Копирование axiosConfig.js в обе директории
$SourceAxiosConfig = Join-Path $DjangoDir "axiosConfig.js"
if (Test-Path $SourceAxiosConfig) {
    # В static/js/
    $JsDir = Join-Path $StaticDir "js"
    if (-not (Test-Path $JsDir)) {
        New-Item -ItemType Directory -Path $JsDir -Force | Out-Null
    }
    $DestAxiosConfig = Join-Path $JsDir "axiosConfig.js"
    Copy-Item -Path $SourceAxiosConfig -Destination $DestAxiosConfig -Force
    
    # В static_root/js/
    $JsRootDir = Join-Path $StaticRootDir "js"
    if (-not (Test-Path $JsRootDir)) {
        New-Item -ItemType Directory -Path $JsRootDir -Force | Out-Null
    }
    $DestAxiosConfigRoot = Join-Path $JsRootDir "axiosConfig.js"
    Copy-Item -Path $SourceAxiosConfig -Destination $DestAxiosConfigRoot -Force
    
    Write-Success "axiosConfig.js скопирован в обе директории"
} else {
    Write-Warning "axiosConfig.js не найден в $SourceAxiosConfig"
}

# Шаг 4: Обновление index.html файлов
Write-Step "4" "Обновление index.html файлов"

function Update-IndexHtml {
    param([string]$IndexPath, [string]$Description)
    
    if (Test-Path $IndexPath) {
        try {
            $IndexContent = Get-Content -Path $IndexPath -Raw
            
            # Добавляем скрипт axiosConfig.js после заголовка, если его там нет
            if ($IndexContent -notmatch 'axiosConfig.js') {
                $IndexContent = $IndexContent -replace '(</head>)', '<script src="/static/js/axiosConfig.js"></script>$1'
                Set-Content -Path $IndexPath -Value $IndexContent -Encoding UTF8
                Write-Success "$Description - добавлена ссылка на axiosConfig.js"
            } else {
                Write-Success "$Description - ссылка на axiosConfig.js уже существует"
            }
        } catch {
            Write-Warning "Ошибка обновления $Description`: $_"
        }
    } else {
        Write-Warning "$Description не найден: $IndexPath"
    }
}

# Обновляем index.html в обеих директориях
Update-IndexHtml (Join-Path $StaticDir "index.html") "index.html в static/"
Update-IndexHtml (Join-Path $StaticRootDir "index.html") "index.html в static_root/"

# Шаг 5: Сборка статических файлов Django и перезапуск контейнеров
if (-not $DevMode -and -not $SkipDocker) {
    Write-Step "5" "Интеграция с Docker-контейнерами"
    
    Push-Location $DjangoDir
    try {
        # Проверка текущего состояния контейнеров
        Write-ColorLog "Проверка состояния контейнеров..." -ForegroundColor Yellow
        $runningContainers = docker-compose ps --services --filter "status=running" 2>$null
        
        if ($runningContainers) {
            Write-Success "Найдены запущенные контейнеры: $($runningContainers -join ', ')"
            
            # Выполнение collectstatic в Django контейнере
            Write-ColorLog "Выполнение collectstatic в Django контейнере..." -ForegroundColor Yellow
            $collectstaticResult = docker-compose exec -T django python manage.py collectstatic --noinput 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "collectstatic выполнен успешно"
            } else {
                Write-Warning "Ошибка collectstatic: $collectstaticResult"
            }
            
            # Перезапуск nginx для обновления статики
            Write-ColorLog "Перезапуск nginx для обновления кэша..." -ForegroundColor Yellow
            docker-compose restart nginx
            if ($LASTEXITCODE -eq 0) {
                Write-Success "nginx перезапущен"
            } else {
                Write-Warning "Ошибка перезапуска nginx"
            }
            
            # Проверка доступности приложения
            Write-ColorLog "Проверка доступности приложения..." -ForegroundColor Yellow
            Start-Sleep -Seconds 3
            
            try {
                $response = Invoke-WebRequest -Uri "http://localhost/nginx-health" -TimeoutSec 10 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-Success "Приложение доступно и работает корректно"
                }
            } catch {
                Write-Warning "Приложение может быть недоступно: $_"
            }
            
        } else {
            Write-ColorLog "Контейнеры не запущены. Запуск полной сборки..." -ForegroundColor Yellow
            
            # Остановка существующих контейнеров
            docker-compose down 2>$null
            
            # Сборка и запуск
            Write-ColorLog "Сборка Docker образов..." -ForegroundColor Yellow
            docker-compose build --no-cache
            
            Write-ColorLog "Запуск контейнеров..." -ForegroundColor Yellow
            docker-compose up -d
            
            # Ожидание запуска
            if (Wait-ForContainer "guscha-django" 60) {
                # Выполнение collectstatic
                Start-Sleep -Seconds 5
                Write-ColorLog "Выполнение collectstatic..." -ForegroundColor Yellow
                docker-compose exec -T django python manage.py collectstatic --noinput
                
                Write-Success "Контейнеры запущены и настроены"
            } else {
                Write-Error "Не удалось запустить контейнеры"
            }
        }
        
    } catch {
        Write-Error "Ошибка работы с Docker: $_"
    } finally {
        Pop-Location
    }
} else {
    if ($DevMode) {
        Write-Step "5" "Режим разработки - пропуск Docker интеграции"
        Write-Success "Файлы готовы для разработки в static/"
    } else {
        Write-Step "5" "Пропуск Docker интеграции (параметр -SkipDocker)"
        Write-Success "Файлы готовы в static_root/ для ручного развертывания"
    }
}

# Финальный отчет
Write-ColorLog "\n🎉 Сборка завершена успешно!" -ForegroundColor Green
Write-ColorLog "Время завершения: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

Write-ColorLog "\n📁 Статические файлы размещены в:" -ForegroundColor Cyan
Write-ColorLog "  • static/ - для разработки" -ForegroundColor White
Write-ColorLog "  • static_root/ - для продакшена (Docker)" -ForegroundColor White

if (-not $DevMode -and -not $SkipDocker) {
    Write-ColorLog "\n🌐 Приложение доступно по адресам:" -ForegroundColor Cyan
    Write-ColorLog "  • http://localhost - основное приложение" -ForegroundColor White
    Write-ColorLog "  • http://localhost/admin - Django админка" -ForegroundColor White
    Write-ColorLog "  • http://localhost/nginx-health - проверка nginx" -ForegroundColor White
} else {
    Write-ColorLog "\n🔧 Для запуска в продакшене выполните:" -ForegroundColor Cyan
    Write-ColorLog "  cd $DjangoDir" -ForegroundColor Yellow
    Write-ColorLog "  docker-compose up -d" -ForegroundColor Yellow
}

Write-ColorLog "\n✨ Бесшовное обновление фронтенда завершено!" -ForegroundColor Magenta
