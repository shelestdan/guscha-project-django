#!/bin/bash

# =============================================================================
# GUSCHA PROJECT - macOS AUTO SETUP SCRIPT
# =============================================================================
# Этот скрипт автоматически настраивает и запускает проект на macOS
# Включает установку зависимостей, миграции, создание суперпользователя

set -e  # Прерывать выполнение при ошибках

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# ФУНКЦИИ ЛОГИРОВАНИЯ
# =============================================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# ПРОВЕРКА СИСТЕМНЫХ ТРЕБОВАНИЙ
# =============================================================================
check_requirements() {
    log_info "Проверка системных требований..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен. Пожалуйста, установите Docker Desktop для macOS"
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен"
        exit 1
    fi
    
    # Проверка Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js не установлен. Требуется версия 18+"
        exit 1
    fi
    
    # Проверка npm
    if ! command -v npm &> /dev/null; then
        log_error "npm не установлен"
        exit 1
    fi
    
    # Проверка Git
    if ! command -v git &> /dev/null; then
        log_error "Git не установлен"
        exit 1
    fi
    
    log_success "Все системные требования удовлетворены"
}

# =============================================================================
# НАСТРОЙКА ОКРУЖЕНИЯ
# =============================================================================
setup_environment() {
    log_info "Настройка окружения..."
    
    # Проверка наличия .env файла
    if [ ! -f "guscha_django/.env" ]; then
        log_warning ".env файл не найден, создаю из примера..."
        cp guscha_django/.env.example guscha_django/.env
        log_warning "Пожалуйста, отредактируйте guscha_django/.env файл с реальными данными"
        log_warning "Особенно важны TELEGRAM_BOT_TOKEN и другие токены API"
    else
        log_info ".env файл найден"
    fi
    
    # Установка прав на выполнение скриптов
    chmod +x guscha_django/scripts/start.sh 2>/dev/null || true
    chmod +x build_frontend.sh 2>/dev/null || true
    
    log_success "Окружение настроено"
}

# =============================================================================
# СБОРКА FRONTEND
# =============================================================================
build_frontend() {
    log_info "Сборка frontend приложения..."
    
    # Переход в директорию frontend
    cd guscha_django_frontend
    
    # Проверка наличия package.json
    if [ ! -f "package.json" ]; then
        log_error "package.json не найден в guscha_django_frontend"
        exit 1
    fi
    
    # Установка зависимостей
    log_info "Установка npm зависимостей..."
    npm install
    
    # Сборка проекта
    log_info "Сборка frontend..."
    npm run build
    
    cd ..
    log_success "Frontend собран"
}

# =============================================================================
# НАСТРОЙКА DOCKER КОНТЕЙНЕРОВ
# =============================================================================
setup_docker() {
    log_info "Настройка Docker контейнеров..."
    
    cd guscha_django
    
    # Остановка существующих контейнеров
    log_info "Остановка существующих контейнеров..."
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    # Создание необходимых директорий
    log_info "Создание директорий для Docker volumes..."
    mkdir -p data/postgres data/redis logs backups media static_root profiles
    
    # Сборка образов
    log_info "Сборка Docker образов..."
    docker-compose -f docker-compose.dev.yml build --no-cache
    
    log_success "Docker контейнеры настроены"
    cd ..
}

# =============================================================================
# ЗАПУСК И НАСТРОЙКА БАЗЫ ДАННЫХ
# =============================================================================
setup_database() {
    log_info "Настройка базы данных..."
    
    cd guscha_django
    
    # Запуск контейнеров
    log_info "Запуск контейнеров..."
    docker-compose -f docker-compose.dev.yml up -d db redis
    
    # Ожидание запуска базы данных
    log_info "Ожидание запуска PostgreSQL..."
    sleep 10
    
    # Проверка доступности базы данных
    log_info "Проверка доступности базы данных..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose -f docker-compose.dev.yml exec -T db pg_isready -U guscha >/dev/null 2>&1; then
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "База данных не запустилась за отведенное время"
        exit 1
    fi
    
    # Запуск основного приложения
    log_info "Запуск Django приложения..."
    docker-compose -f docker-compose.dev.yml up -d django
    
    # Ожидание запуска Django
    log_info "Ожидание запуска Django..."
    sleep 15
    
    # Выполнение миграций
    log_info "Выполнение миграций базы данных..."
    docker-compose -f docker-compose.dev.yml exec -T django python manage.py migrate
    
    log_success "База данных настроена"
    cd ..
}

# =============================================================================
# СОЗДАНИЕ СУПЕРПОЛЬЗОВАТЕЛЯ
# =============================================================================
create_superuser() {
    log_info "Создание суперпользователя..."
    
    cd guscha_django
    
    # Проверка существования суперпользователя
    if docker-compose -f docker-compose.dev.yml exec -T django python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.filter(email='admin@guscha.ru').exists())
" | grep -q "True"; then
        log_info "Суперпользователь уже существует"
    else
        # Создание суперпользователя
        log_info "Создание нового суперпользователя..."
        docker-compose -f docker-compose.dev.yml exec -T django python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin@guscha.ru', 'SecureAdminPass123!')
print('Суперпользователь создан')
"
        log_success "Суперпользователь создан"
        log_info "Данные для входа:"
        log_info "Email: admin@guscha.ru"
        log_info "Пароль: SecureAdminPass123!"
    fi
    
    cd ..
}

# =============================================================================
# ЗАПУСК ВСЕХ СЕРВИСОВ
# =============================================================================
start_services() {
    log_info "Запуск всех сервисов..."
    
    cd guscha_django
    
    # Запуск всех контейнеров
    docker-compose -f docker-compose.dev.yml up -d
    
    # Ожидание запуска всех сервисов
    log_info "Ожидание запуска всех сервисов..."
    sleep 20
    
    # Создание директории profiles (для Silk)
    log_info "Создание директории для профилирования..."
    docker-compose -f docker-compose.dev.yml exec -T django mkdir -p /app/profiles 2>/dev/null || true
    
    log_success "Все сервисы запущены"
    cd ..
}

# =============================================================================
# ПРОВЕРКА РАБОТОСПОСОБНОСТИ
# =============================================================================
verify_setup() {
    log_info "Проверка работоспособности..."
    
    # Проверка доступности основного приложения
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
        log_success "Основное приложение доступно: http://localhost"
    else
        log_warning "Основное приложение пока недоступно, возможно,还需要 время"
    fi
    
    # Проверка доступности админки
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/secure-admin-guscha-2024/ | grep -q "200"; then
        log_success "Админ-панель доступна: http://localhost/secure-admin-guscha-2024/"
    else
        log_warning "Админ-панель пока недоступна, возможно,还需要 время"
    fi
    
    # Проверка статуса контейнеров
    cd guscha_django
    log_info "Статус Docker контейнеров:"
    docker-compose -f docker-compose.dev.yml ps
    cd ..
}

# =============================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# =============================================================================
main() {
    echo "========================================================================"
    echo "🚀 GUSCHA PROJECT - macOS AUTO SETUP"
    echo "========================================================================"
    echo ""
    
    # Проверка, что мы в корневой директории проекта
    if [ ! -f "build_frontend.sh" ] || [ ! -d "guscha_django" ]; then
        log_error "Скрипт должен запускаться из корневой директории проекта"
        exit 1
    fi
    
    # Выполнение всех шагов
    check_requirements
    setup_environment
    build_frontend
    setup_docker
    setup_database
    create_superuser
    start_services
    verify_setup
    
    echo ""
    echo "========================================================================"
    echo "✅ УСТАНОВКА ЗАВЕРШЕНА!"
    echo "========================================================================"
    echo ""
    echo "🌐 Доступные сервисы:"
    echo "   • Основное приложение: http://localhost"
    echo "   • Админ-панель: http://localhost/secure-admin-guscha-2024/"
    echo "   • API: http://localhost/api/"
    echo ""
    echo "👤 Данные для входа в админку:"
    echo "   • Email: admin@guscha.ru"
    echo "   • Пароль: SecureAdminPass123!"
    echo ""
    echo "📝 Важные заметки:"
    echo "   • Убедитесь, что в guscha_django/.env указаны реальные токены"
    echo "   • Telegram бот будет работать с правильным токеном"
    echo "   • Все контейнеры автоматически перезапускаются"
    echo ""
    echo "🔧 Управление проектом:"
    echo "   • Остановка: cd guscha_django && docker-compose -f docker-compose.dev.yml down"
    echo "   • Перезапуск: cd guscha_django && docker-compose -f docker-compose.dev.yml restart"
    echo "   • Логи: cd guscha_django && docker-compose -f docker-compose.dev.yml logs -f"
    echo ""
}

# Запуск основной функции
main "$@"
