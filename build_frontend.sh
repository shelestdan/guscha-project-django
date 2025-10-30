#!/bin/bash

# ============================================================================
# FRONTEND BUILD SCRIPT FOR macOS/Linux
# ============================================================================
# This script builds the React frontend and integrates it with Django
# Equivalent to build_frontend_improved.ps1 for Windows
#
# Usage:
#   ./build_frontend.sh                 # Standard build
#   ./build_frontend.sh --skip-build    # Skip npm build
#   ./build_frontend.sh --dev-mode      # Development mode (no Docker)
#   ./build_frontend.sh --force-refresh # Full Docker restart

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_BUILD=false
SKIP_DOCKER=false
DEV_MODE=false
FORCE_REFRESH=false
RESTART_CONTAINERS=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --dev-mode)
            DEV_MODE=true
            shift
            ;;
        --force-refresh)
            FORCE_REFRESH=true
            shift
            ;;
        --restart-containers)
            RESTART_CONTAINERS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Logging functions
log_step() {
    echo -e "\n${CYAN}=== Step $1: $2 ===${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Determine paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRONTEND_DIR="$SCRIPT_DIR/guscha_django_frontend"
DJANGO_DIR="$SCRIPT_DIR/guscha_django"
BUILD_DIR="$FRONTEND_DIR/build"
STATIC_DIR="$DJANGO_DIR/static"
STATIC_ROOT_DIR="$DJANGO_DIR/static_root"
TEMPLATES_DIR="$DJANGO_DIR/templates"

echo -e "${MAGENTA}🚀 Starting frontend build script${NC}"
echo -e "${CYAN}Time: $(date '+%Y-%m-%d %H:%M:%S')${NC}"

if [ "$VERBOSE" = true ]; then
    echo -e "${CYAN}Parameters:${NC}"
    echo "  - SkipBuild: $SKIP_BUILD"
    echo "  - SkipDocker: $SKIP_DOCKER"
    echo "  - DevMode: $DEV_MODE"
    echo "  - ForceRefresh: $FORCE_REFRESH"
    echo "  - RestartContainers: $RESTART_CONTAINERS"
fi

# Check directories
if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

if [ ! -d "$DJANGO_DIR" ]; then
    log_error "Django directory not found: $DJANGO_DIR"
    exit 1
fi

# Check Docker (if not in dev mode)
if [ "$DEV_MODE" = false ] && [ "$SKIP_DOCKER" = false ]; then
    if ! docker ps &> /dev/null; then
        log_error "Docker is not running or not accessible"
        log_warning "Start Docker Desktop or use --dev-mode"
        exit 1
    fi
    log_success "Docker is available"
fi

log_success "All preliminary checks passed"

# Step 1: Build React frontend
if [ "$SKIP_BUILD" = false ]; then
    log_step "1" "Building React frontend"
    cd "$FRONTEND_DIR"
    
    if [ ! -f "package.json" ]; then
        log_error "package.json not found in $FRONTEND_DIR"
        exit 1
    fi
    
    echo "Installing npm dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        log_error "npm install failed"
        exit 1
    fi
    log_success "Dependencies installed"
    
    echo "Building React application..."
    npm run build
    if [ $? -ne 0 ]; then
        log_error "npm build failed"
        exit 1
    fi
    
    if [ ! -d "$BUILD_DIR" ]; then
        log_error "Build failed, build directory not created"
        exit 1
    fi
    
    FILE_COUNT=$(find "$BUILD_DIR" -type f | wc -l)
    log_success "Build completed successfully ($FILE_COUNT files)"
    
    cd "$SCRIPT_DIR"
else
    log_step "1" "Skipping frontend build (--skip-build)"
    if [ ! -d "$BUILD_DIR" ]; then
        log_error "Build directory not found, but build was skipped"
        exit 1
    fi
    log_success "Using existing build"
fi

# Step 2: Prepare Django directories
log_step "2" "Preparing Django directories"

# Create necessary directories
for dir in "$STATIC_DIR" "$STATIC_ROOT_DIR" "$TEMPLATES_DIR"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log_success "Created directory: $dir"
    fi
done

# Check write permissions
TEST_FILE="$STATIC_ROOT_DIR/test_write.tmp"
if echo "test" > "$TEST_FILE" 2>/dev/null; then
    rm -f "$TEST_FILE"
    log_success "Write permissions verified"
else
    log_error "No write permissions in $STATIC_ROOT_DIR"
    exit 1
fi

# Step 3: Backup important files
log_step "3" "Backing up important files"

BACKUP_DIR="/tmp/guscha_backup_$(date +%s)"
mkdir -p "$BACKUP_DIR"

# Backup axiosConfig.js if exists
if [ -f "$STATIC_DIR/js/axiosConfig.js" ]; then
    mkdir -p "$BACKUP_DIR/static/js"
    cp "$STATIC_DIR/js/axiosConfig.js" "$BACKUP_DIR/static/js/"
    log_success "Backed up axiosConfig.js from static/"
fi

if [ -f "$STATIC_ROOT_DIR/js/axiosConfig.js" ]; then
    mkdir -p "$BACKUP_DIR/static_root/js"
    cp "$STATIC_ROOT_DIR/js/axiosConfig.js" "$BACKUP_DIR/static_root/js/"
    log_success "Backed up axiosConfig.js from static_root/"
fi

# Clear directories
echo "Cleaning old static files..."
rm -rf "${STATIC_DIR:?}"/*
rm -rf "${STATIC_ROOT_DIR:?}"/*
log_success "Directories cleaned"

# Step 4: Copy files
log_step "4" "Copying frontend files"

# Copy to static/ (for development)
echo "Copying to static/ (development mode)..."
if [ -d "$BUILD_DIR/static" ]; then
    cp -r "$BUILD_DIR/static"/* "$STATIC_DIR/"
    log_success "Static files copied to static/"
fi

# Copy to static_root/ (for production)
echo "Copying to static_root/ (production mode)..."

# Copy React root files
REACT_FILES=("favicon.ico" "logo192.png" "logo512.png" "manifest.json" "robots.txt" "index.html")
for file in "${REACT_FILES[@]}"; do
    if [ -f "$BUILD_DIR/$file" ]; then
        cp "$BUILD_DIR/$file" "$STATIC_DIR/"
        cp "$BUILD_DIR/$file" "$STATIC_ROOT_DIR/"
    fi
done

# Copy static resources to static_root
if [ -d "$BUILD_DIR/static" ]; then
    cp -r "$BUILD_DIR/static"/* "$STATIC_ROOT_DIR/"
    log_success "Static resources copied to static_root/"
fi

# Restore important files
if [ -f "$BACKUP_DIR/static/js/axiosConfig.js" ]; then
    mkdir -p "$STATIC_DIR/js"
    cp "$BACKUP_DIR/static/js/axiosConfig.js" "$STATIC_DIR/js/"
    log_success "Restored axiosConfig.js to static/"
fi

if [ -f "$BACKUP_DIR/static_root/js/axiosConfig.js" ]; then
    mkdir -p "$STATIC_ROOT_DIR/js"
    cp "$BACKUP_DIR/static_root/js/axiosConfig.js" "$STATIC_ROOT_DIR/js/"
    log_success "Restored axiosConfig.js to static_root/"
fi

# Copy axiosConfig.js from static to static_root if exists
if [ -f "$STATIC_DIR/js/axiosConfig.js" ]; then
    mkdir -p "$STATIC_ROOT_DIR/js"
    cp "$STATIC_DIR/js/axiosConfig.js" "$STATIC_ROOT_DIR/js/"
    log_success "axiosConfig.js copied from static/js/ to static_root/js/"
fi

# Cleanup backup
rm -rf "$BACKUP_DIR"

# Step 5: Update index.html files
log_step "5" "Updating index.html files"

update_index_html() {
    local INDEX_PATH="$1"
    local DESCRIPTION="$2"
    
    if [ -f "$INDEX_PATH" ]; then
        if ! grep -q "axiosConfig.js" "$INDEX_PATH"; then
            sed -i.bak 's|</head>|<script src="/static/js/axiosConfig.js"></script></head>|' "$INDEX_PATH"
            rm -f "${INDEX_PATH}.bak"
            log_success "$DESCRIPTION - added axiosConfig.js link"
        else
            log_success "$DESCRIPTION - axiosConfig.js link already exists"
        fi
    else
        log_warning "$DESCRIPTION not found: $INDEX_PATH"
    fi
}

update_index_html "$STATIC_DIR/index.html" "index.html in static/"
update_index_html "$STATIC_ROOT_DIR/index.html" "index.html in static_root/"

# Step 6: Docker integration
if [ "$DEV_MODE" = false ] && [ "$SKIP_DOCKER" = false ]; then
    log_step "6" "Docker integration"
    
    cd "$DJANGO_DIR"
    
    echo "Checking container status..."
    RUNNING_CONTAINERS=$(docker-compose ps --services --filter "status=running" 2>/dev/null || echo "")
    
    if [ -n "$RUNNING_CONTAINERS" ]; then
        log_success "Found running containers: $RUNNING_CONTAINERS"
        
        if [ "$RESTART_CONTAINERS" = true ]; then
            echo "Restarting containers (down + up -d)..."
            docker-compose down
            log_success "Containers stopped"
            
            docker-compose up -d
            log_success "Containers started"
            
            sleep 10
            echo "Running collectstatic..."
            docker-compose exec -T django python manage.py collectstatic --noinput
            log_success "Containers restarted and collectstatic completed"
            
        elif [ "$FORCE_REFRESH" = true ]; then
            echo "Full cache refresh (down + up)..."
            docker-compose down
            log_success "All containers stopped"
            
            docker-compose up -d
            log_success "Containers restarted"
            
            sleep 10
            echo "Running collectstatic..."
            docker-compose exec -T django python manage.py collectstatic --noinput
            log_success "Full cache refresh completed"
            
        else
            # Standard update
            echo "Running collectstatic in Django container..."
            docker-compose exec -T django python manage.py collectstatic --noinput
            log_success "collectstatic completed"
            
            echo "Restarting nginx..."
            docker-compose restart nginx
            log_success "nginx restarted"
        fi
        
        # Check application availability
        echo "Checking application availability..."
        sleep 3
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost/nginx-health" | grep -q "200"; then
            log_success "Application is available and working"
        else
            log_warning "Application may not be available"
        fi
        
    else
        echo "Containers not running. Starting full build..."
        
        docker-compose down 2>/dev/null || true
        
        echo "Building Docker images..."
        docker-compose build --no-cache
        
        echo "Starting containers..."
        docker-compose up -d
        
        sleep 15
        
        echo "Running collectstatic..."
        docker-compose exec -T django python manage.py collectstatic --noinput
        
        log_success "Containers started and configured"
    fi
    
    cd "$SCRIPT_DIR"
else
    if [ "$DEV_MODE" = true ]; then
        log_step "6" "Development mode - skipping Docker integration"
        log_success "Files ready for development in static/"
    else
        log_step "6" "Skipping Docker integration (--skip-docker)"
        log_success "Files ready in static_root/ for manual deployment"
    fi
fi

# Final report
echo
echo -e "${GREEN}🎉 Build completed successfully!${NC}"
echo -e "${CYAN}Time: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo
echo -e "${CYAN}📁 Static files placed in:${NC}"
echo "  • static/ - for development"
echo "  • static_root/ - for production (Docker)"

if [ "$DEV_MODE" = false ] && [ "$SKIP_DOCKER" = false ]; then
    echo
    echo -e "${CYAN}🌐 Application available at:${NC}"
    echo "  • http://localhost - main application"
    echo "  • http://localhost/admin/ - Django admin"
    echo "  • http://localhost/nginx-health - nginx health check"
else
    echo
    echo -e "${CYAN}🔧 To run in production:${NC}"
    echo "  cd $DJANGO_DIR"
    echo "  docker-compose up -d"
fi

echo
echo -e "${MAGENTA}✨ Frontend build completed!${NC}"
