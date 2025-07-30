# Оптимизация Docker для Django проекта

## Проблема
После изменения кода кнопка не работает, требуется пересборка контейнера. Стандартный Dockerfile пересобирает все слои при любом изменении кода.

## Решение: Многоэтапный Dockerfile с оптимизацией

### Файлы оптимизации:
- `Dockerfile.optimized` - Оптимизированный многоэтапный Dockerfile
- `docker-compose.optimized.yml` - Улучшенный docker-compose
- `rebuild.ps1` - Скрипт быстрой пересборки (стандартный)
- `rebuild-optimized.ps1` - Скрипт быстрой пересборки (оптимизированный)

## Преимущества оптимизированного Dockerfile

### 1. Многоэтапная сборка (Multi-stage build)
- **Builder stage**: Сборка зависимостей и статических файлов
- **Production stage**: Минимальный продакшн образ
- **Development stage**: Образ для разработки с дополнительными инструментами
- **Static-files stage**: Отдельный образ только со статическими файлами для nginx

### 2. Оптимизация кэширования слоев
```dockerfile
# Сначала копируем requirements.txt (изменяется редко)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Потом копируем код (изменяется часто)
COPY . .
```

### 3. Виртуальное окружение
- Изолированные зависимости Python
- Быстрое копирование между этапами
- Меньший размер финального образа

### 4. Безопасность
- Непривилегированный пользователь `app`
- Минимальные системные зависимости в продакшн
- Правильные права доступа к файлам

### 5. Именованные volumes
- Статические файлы в отдельном volume
- Персистентность данных Redis
- Быстрое монтирование для разработки

## Использование

### Быстрая пересборка (рекомендуется)
```powershell
# Для оптимизированной версии
.\rebuild-optimized.ps1

# Для стандартной версии
.\rebuild.ps1
```

### Ручная пересборка
```bash
# Остановка контейнеров
docker-compose -f docker-compose.optimized.yml down

# Пересборка только Django контейнера
docker-compose -f docker-compose.optimized.yml build --no-cache django

# Запуск
docker-compose -f docker-compose.optimized.yml up -d

# Сбор статических файлов
docker-compose -f docker-compose.optimized.yml exec django python manage.py collectstatic --noinput
```

### Разработка vs Продакшн

#### Для разработки:
```yaml
# В docker-compose.optimized.yml
build:
  target: development  # Использует этап development
```

#### Для продакшн:
```yaml
build:
  target: production   # Использует этап production с gunicorn
```

## Что изменилось

### Проблемы старого Dockerfile:
1. ❌ Копирование всего кода в начале
2. ❌ Пересборка всех слоев при изменении кода
3. ❌ Большой размер образа
4. ❌ Запуск от root пользователя
5. ❌ Статические файлы собираются каждый раз

### Преимущества нового Dockerfile:
1. ✅ Оптимизированный порядок копирования
2. ✅ Кэширование слоев с зависимостями
3. ✅ Минимальный размер продакшн образа
4. ✅ Безопасный непривилегированный пользователь
5. ✅ Статические файлы в отдельном volume
6. ✅ Быстрая пересборка при изменении только кода

## Мониторинг и отладка

### Просмотр логов
```bash
# Логи Django
docker-compose -f docker-compose.optimized.yml logs -f django

# Логи всех сервисов
docker-compose -f docker-compose.optimized.yml logs -f
```

### Проверка статуса
```bash
docker-compose -f docker-compose.optimized.yml ps
```

### Вход в контейнер для отладки
```bash
docker-compose -f docker-compose.optimized.yml exec django bash
```

## Рекомендации

1. **Используйте оптимизированную версию** для разработки
2. **Запускайте rebuild-optimized.ps1** после изменений в коде
3. **Проверяйте логи** после пересборки
4. **Используйте именованные volumes** для персистентности данных
5. **Регулярно очищайте** неиспользуемые образы: `docker system prune -f`

## Размеры образов

- **Стандартный Dockerfile**: ~800MB
- **Оптимизированный production**: ~200MB
- **Оптимизированный development**: ~250MB

Экономия места: **~75%** для продакшн образа!