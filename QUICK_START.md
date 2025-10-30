# 🚀 GUSCHA PROJECT - ОДНА КОМАНДА ДЛЯ ПОЛНОЙ УСТАНОВКИ

## ⚡ Супер быстрый старт

### На новом macOS/Linux сервере выполните ОДНУ команду:

```bash
curl -fsSL https://raw.githubusercontent.com/shelestdan/guscha-project-django/macOS/FULL_SETUP.sh -o setup.sh && chmod +x setup.sh && ./setup.sh
```

## 📋 Или по шагам:

### 1. Скачайте и запустите:
```bash
git clone -b macOS git@github.com:shelestdan/guscha-project-django.git
cd guscha-project-django
chmod +x FULL_SETUP.sh
./FULL_SETUP.sh
```

### 2. Готово! 🎉

После установки будете иметь:
- 🌐 **Сайт:** http://localhost
- 🔧 **API:** http://localhost/api/
- 👤 **Админка:** http://localhost/admin/
- 🔐 **Вход:** admin@guscha.com / admin123456

## ✅ Что делает скрипт автоматически:

1. **🔍 Проверяет систему** (macOS/Linux)
2. **📦 Устанавливает Docker** (если нужен)
3. **📥 Клонирует репозиторий** с GitHub
4. **⚙️ Настраивает .env** файл
5. **🐳 Собирает Docker образы**
6. **🚀 Запускает все контейнеры**
7. **✅ Проверяет работоспособность**
8. **👤 Создает админа** (admin@guscha.com)
9. **📱 Показывает доступные сервисы**

## 🎯 Результат:

**Полностью рабочий проект** за 5-10 минут на любом сервере!

- ✅ Логотип отображается
- ✅ Иконка корзины работает  
- ✅ Telegram бот готов
- ✅ База данных настроена
- ✅ Все сервисы запущены

## 🔧 Управление после установки:

```bash
cd guscha_django

# Проверить статус
docker-compose -f docker-compose.dev.yml ps

# Посмотреть логи
docker-compose -f docker-compose.dev.yml logs

# Перезапустить
docker-compose -f docker-compose.dev.yml restart

# Остановить
docker-compose -f docker-compose.dev.yml down
```

**Больше НИЧЕГО настраивать не нужно!** 🚀
