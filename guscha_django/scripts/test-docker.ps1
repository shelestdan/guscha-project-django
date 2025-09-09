# Тестовый скрипт для проверки Docker setup
# Использование: .\scripts\test-docker.ps1

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

function Test-DockerFile {
    param([string]$DockerFile)
    
    Write-ColorOutput $Blue "🔍 Тестирование $DockerFile..."
    
    # Проверка синтаксиса через попытку сборки с --target для первой стадии
    $result = & docker build -f $DockerFile --target base -t test-syntax . 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput $Green "✅ $DockerFile - синтаксис корректен"
        # Удаляем тестовый образ
        & docker rmi test-syntax -f 2>$null
        return $true
    } else {
        Write-ColorOutput $Red "❌ $DockerFile - ошибка синтаксиса:"
        Write-ColorOutput $Red $result
        return $false
    }
}

function Test-ComposeFile {
    param([string]$ComposeFile)
    
    Write-ColorOutput $Blue "🔍 Тестирование $ComposeFile..."
    
    $result = & docker-compose -f $ComposeFile config 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput $Green "✅ $ComposeFile - конфигурация корректна"
        return $true
    } else {
        Write-ColorOutput $Red "❌ $ComposeFile - ошибка конфигурации:"
        Write-ColorOutput $Red $result
        return $false
    }
}

function Test-RequiredFiles {
    $requiredFiles = @(
        "Dockerfile",
        "Dockerfile.telegram", 

        "docker-compose.dev.yml",
        "scripts/start.sh",
        ".dockerignore"
    )
    
    $allExist = $true
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-ColorOutput $Green "✅ $file найден"
        } else {
            Write-ColorOutput $Red "❌ $file отсутствует"
            $allExist = $false
        }
    }
    
    return $allExist
}

function Test-EnvFile {
    if (Test-Path ".env") {
        Write-ColorOutput $Green "✅ .env файл найден"
        
        # Проверка основных переменных
        $envContent = Get-Content ".env" -Raw
        $requiredVars = @("SECRET_KEY", "TELEGRAM_BOT_TOKEN", "REDIS_URL")
        
        foreach ($var in $requiredVars) {
            if ($envContent -match "$var=") {
                Write-ColorOutput $Green "  ✅ $var настроен"
            } else {
                Write-ColorOutput $Yellow "  ⚠️  $var не найден в .env"
            }
        }
        return $true
    } else {
        Write-ColorOutput $Yellow "⚠️  .env файл не найден"
        if (Test-Path ".env.example") {
            Write-ColorOutput $Blue "📋 .env.example доступен для копирования"
        }
        return $false
    }
}

# Основная логика тестирования
Write-ColorOutput $Blue @"
╔══════════════════════════════════════════════════════════════╗
║                    Docker Setup Test                        ║
║                   Guscha Django Project                     ║
╚══════════════════════════════════════════════════════════════╝
"@

$testsPassed = 0
$totalTests = 0

# Тест 1: Проверка наличия файлов
Write-ColorOutput $Blue "\n📁 Тест 1: Проверка наличия файлов"
$totalTests++
if (Test-RequiredFiles) {
    $testsPassed++
}

# Тест 2: Проверка .env файла
Write-ColorOutput $Blue "\n🔧 Тест 2: Проверка .env конфигурации"
$totalTests++
if (Test-EnvFile) {
    $testsPassed++
}

# Тест 3: Проверка docker-compose файлов
Write-ColorOutput $Blue "\n🐳 Тест 3: Проверка Docker Compose конфигураций"
$totalTests++
if (Test-ComposeFile "docker-compose.dev.yml") {
    $testsPassed++
}

# Тест 4: Проверка Dockerfile синтаксиса (упрощенная)
Write-ColorOutput $Blue "\n🔨 Тест 4: Проверка Dockerfile файлов"
$totalTests++
$dockerfilesOk = $true

# Проверяем наличие основных инструкций в Dockerfile
if (Test-Path "Dockerfile") {
    $dockerfileContent = Get-Content "Dockerfile" -Raw
    if ($dockerfileContent -match "FROM" -and $dockerfileContent -match "COPY" -and $dockerfileContent -match "RUN") {
        Write-ColorOutput $Green "✅ Dockerfile содержит основные инструкции"
    } else {
        Write-ColorOutput $Red "❌ Dockerfile не содержит необходимых инструкций"
        $dockerfilesOk = $false
    }
} else {
    $dockerfilesOk = $false
}

if (Test-Path "Dockerfile.telegram") {
    $telegramDockerfileContent = Get-Content "Dockerfile.telegram" -Raw
    if ($telegramDockerfileContent -match "FROM" -and $telegramDockerfileContent -match "COPY" -and $telegramDockerfileContent -match "CMD") {
        Write-ColorOutput $Green "✅ Dockerfile.telegram содержит основные инструкции"
    } else {
        Write-ColorOutput $Red "❌ Dockerfile.telegram не содержит необходимых инструкций"
        $dockerfilesOk = $false
    }
} else {
    $dockerfilesOk = $false
}

if ($dockerfilesOk) {
    $testsPassed++
}

# Результаты
Write-ColorOutput $Blue "\n📊 Результаты тестирования:"
Write-ColorOutput $Blue "═══════════════════════════════════"

if ($testsPassed -eq $totalTests) {
    Write-ColorOutput $Green "🎉 Все тесты пройдены! ($testsPassed/$totalTests)"
    Write-ColorOutput $Green "✅ Docker setup готов к использованию"
    Write-ColorOutput $Blue "\n🚀 Для запуска используйте:"
    Write-ColorOutput $Yellow "   .\scripts\start-docker.ps1 dev    # Режим разработки"
    Write-ColorOutput $Yellow "   .\scripts\start-docker.ps1 prod   # Продакшн режим"
} else {
    Write-ColorOutput $Red "❌ Тесты не пройдены: $testsPassed/$totalTests"
    Write-ColorOutput $Yellow "⚠️  Исправьте ошибки перед запуском Docker"
}

Write-ColorOutput $Blue "\n📚 Дополнительная информация:"
Write-ColorOutput $Blue "   Документация: DOCKER_SETUP.md"
Write-ColorOutput $Blue "   Быстрый старт: .\scripts\start-docker.ps1"