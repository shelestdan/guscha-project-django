# Скрипт очистки проекта Guscha
# Удаляет временные файлы, логи, build артефакты

param(
    [switch]$DryRun,
    [switch]$Deep
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "`n=== ОЧИСТКА ПРОЕКТА GUSCHA ===" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "РЕЖИМ ПРОВЕРКИ (файлы не будут удалены)" -ForegroundColor Yellow
    Write-Host ""
}

$totalFreed = 0

function Get-DirectorySize {
    param($Path)
    if (Test-Path $Path) {
        return (Get-ChildItem $Path -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    }
    return 0
}

function Remove-Directory {
    param($Path, $Description)
    
    if (Test-Path $Path) {
        $size = Get-DirectorySize $Path
        
        if ($DryRun) {
            Write-Host "  [ПРОВЕРКА] $Description : $([math]::Round($size, 2)) MB" -ForegroundColor Yellow
        } else {
            Write-Host "  Удаление $Description : $([math]::Round($size, 2)) MB" -ForegroundColor Green
            Remove-Item $Path -Recurse -Force
        }
        
        return $size
    } else {
        Write-Host "  [ПРОПУЩЕНО] $Description (не найдено)" -ForegroundColor Gray
        return 0
    }
}

# 1. Очистка логов
Write-Host "1. Очистка логов..." -ForegroundColor Cyan
$logsSize = 0
if (Test-Path "guscha_django/logs") {
    $logFiles = Get-ChildItem "guscha_django/logs" -Filter "*.log" -File
    foreach ($file in $logFiles) {
        $size = $file.Length / 1MB
        $logsSize += $size
        
        if ($DryRun) {
            Write-Host "  [ПРОВЕРКА] $($file.Name) : $([math]::Round($size, 2)) MB" -ForegroundColor Yellow
        } else {
            Write-Host "  Удаление $($file.Name) : $([math]::Round($size, 2)) MB" -ForegroundColor Green
            Remove-Item $file.FullName -Force
        }
    }
}
$totalFreed += $logsSize
Write-Host ""

# 2. Очистка профилей Django Silk
Write-Host "2. Очистка профилей Django Silk..." -ForegroundColor Cyan
$profilesSize = Remove-Directory "guscha_django/profiles" "Профили Django Silk"
$totalFreed += $profilesSize
Write-Host ""

# 3. Очистка Python cache
Write-Host "3. Очистка Python cache..." -ForegroundColor Cyan
$pycacheSize = 0
$pycacheDirs = Get-ChildItem -Path "guscha_django" -Include "__pycache__" -Recurse -Directory
foreach ($dir in $pycacheDirs) {
    $size = Get-DirectorySize $dir.FullName
    $pycacheSize += $size
    
    if ($DryRun) {
        Write-Host "  [ПРОВЕРКА] $($dir.FullName) : $([math]::Round($size, 2)) MB" -ForegroundColor Yellow
    } else {
        Remove-Item $dir.FullName -Recurse -Force
    }
}
if ($pycacheSize -gt 0) {
    Write-Host "  Очищено __pycache__: $([math]::Round($pycacheSize, 2)) MB" -ForegroundColor Green
}
$totalFreed += $pycacheSize
Write-Host ""

# 4. Очистка .pyc файлов
Write-Host "4. Очистка .pyc файлов..." -ForegroundColor Cyan
$pycFiles = Get-ChildItem -Path "guscha_django" -Filter "*.pyc" -Recurse -File
$pycSize = ($pycFiles | Measure-Object -Property Length -Sum).Sum / 1MB
if ($pycFiles.Count -gt 0) {
    if ($DryRun) {
        Write-Host "  [ПРОВЕРКА] Найдено $($pycFiles.Count) .pyc файлов : $([math]::Round($pycSize, 2)) MB" -ForegroundColor Yellow
    } else {
        $pycFiles | Remove-Item -Force
        Write-Host "  Удалено $($pycFiles.Count) .pyc файлов : $([math]::Round($pycSize, 2)) MB" -ForegroundColor Green
    }
    $totalFreed += $pycSize
}
Write-Host ""

# 5. Очистка Frontend build артефактов
Write-Host "5. Очистка Frontend build артефактов..." -ForegroundColor Cyan
$buildSize = Remove-Directory "guscha_django_frontend/build" "React build"
$totalFreed += $buildSize

$coverageSize = Remove-Directory "guscha_django_frontend/coverage" "Coverage отчёты"
$totalFreed += $coverageSize
Write-Host ""

# 6. Глубокая очистка (опционально)
if ($Deep) {
    Write-Host "6. ГЛУБОКАЯ ОЧИСТКА..." -ForegroundColor Red
    Write-Host "  ВНИМАНИЕ: Это удалит node_modules и venv!" -ForegroundColor Red
    Write-Host ""
    
    $nodeModulesSize = Remove-Directory "guscha_django_frontend/node_modules" "node_modules"
    $totalFreed += $nodeModulesSize
    
    $venvSize = Remove-Directory "guscha_django/venv" "Python venv"
    $totalFreed += $venvSize
    
    Write-Host ""
    Write-Host "  После глубокой очистки выполните:" -ForegroundColor Yellow
    Write-Host "    cd guscha_django_frontend && npm install" -ForegroundColor White
    Write-Host "    cd guscha_django && python -m venv venv && .\venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor White
    Write-Host ""
}

# Итоги
Write-Host "=== ИТОГИ ===" -ForegroundColor Cyan
Write-Host ""
if ($DryRun) {
    Write-Host "Можно освободить: $([math]::Round($totalFreed, 2)) MB" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Для реальной очистки запустите:" -ForegroundColor Green
    Write-Host "  .\cleanup-project.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Для глубокой очистки (включая node_modules и venv):" -ForegroundColor Green
    Write-Host "  .\cleanup-project.ps1 -Deep" -ForegroundColor White
} else {
    Write-Host "Освобождено: $([math]::Round($totalFreed, 2)) MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "Очистка завершена успешно! ✓" -ForegroundColor Green
}
Write-Host ""
