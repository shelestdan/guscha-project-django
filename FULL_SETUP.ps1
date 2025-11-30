$ErrorActionPreference = "Stop"

Write-Host "🔧 GUSCHA PROJECT - FULL SETUP SCRIPT (Windows)" -ForegroundColor Cyan

# Define paths
$ProjectRoot = "d:\GusTest"
$FrontendPath = Join-Path $ProjectRoot "guscha_django_frontend"
$BackendPath = Join-Path $ProjectRoot "guscha_django"
$StaticRoot = Join-Path $BackendPath "static_root"

# 1. Build Frontend
Write-Host "📦 Building Frontend..." -ForegroundColor Yellow
Set-Location $FrontendPath

# Always install dependencies to ensure consistency
Write-Host "   Installing dependencies (this may take a few minutes)..."
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Error "npm install failed with exit code $LASTEXITCODE"
    exit 1
}

Write-Host "   Running build..."
$env:DISABLE_ESLINT_PLUGIN = "true"
npm run build

if (-not (Test-Path "build")) {
    Write-Error "Build failed. Directory 'build' not found."
    exit 1
}

# 2. Prepare Static Files
Write-Host "📂 Preparing Static Files..." -ForegroundColor Yellow

# Clean static_root
if (Test-Path $StaticRoot) {
    Remove-Item -Path $StaticRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $StaticRoot | Out-Null

# Copy build files
Write-Host "   Copying build artifacts..."
Copy-Item -Path "build\*" -Destination $StaticRoot -Recurse -Force

# Flatten static folder
$NestedStatic = Join-Path $StaticRoot "static"
if (Test-Path $NestedStatic) {
    Write-Host "   Flattening static directory structure for Nginx..."
    Get-ChildItem -Path $NestedStatic | Move-Item -Destination $StaticRoot -Force
    Remove-Item -Path $NestedStatic -Force
}

# 3. Docker Operations
Write-Host "🐳 Docker Operations..." -ForegroundColor Yellow
Set-Location $BackendPath

Write-Host "   Stopping existing containers..."
docker-compose -f docker-compose.dev.yml down

Write-Host "   Building and starting containers..."
docker-compose -f docker-compose.dev.yml up -d --build

# 4. Wait for DB and Migrations
Write-Host "⏳ Waiting for services to initialize (30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "🔄 Applying Migrations..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml exec -T django python manage.py migrate --noinput

# 5. Create Admin
Write-Host "👤 Checking/Creating Admin User..." -ForegroundColor Yellow
$CreateAdminScript = "
from apps.accounts.models import User
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')
django.setup()
try:
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser('admin@example.com', 'Admin123!@#')
        print('CREATED')
    else:
        print('EXISTS')
except Exception as e:
    print(f'ERROR: {e}')
"

# Remove newlines for the command argument
$OneLineScript = $CreateAdminScript -replace "`r`n", ";" -replace "`n", ";"

$AdminResult = docker-compose -f docker-compose.dev.yml exec -T django python manage.py shell -c "$OneLineScript"

if ($AdminResult -match "CREATED") {
    Write-Host "   ✅ Admin user created (admin@example.com / Admin123!@#)" -ForegroundColor Green
} elseif ($AdminResult -match "EXISTS") {
    Write-Host "   ℹ️  Admin user already exists" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Could not verify admin user: $AdminResult" -ForegroundColor Red
}

# 6. Final Check
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "   ---------------------------------------------------"
Write-Host "   🌐 Web:      http://localhost"
Write-Host "   🔧 API:      http://localhost/api/"
Write-Host "   👤 Admin:    http://localhost/admin/"
Write-Host "   ---------------------------------------------------"
Write-Host "   Credentials: admin@example.com / Admin123!@#"
