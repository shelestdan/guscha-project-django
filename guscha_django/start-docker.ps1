# Скрипт быстрого запуска Docker для Guscha Django Project
# Использование: .\start-docker.ps1 [dev|prod] [build]

param(
    [string]$Mode = "dev",
    [switch]$Build = $false
)

# Цвета для вывода
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Show-Header {
    Write-ColorOutput $Blue @"
╔══════════════════════════════════════════════════════════════╗
║                    Guscha Django Project                     ║
║                   Docker Setup Script                       ║
╚══════════════════════════════════════════════════════════════╝
"@
}

function Test-DockerInstalled {
    try {
        docker --version | Out-Null
        docker-compose --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Test-EnvFile {
    if (!(Test-Path ".env")) {
        Write-ColorOutput $Yellow "⚠️  Файл .env не найден!"
        if (Test-Path ".env.example") {
            Write-ColorOutput $Yellow "📋 Копирую .env.example в .env..."
            Copy-Item ".env.example" ".env"
            Write-ColorOutput $Yellow "✏️  Пожалуйста, отредактируйте .env файл с вашими настройками."
            return $false
        } else {
            Write-ColorOutput $Red "❌ Файл .env.example также не найден!"
            Write-ColorOutput $Red "Создайте .env файл с необходимыми настройками."
            return $false
        }
    }
    return $true
}

function Start-Services {
    param(
        [string]$ComposeFile,
        [bool]$ShouldBuild
    )
    
    Write-ColorOutput $Blue "🚀 Запуск сервисов..."
    
    if ($ShouldBuild) {
        Write-ColorOutput $Yellow "🔨 Пересборка образов..."
        & docker-compose -f $ComposeFile build
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput $Red "❌ Ошибка при сборке образов!"
            return $false
        }
    }
    
    Write-ColorOutput $Blue "▶️  Запуск контейнеров..."
    & docker-compose -f $ComposeFile up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput $Green "✅ Сервисы успешно запущены!"
        return $true
    } else {
        Write-ColorOutput $Red "❌ Ошибка при запуске сервисов!"
        return $false
    }
}

function Show-ServiceStatus {
    param([string]$ComposeFile)
    
    Write-ColorOutput $Blue "📊 Статус сервисов:"
    & docker-compose -f $ComposeFile ps
}

function Show-Logs {
    param([string]$ComposeFile)
    
    Write-ColorOutput $Blue "📋 Последние логи:"
    & docker-compose -f $ComposeFile logs --tail=10
}

function Show-URLs {
    param([string]$Mode)
    
    Write-ColorOutput $Green "🌐 Доступные URL:"
    
    if ($Mode -eq "prod") {
        Write-ColorOutput $Green "   Django (через Nginx): http://localhost"
        Write-ColorOutput $Green "   Django (HTTPS): https://localhost"
    } else {
        Write-ColorOutput $Green "   Django (прямой): http://localhost:8000"
        Write-ColorOutput $Green "   Django (через Nginx): http://localhost"
        Write-ColorOutput $Green "   PostgreSQL: localhost:5432"
        Write-ColorOutput $Green "   Redis: localhost:6379"
    }
}

function Show-Commands {
    param([string]$ComposeFile)
    
    Write-ColorOutput $Blue "🛠️  Полезные команды:"
    Write-ColorOutput $Yellow "   Просмотр логов: docker-compose -f $ComposeFile logs -f"
    Write-ColorOutput $Yellow "   Остановка: docker-compose -f $ComposeFile down"
    Write-ColorOutput $Yellow "   Перезапуск: docker-compose -f $ComposeFile restart"
    Write-ColorOutput $Yellow "   Django shell: docker-compose -f $ComposeFile exec django python manage.py shell"
    Write-ColorOutput $Yellow "   Миграции: docker-compose -f $ComposeFile exec django python manage.py migrate"
}

# Основная логика
Show-Header

# Проверка Docker
if (!(Test-DockerInstalled)) {
    Write-ColorOutput $Red "❌ Docker или Docker Compose не установлены!"
    Write-ColorOutput $Yellow "Установите Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
}

Write-ColorOutput $Green "✅ Docker установлен"

# Определение режима
$ComposeFile = if ($Mode -eq "prod") { "docker-compose.yml" } else { "docker-compose.dev.yml" }

if (!(Test-Path $ComposeFile)) {
    Write-ColorOutput $Red "❌ Файл $ComposeFile не найден!"
    exit 1
}

Write-ColorOutput $Blue "📋 Режим: $Mode"
Write-ColorOutput $Blue "📄 Конфигурация: $ComposeFile"

# Проверка .env файла
if (!(Test-EnvFile)) {
    Write-ColorOutput $Yellow "⏸️  Настройте .env файл и запустите скрипт снова."
    exit 1
}

Write-ColorOutput $Green "✅ Файл .env найден"

# Запуск сервисов
if (Start-Services -ComposeFile $ComposeFile -ShouldBuild $Build) {
    Start-Sleep -Seconds 3
    
    Show-ServiceStatus -ComposeFile $ComposeFile
    Write-Output ""
    Show-URLs -Mode $Mode
    Write-Output ""
    Show-Commands -ComposeFile $ComposeFile
    
    Write-ColorOutput $Green "🎉 Готово! Проект запущен успешно."
} else {
    Write-ColorOutput $Red "💥 Не удалось запустить проект."
    Write-ColorOutput $Yellow "📋 Проверьте логи для диагностики:"
    Show-Logs -ComposeFile $ComposeFile
    exit 1
}