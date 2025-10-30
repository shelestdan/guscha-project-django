#!/bin/bash

# =============================================================================
# 🔧 GUSCHA PROJECT - FULL SETUP SCRIPT
# =============================================================================
# Автоматическая установка и настройка проекта на новом macOS/Linux сервере
# Автор: Ludmila Filippova
# Версия: 1.0
# =============================================================================

set -e  # Exit on any error

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${GREEN}"
    echo "██████╗ ██╗   ██╗██╗██╗     ██████╗     ██████╗██╗     ██╗"
    echo "██╔══██╗██║   ██║██║██║     ██╔══██╗    ██╔════╝██║     ██║"
    echo "██████╔╝██║   ██║██║██║     ██║  ██║    ██║     ██║     ██║"
    echo "██╔══██╗╚██╗ ██╔╝██║██║     ██║  ██║    ██║     ██║     ██║"
    echo "██████╔╝ ╚████╔╝ ██║███████╗██████╔╝    ╚██████╗███████╗██║"
    echo "╚═════╝   ╚═══╝  ╚═╝╚══════╝╚═════╝      ╚═════╝╚══════╝╚═╝"
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

# Проверка системных требований
check_requirements() {
    print_step "Проверка системных требований..."
    
    # Проверка ОС
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        PACKAGE_MANAGER="brew"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
        if command -v apt-get &> /dev/null; then
            PACKAGE_MANAGER="apt"
        elif command -v yum &> /dev/null; then
            PACKAGE_MANAGER="yum"
        else
            print_error "Поддерживаются только macOS и Ubuntu/CentOS"
            exit 1
        fi
    else
        print_error "Поддерживаются только macOS и Linux"
        exit 1
    fi
    
    print_success "ОС: $OS, Package Manager: $PACKAGE_MANAGER"
    
    # Проверка Git
    if ! command -v git &> /dev/null; then
        print_error "Git не установлен. Установите Git и запустите скрипт снова."
        exit 1
    fi
    
    print_success "Git установлен"
}

# Установка Docker
install_docker() {
    print_step "Проверка и установка Docker..."
    
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        print_success "Docker и Docker Compose уже установлены"
        return
    fi
    
    if [[ "$OS" == "macOS" ]]; then
        print_warning "На macOS установите Docker Desktop вручную:"
        echo "1. Скачайте: https://www.docker.com/products/docker-desktop"
        echo "2. Установите и запустите Docker Desktop"
        echo "3. Нажмите Enter для продолжения..."
        read -r
    else
        print_step "Установка Docker на Linux..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        
        print_step "Установка Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
        print_success "Docker и Docker Compose установлены"
        print_warning "Выйдите из системы и войдите снова для применения прав Docker"
    fi
}

# Проверка что мы в правильной директории
check_project_directory() {
    print_step "Проверка структуры проекта..."
    
    if [ ! -f "guscha_django/docker-compose.dev.yml" ]; then
        print_error "Ошибка: docker-compose.dev.yml не найден"
        print_error "Убедитесь что вы запускаете скрипт из корневой директории проекта"
        exit 1
    fi
    
    if [ ! -f "guscha_django/.env.example" ]; then
        print_error "Ошибка: .env.example не найден"
        print_error "Убедитесь что вы скачали полный проект"
        exit 1
    fi
    
    print_success "Структура проекта корректна"
}

# Настройка переменных окружения
setup_environment() {
    print_step "Настройка переменных окружения..."
    
    if [ ! -f "guscha_django/.env" ]; then
        print_step "Создание файла .env из шаблона..."
        cp guscha_django/.env.example guscha_django/.env
        
        # Генерация секретного ключа Django
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -hex 32)
        
        # Обновление .env файла
        sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" guscha_django/.env
        sed -i.bak "s/DEBUG=True/DEBUG=True/" guscha_django/.env
        sed -i.bak "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost,127.0.0.1/" guscha_django/.env
        
        rm guscha_django/.env.bak
        
        print_success "Файл .env создан"
    else
        print_success "Файл .env уже существует"
    fi
}

# Сборка и запуск контейнеров
build_and_start() {
    print_step "Сборка и запуск Docker контейнеров..."
    
    cd guscha_django
    
    # Остановка старых контейнеров если есть
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    # Сборка образов
    print_step "Сборка Docker образов..."
    docker-compose -f docker-compose.dev.yml build
    
    # Запуск контейнеров
    print_step "Запуск контейнеров..."
    docker-compose -f docker-compose.dev.yml up -d
    
    # Ожидание запуска
    print_step "Ожидание запуска сервисов..."
    sleep 30
    
    cd ..
    print_success "Контейнеры запущены"
}

# Проверка работоспособности
check_services() {
    print_step "Проверка работоспособности сервисов..."
    
    cd guscha_django
    
    # Проверка статуса контейнеров
    if docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
        print_success "Контейнеры работают"
    else
        print_error "Некоторые контейнеры не запущены"
        docker-compose -f docker-compose.dev.yml ps
        exit 1
    fi
    
    # Проверка доступности сайта
    sleep 10
    if curl -s http://localhost > /dev/null; then
        print_success "Сайт доступен по http://localhost"
    else
        print_warning "Сайт еще не доступен, подождите еще 30 секунд..."
        sleep 30
        if curl -s http://localhost > /dev/null; then
            print_success "Сайт доступен по http://localhost"
        else
            print_error "Сайт недоступен. Проверьте логи: docker-compose logs"
        fi
    fi
    
    # Проверка медиа файлов
    if curl -s http://localhost/static/media/logo.cf654137a024406cbade9c254b442833.svg > /dev/null; then
        print_success "Логотип доступен"
    else
        print_warning "Логотип недоступен, но это не критично"
    fi
    
    cd ..
}

# Создание административного пользователя
create_admin() {
    print_step "Создание административного пользователя..."
    
    cd guscha_django
    
    # Проверка существования админа
    if docker-compose -f docker-compose.dev.yml exec -T django python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.filter(is_superuser=True).count())
" | grep -q "0"; then
        echo "Создание суперпользователя..."
        echo "Email: admin@guscha.com"
        echo "Password: admin123456"
        docker-compose -f docker-compose.dev.yml exec -T django python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin@guscha.com', 'admin123456')
"
        print_success "Администратор создан"
    else
        print_success "Администратор уже существует"
    fi
    
    cd ..
}

# Показ итоговой информации
show_final_info() {
    print_success "═══════════════════════════════════════════════════"
    echo -e "${GREEN}🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!${NC}"
    print_success "═══════════════════════════════════════════════════"
    echo
    echo -e "${BLUE}📱 Доступные сервисы:${NC}"
    echo -e "   🌐 Сайт:           ${GREEN}http://localhost${NC}"
    echo -e "   🔧 API:            ${GREEN}http://localhost/api/${NC}"
    echo -e "   👤 Админка:        ${GREEN}http://localhost/admin/${NC}"
    echo
    echo -e "${BLUE}🔐 Данные для входа:${NC}"
    echo -e "   Email:    ${YELLOW}admin@guscha.com${NC}"
    echo -e "   Password: ${YELLOW}admin123456${NC}"
    echo
    echo -e "${BLUE}📋 Полезные команды:${NC}"
    echo -e "   Статус:   ${YELLOW}cd guscha_django && docker-compose -f docker-compose.dev.yml ps${NC}"
    echo -e "   Логи:     ${YELLOW}cd guscha_django && docker-compose -f docker-compose.dev.yml logs${NC}"
    echo -e "   Перезапуск:${YELLOW}cd guscha_django && docker-compose -f docker-compose.dev.yml restart${NC}"
    echo -e "   Остановка: ${YELLOW}cd guscha_django && docker-compose -f docker-compose.dev.yml down${NC}"
    echo
    echo -e "${BLUE}📁 Структура проекта:${NC}"
    echo -e "   📂 guscha-project-django/"
    echo -e "   ├── 📂 guscha_django/          # Django проект"
    echo -e "   ├── 📂 guscha_django_frontend/ # React проект"
    echo -e "   ├── 📄 copy_media_files.sh     # Скрипт медиа файлов"
    echo -e "   └── 📄 DEPLOYMENT.md           # Документация"
    echo
    print_success "Приятной работы! 🚀"
}

# Главная функция
main() {
    print_header
    
    echo -e "${YELLOW}Этот скрипт выполнит полную установку проекта Guscha${NC}"
    echo -e "${YELLOW}Включая: Docker, настройку и запуск всех сервисов${NC}"
    echo -e "${YELLOW}Убедитесь что вы запускаете скрипт из корневой директории проекта${NC}"
    echo
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Установка отменена"
        exit 0
    fi
    
    check_requirements
    install_docker
    check_project_directory
    setup_environment
    build_and_start
    check_services
    create_admin
    show_final_info
}

# Запуск
main "$@"
