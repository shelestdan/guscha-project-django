#!/bin/bash

# Скрипт быстрого деплоя Guscha Project
# Использование: ./deploy.sh [production|development]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка аргументов
MODE=${1:-production}

if [ "$MODE" != "production" ] && [ "$MODE" != "development" ]; then
    log_error "Неверный режим. Используйте: production или development"
    exit 1
fi

log_info "Режим деплоя: $MODE"

# Проверка Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    log_error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

log_info "Docker и Docker Compose установлены ✓"

# Проверка .env файла
if [ ! -f "guscha_django/.env" ]; then
    log_warn ".env файл не найден. Создаю из примера..."
    cp guscha_django/.env.example guscha_django/.env
    log_error ".env файл создан. ОБЯЗАТЕЛЬНО отредактируйте его перед продолжением!"
    log_error "Откройте guscha_django/.env и измените все значения на свои."
    exit 1
fi

log_info ".env файл найден ✓"

# Проверка критических переменных
log_info "Проверка критических переменных окружения..."

check_env_var() {
    local var_name=$1
    local var_value=$(grep "^${var_name}=" guscha_django/.env | cut -d '=' -f2-)
    
    if [ -z "$var_value" ] || [ "$var_value" == "your-"* ] || [ "$var_value" == "change-this"* ]; then
        log_error "Переменная $var_name не настроена в .env файле!"
        return 1
    fi
    return 0
}

ERRORS=0

if [ "$MODE" == "production" ]; then
    check_env_var "SECRET_KEY" || ERRORS=$((ERRORS+1))
    check_env_var "POSTGRES_PASSWORD" || ERRORS=$((ERRORS+1))
    check_env_var "ADMIN_URL" || ERRORS=$((ERRORS+1))
    check_env_var "DOMAIN_NAME" || ERRORS=$((ERRORS+1))
    
    if [ $ERRORS -gt 0 ]; then
        log_error "Найдено $ERRORS ошибок в .env файле. Исправьте их перед деплоем."
        exit 1
    fi
fi

log_info "Все критические переменные настроены ✓"

# Выбор docker-compose файла
if [ "$MODE" == "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
else
    COMPOSE_FILE="guscha_django/docker-compose.dev.yml"
fi

log_info "Используется конфигурация: $COMPOSE_FILE"

# Остановка существующих контейнеров
log_info "Остановка существующих контейнеров..."
docker compose -f $COMPOSE_FILE down 2>/dev/null || true

# Сборка и запуск
log_info "Сборка и запуск контейнеров..."
docker compose -f $COMPOSE_FILE up -d --build

# Ожидание запуска БД
log_info "Ожидание запуска базы данных..."
sleep 10

# Выполнение миграций
log_info "Выполнение миграций базы данных..."
if [ "$MODE" == "production" ]; then
    docker compose -f $COMPOSE_FILE exec -T django python manage.py migrate --noinput
else
    docker compose -f $COMPOSE_FILE exec -T django python manage.py migrate --noinput
fi

# Сбор статических файлов
log_info "Сбор статических файлов..."
if [ "$MODE" == "production" ]; then
    docker compose -f $COMPOSE_FILE exec -T django python manage.py collectstatic --noinput --clear
else
    docker compose -f $COMPOSE_FILE exec -T django python manage.py collectstatic --noinput
fi

# Проверка статуса
log_info "Проверка статуса контейнеров..."
docker compose -f $COMPOSE_FILE ps

# Вывод информации
echo ""
log_info "================================"
log_info "Деплой завершен успешно! 🎉"
log_info "================================"
echo ""

if [ "$MODE" == "production" ]; then
    log_info "Приложение доступно по адресу: http://$(grep DOMAIN_NAME guscha_django/.env | cut -d '=' -f2)"
    log_info "Админка: http://$(grep DOMAIN_NAME guscha_django/.env | cut -d '=' -f2)/$(grep ADMIN_URL guscha_django/.env | cut -d '=' -f2)"
else
    log_info "Приложение доступно по адресу: http://localhost"
    log_info "Django API: http://localhost:8000"
    log_info "Админка: http://localhost:8000/admin/"
fi

echo ""
log_info "Полезные команды:"
echo "  Просмотр логов:     docker compose -f $COMPOSE_FILE logs -f"
echo "  Статус контейнеров: docker compose -f $COMPOSE_FILE ps"
echo "  Остановка:          docker compose -f $COMPOSE_FILE down"
echo "  Перезапуск:         docker compose -f $COMPOSE_FILE restart"
echo ""

# Создание суперпользователя (только для development)
if [ "$MODE" == "development" ]; then
    log_warn "Не забудьте создать суперпользователя:"
    echo "  docker compose -f $COMPOSE_FILE exec django python manage.py createsuperuser"
fi

log_info "Готово!"
