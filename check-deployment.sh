#!/bin/bash

# Скрипт проверки деплоя
# Проверяет все компоненты системы

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS+1))
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS+1))
}

echo "================================"
echo "Проверка деплоя Guscha Project"
echo "================================"
echo ""

# Определение режима
if [ -f "docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    MODE="production"
else
    COMPOSE_FILE="guscha_django/docker-compose.dev.yml"
    MODE="development"
fi

echo "Режим: $MODE"
echo "Конфигурация: $COMPOSE_FILE"
echo ""

# 1. Проверка Docker
echo "1. Проверка Docker..."
if command -v docker &> /dev/null; then
    log_success "Docker установлен ($(docker --version))"
else
    log_fail "Docker не установлен"
fi

if command -v docker compose &> /dev/null; then
    log_success "Docker Compose установлен"
else
    log_fail "Docker Compose не установлен"
fi
echo ""

# 2. Проверка .env файла
echo "2. Проверка .env файла..."
if [ -f "guscha_django/.env" ]; then
    log_success ".env файл существует"
    
    # Проверка критических переменных
    check_var() {
        local var=$1
        if grep -q "^${var}=" guscha_django/.env; then
            local value=$(grep "^${var}=" guscha_django/.env | cut -d '=' -f2-)
            if [ -z "$value" ] || [[ "$value" == *"your-"* ]] || [[ "$value" == *"change-this"* ]]; then
                log_warn "$var не настроена или использует значение по умолчанию"
            else
                log_success "$var настроена"
            fi
        else
            log_fail "$var отсутствует в .env"
        fi
    }
    
    check_var "SECRET_KEY"
    check_var "POSTGRES_PASSWORD"
    check_var "ADMIN_URL"
    check_var "DEBUG"
else
    log_fail ".env файл не найден"
fi
echo ""

# 3. Проверка контейнеров
echo "3. Проверка контейнеров..."
if docker compose -f $COMPOSE_FILE ps | grep -q "Up"; then
    log_success "Контейнеры запущены"
    
    # Проверка каждого сервиса
    check_service() {
        local service=$1
        if docker compose -f $COMPOSE_FILE ps $service | grep -q "Up"; then
            log_success "$service запущен"
        else
            log_fail "$service не запущен"
        fi
    }
    
    check_service "db"
    check_service "redis"
    check_service "django"
    check_service "nginx"
    
    if [ "$MODE" == "production" ]; then
        check_service "telegram-bot"
    fi
else
    log_fail "Контейнеры не запущены"
fi
echo ""

# 4. Проверка здоровья сервисов
echo "4. Проверка здоровья сервисов..."

# PostgreSQL
if docker compose -f $COMPOSE_FILE exec -T db pg_isready &> /dev/null; then
    log_success "PostgreSQL готов к работе"
else
    log_fail "PostgreSQL не отвечает"
fi

# Redis
if docker compose -f $COMPOSE_FILE exec -T redis redis-cli ping &> /dev/null; then
    log_success "Redis готов к работе"
else
    log_fail "Redis не отвечает"
fi

# Django
if docker compose -f $COMPOSE_FILE exec -T django python manage.py check &> /dev/null; then
    log_success "Django проверка пройдена"
else
    log_fail "Django проверка не пройдена"
fi
echo ""

# 5. Проверка портов
echo "5. Проверка доступности портов..."

check_port() {
    local port=$1
    local service=$2
    if nc -z localhost $port 2>/dev/null; then
        log_success "Порт $port ($service) доступен"
    else
        log_warn "Порт $port ($service) недоступен"
    fi
}

check_port 80 "HTTP"
check_port 443 "HTTPS"

if [ "$MODE" == "development" ]; then
    check_port 8000 "Django"
    check_port 5432 "PostgreSQL"
    check_port 6379 "Redis"
fi
echo ""

# 6. Проверка статических файлов
echo "6. Проверка статических файлов..."
if docker compose -f $COMPOSE_FILE exec -T django ls /app/static_root/ &> /dev/null; then
    log_success "Директория статических файлов существует"
    
    file_count=$(docker compose -f $COMPOSE_FILE exec -T django find /app/static_root/ -type f | wc -l)
    if [ $file_count -gt 0 ]; then
        log_success "Найдено $file_count статических файлов"
    else
        log_warn "Статические файлы не найдены. Выполните: collectstatic"
    fi
else
    log_fail "Директория статических файлов не найдена"
fi
echo ""

# 7. Проверка миграций
echo "7. Проверка миграций базы данных..."
if docker compose -f $COMPOSE_FILE exec -T django python manage.py showmigrations | grep -q "\[ \]"; then
    log_warn "Есть неприменённые миграции"
else
    log_success "Все миграции применены"
fi
echo ""

# 8. Проверка логов на ошибки
echo "8. Проверка логов на ошибки..."
if docker compose -f $COMPOSE_FILE logs --tail=100 | grep -i "error" | grep -v "0 error" &> /dev/null; then
    log_warn "Обнаружены ошибки в логах. Проверьте: docker compose logs"
else
    log_success "Критических ошибок в логах не обнаружено"
fi
echo ""

# 9. Проверка безопасности
echo "9. Проверка настроек безопасности..."

if [ "$MODE" == "production" ]; then
    # Проверка DEBUG
    if grep -q "^DEBUG=False" guscha_django/.env; then
        log_success "DEBUG отключен"
    else
        log_fail "DEBUG должен быть False в продакшене!"
    fi
    
    # Проверка ALLOWED_HOSTS
    if grep -q "^ALLOWED_HOSTS=" guscha_django/.env && ! grep -q "ALLOWED_HOSTS=localhost" guscha_django/.env; then
        log_success "ALLOWED_HOSTS настроен"
    else
        log_warn "ALLOWED_HOSTS должен содержать ваш домен"
    fi
    
    # Проверка SECRET_KEY
    if grep -q "^SECRET_KEY=django-insecure" guscha_django/.env; then
        log_fail "SECRET_KEY использует небезопасное значение по умолчанию!"
    else
        log_success "SECRET_KEY изменён"
    fi
fi
echo ""

# Итоги
echo "================================"
echo "Результаты проверки:"
echo "================================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ Все проверки пройдены успешно!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Проверка завершена с $WARNINGS предупреждениями${NC}"
    exit 0
else
    echo -e "${RED}✗ Обнаружено $ERRORS ошибок и $WARNINGS предупреждений${NC}"
    echo ""
    echo "Рекомендации:"
    echo "1. Проверьте логи: docker compose -f $COMPOSE_FILE logs"
    echo "2. Проверьте статус: docker compose -f $COMPOSE_FILE ps"
    echo "3. Проверьте .env файл"
    exit 1
fi
