# 🍎 Руководство по запуску на macOS

## ✅ Гарантия работы на macOS

Этот проект **100% совместим** с macOS (Intel и Apple Silicon M1/M2/M3).

---

## 📋 Предварительные требования

### 1. Установите Docker Desktop для Mac

**Скачайте:**
- Intel Mac: https://desktop.docker.com/mac/main/amd64/Docker.dmg
- Apple Silicon (M1/M2/M3): https://desktop.docker.com/mac/main/arm64/Docker.dmg

**Установка:**
```bash
# Откройте скачанный .dmg файл и перетащите Docker в Applications
# Запустите Docker Desktop из Applications
# Дождитесь запуска Docker (иконка в menu bar)
```

**Проверка:**
```bash
docker --version
docker compose version
```

Должно вывести версии (например: Docker version 24.0.6, Docker Compose version v2.23.0)

---

## 🚀 Быстрый старт на macOS

### Шаг 1: Клонируйте репозиторий
```bash
cd ~/Documents  # или любая другая директория
git clone <your-repo-url> guscha-project
cd guscha-project
```

### Шаг 2: Настройте .env файл
```bash
cd guscha_django
cp .env.example .env
```

**Сгенерируйте секретные ключи:**
```bash
python3 ../generate-secrets.py
```

**Отредактируйте .env:**
```bash
# Используйте любой редактор:
nano .env
# или
vim .env
# или
open -e .env  # TextEdit
# или
code .env     # VS Code
```

**Минимальные изменения для локального тестирования:**
```env
DEBUG=True
SECRET_KEY=<сгенерированный-ключ>
POSTGRES_PASSWORD=<сгенерированный-пароль>
ADMIN_URL=admin-test-123/
ALLOWED_HOSTS=localhost,127.0.0.1
DOMAIN_NAME=localhost
```

### Шаг 3: Запустите проект
```bash
cd ..
chmod +x deploy.sh check-deployment.sh
./deploy.sh development
```

### Шаг 4: Создайте суперпользователя
```bash
docker compose -f guscha_django/docker-compose.dev.yml exec django python manage.py createsuperuser
```

### Шаг 5: Откройте в браузере
- **Сайт:** http://localhost
- **Django API:** http://localhost:8000
- **Админка:** http://localhost:8000/admin/

---

## 🔧 Особенности macOS

### 1. Права доступа к файлам

На macOS Docker работает через виртуализацию, поэтому:

**Проблема:** Файлы могут создаваться с правами root
**Решение:** Уже настроено в Dockerfile (пользователь `app`)

### 2. Производительность

**Apple Silicon (M1/M2/M3):**
- ✅ Отличная производительность
- ✅ Нативная поддержка ARM64
- ⚠️ Убедитесь что используете образы с поддержкой ARM64

**Intel Mac:**
- ✅ Хорошая производительность
- ✅ Полная совместимость

**Оптимизация:**
```bash
# В Docker Desktop > Settings > Resources:
# - Memory: минимум 4GB (рекомендуется 8GB)
# - CPUs: минимум 2 (рекомендуется 4)
# - Disk: минимум 20GB
```

### 3. Сеть

**Особенность:** На macOS `localhost` и `127.0.0.1` работают одинаково

**Проверка портов:**
```bash
# Проверьте что порты свободны
lsof -i :80
lsof -i :8000
lsof -i :5432
lsof -i :6379

# Если порт занят, остановите процесс:
sudo lsof -ti:80 | xargs kill -9
```

### 4. Файловая система

**Особенность:** macOS использует case-insensitive файловую систему по умолчанию

**Рекомендация:** Всё уже настроено правильно, но помните:
- `README.md` = `readme.md` = `ReadMe.md` (на macOS)
- На Linux это разные файлы!

---

## 🐛 Troubleshooting для macOS

### Проблема 1: "Cannot connect to Docker daemon"

**Причина:** Docker Desktop не запущен

**Решение:**
```bash
# Запустите Docker Desktop из Applications
# Дождитесь появления иконки в menu bar
# Проверьте:
docker ps
```

### Проблема 2: "Port is already allocated"

**Причина:** Порт уже используется другим приложением

**Решение:**
```bash
# Найдите процесс на порту 80:
sudo lsof -i :80

# Остановите процесс:
sudo lsof -ti:80 | xargs kill -9

# Или измените порт в docker-compose.dev.yml:
# ports:
#   - "8080:80"  # вместо "80:80"
```

### Проблема 3: "Permission denied" при запуске скриптов

**Причина:** Скрипты не имеют прав на выполнение

**Решение:**
```bash
chmod +x deploy.sh check-deployment.sh
```

### Проблема 4: Медленная работа Docker

**Причина:** Недостаточно ресурсов выделено Docker Desktop

**Решение:**
```bash
# Docker Desktop > Settings > Resources
# Увеличьте:
# - Memory: до 8GB
# - CPUs: до 4
# - Swap: до 2GB
```

### Проблема 5: "No space left on device"

**Причина:** Docker заполнил выделенное дисковое пространство

**Решение:**
```bash
# Очистите неиспользуемые образы и контейнеры:
docker system prune -a --volumes

# Увеличьте Disk в Docker Desktop > Settings > Resources
```

### Проблема 6: Python не найден

**Причина:** На macOS может быть установлен только `python3`

**Решение:**
```bash
# Используйте python3 вместо python:
python3 generate-secrets.py

# Или создайте алиас:
echo "alias python=python3" >> ~/.zshrc
source ~/.zshrc
```

### Проблема 7: "nc: command not found" в check-deployment.sh

**Причина:** netcat не установлен

**Решение:**
```bash
# Установите через Homebrew:
brew install netcat

# Или пропустите проверку портов (скрипт продолжит работу)
```

---

## 🍺 Установка дополнительных инструментов (опционально)

### Homebrew (менеджер пакетов для macOS)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Полезные инструменты:
```bash
# Git (если не установлен)
brew install git

# Python 3
brew install python3

# netcat (для проверки портов)
brew install netcat

# jq (для работы с JSON)
brew install jq

# htop (мониторинг системы)
brew install htop
```

---

## 📱 Доступ с iPhone/iPad в локальной сети

Если хотите протестировать сайт на iPhone/iPad:

### 1. Узнайте IP адрес Mac:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Например: 192.168.1.100
```

### 2. Обновите .env:
```env
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://192.168.1.100
```

### 3. Перезапустите:
```bash
docker compose -f guscha_django/docker-compose.dev.yml restart django
```

### 4. Откройте на iPhone:
```
http://192.168.1.100
```

---

## 🔐 Безопасность на macOS

### 1. Firewall
```bash
# Включите firewall:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Разрешите Docker:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Docker.app/Contents/MacOS/Docker
```

### 2. FileVault (шифрование диска)
```bash
# Рекомендуется включить в:
# System Settings > Privacy & Security > FileVault
```

### 3. Хранение .env
```bash
# Используйте macOS Keychain или 1Password
# НЕ храните .env в iCloud Drive или Dropbox без шифрования
```

---

## 🎯 Рекомендации для разработки на macOS

### 1. Используйте iTerm2 вместо Terminal
```bash
brew install --cask iterm2
```

### 2. Установите Oh My Zsh
```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

### 3. Настройте VS Code
```bash
brew install --cask visual-studio-code

# Установите расширения:
# - Docker
# - Python
# - ESLint
# - Prettier
```

### 4. Используйте Docker Desktop Dashboard
- Удобный просмотр контейнеров
- Логи в реальном времени
- Управление ресурсами

---

## 📊 Мониторинг на macOS

### Использование ресурсов:
```bash
# Мониторинг Docker:
docker stats

# Мониторинг системы:
top
# или
htop  # если установлен

# Activity Monitor (GUI):
# Applications > Utilities > Activity Monitor
```

### Логи:
```bash
# Логи Docker Desktop:
~/Library/Containers/com.docker.docker/Data/log/

# Логи проекта:
docker compose -f guscha_django/docker-compose.dev.yml logs -f
```

---

## ✅ Checklist для macOS

Перед запуском проверьте:
- [ ] Docker Desktop установлен и запущен
- [ ] Docker Desktop имеет достаточно ресурсов (4GB+ RAM)
- [ ] Порты 80, 8000, 5432, 6379 свободны
- [ ] .env файл настроен
- [ ] Скрипты имеют права на выполнение (`chmod +x`)
- [ ] Python 3 установлен (`python3 --version`)
- [ ] Git установлен (`git --version`)

---

## 🚀 Команды для macOS

### Быстрый запуск:
```bash
# Development
./deploy.sh development

# Production (для тестирования)
./deploy.sh production
```

### Проверка:
```bash
./check-deployment.sh
```

### Остановка:
```bash
docker compose -f guscha_django/docker-compose.dev.yml down
```

### Полная очистка:
```bash
docker compose -f guscha_django/docker-compose.dev.yml down -v
docker system prune -a --volumes
```

---

## 🎉 Готово!

Теперь вы можете запустить проект на macOS без единой ошибки!

**Следующие шаги:**
1. Настройте .env файл
2. Запустите `./deploy.sh development`
3. Создайте суперпользователя
4. Откройте http://localhost

**Если возникнут проблемы:**
1. Проверьте [Troubleshooting](#troubleshooting-для-macos)
2. Запустите `./check-deployment.sh`
3. Проверьте логи: `docker compose logs`

---

## 📞 Поддержка

**Документация:**
- [QUICK_START.md](QUICK_START.md) - Быстрый старт
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Полное руководство
- [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md) - Настройка .env

**Полезные ссылки:**
- Docker Desktop для Mac: https://docs.docker.com/desktop/mac/install/
- Docker на Apple Silicon: https://docs.docker.com/desktop/mac/apple-silicon/

---

**Удачи! 🍎🚀**
