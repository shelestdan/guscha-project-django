#!/bin/bash

# Скрипт для копирования медиа файлов из React сборки в static_root
# Используется для логотипа, иконок и других статических ресурсов

set -e

echo "🔄 Копирование медиа файлов из React в static_root..."

# Пути
FRONTEND_BUILD_DIR="guscha_django_frontend/build/static/media"
STATIC_MEDIA_DIR="guscha_django/static_root/media"

# Создаем директорию если не существует
mkdir -p "$STATIC_MEDIA_DIR"

# Копируем только нужные файлы (логотип и иконки)
if [ -d "$FRONTEND_BUILD_DIR" ]; then
    echo "📁 Найдена сборка React: $FRONTEND_BUILD_DIR"
    
    # Копируем SVG файлы (логотипы, иконки)
    find "$FRONTEND_BUILD_DIR" -name "*.svg" -exec cp {} "$STATIC_MEDIA_DIR/" \;
    
    # Копируем PNG файлы (favicon и другие)
    find "$FRONTEND_BUILD_DIR" -name "*.png" -exec cp {} "$STATIC_MEDIA_DIR/" \;
    
    # Копируем ICO файлы (favicon)
    find "$FRONTEND_BUILD_DIR" -name "*.ico" -exec cp {} "$STATIC_MEDIA_DIR/" \;
    
    echo "✅ Медиа файлы скопированы в: $STATIC_MEDIA_DIR"
    
    # Показываем что скопировано
    echo "📋 Скопированные файлы:"
    ls -la "$STATIC_MEDIA_DIR" | grep -E "\.(svg|png|ico)$"
    
else
    echo "❌ Ошибка: директория сборки React не найдена: $FRONTEND_BUILD_DIR"
    echo "💡 Сначала соберите React: cd guscha_django_frontend && npm run build"
    exit 1
fi

echo "🎉 Готово! Теперь можно коммитить медиа файлы в Git."
