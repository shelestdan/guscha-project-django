# Развертывание проекта на новом сервере

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone -b macOS git@github.com:shelestdan/guscha-project-django.git
cd guscha-project-django
```

### 2. Автоматическая настройка (macOS)
```bash
chmod +x quick_start.sh
./quick_start.sh
```

### 3. Синхронизация медиа файлов
```bash
# Медиа файлы (логотип, иконки) уже включены в Git
# Но если нужно обновить после изменений в React:
cd guscha_django_frontend
npm install
npm run build
cd ..
./copy_media_files.sh
```

### 4. Запуск контейнеров
```bash
cd guscha_django
docker-compose -f docker-compose.dev.yml up -d
```

## 📁 Структура медиа файлов

```
guscha_django/static_root/media/
├── logo.cf654137a024406cbade9c254b442833.svg          # Основной логотип
├── instrument_x4fdrqsfczqn.4a7efb845c2b844e443b92e46d63e8cc.svg  # Иконка корзины
└── TelegramIcon.3a0e1444dfc60df021cef070260a88fc.svg  # Иконка Telegram
```

## 🔄 Обновление медиа файлов

Если вы изменили логотип или иконки в React:

```bash
# 1. Соберите React
cd guscha_django_frontend
npm run build

# 2. Скопируйте новые файлы
cd ..
./copy_media_files.sh

# 3. Закоммитьте изменения
git add -f guscha_django/static_root/media/
git commit -m "Update media files"
git push origin macOS
```

## 🌐 Доступность

После запуска:
- **Сайт:** http://localhost
- **API:** http://localhost/api/
- **Админка:** http://localhost/admin/
- **Логотип:** http://localhost/static/media/logo.cf654137a024406cbade9c254b442833.svg
- **Иконка корзины:** http://localhost/static/media/instrument_x4fdrqsfczqn.4a7efb845c2b844e443b92e46d63e8cc.svg

## ✅ Проверка работоспособности

```bash
# Проверка статуса контейнеров
docker-compose -f docker-compose.dev.yml ps

# Проверка доступности логотипа
curl -I http://localhost/static/media/logo.cf654137a024406cbade9c254b442833.svg

# Проверка доступности иконки корзины  
curl -I http://localhost/static/media/instrument_x4fdrqsfczqn.4a7efb845c2b844e443b92e46d63e8cc.svg
```

## 🔧 Git настройки

Медиа файлы включены в Git с исключениями:
- `static_root/` - игнорируется
- `!static_root/media/` - включается
- `!static_root/media/*.svg` - включаются SVG файлы
- `!static_root/media/*.png` - включаются PNG файлы  
- `!static_root/media/*.ico` - включаются ICO файлы

Это позволяет хранить только необходимые медиа файлы, игнорируя остальную статику.
