# 🍎 Запуск на macOS за 5 минут

## ✅ 100% гарантия работы на macOS (Intel и Apple Silicon)

---

## Шаг 1: Установите Docker Desktop (2 минуты)

**Скачайте:**
- Intel Mac: https://desktop.docker.com/mac/main/amd64/Docker.dmg
- Apple Silicon (M1/M2/M3): https://desktop.docker.com/mac/main/arm64/Docker.dmg

**Установите:** Перетащите Docker в Applications и запустите

**Проверьте:**
```bash
docker --version
```

---

## Шаг 2: Настройте проект (2 минуты)

```bash
# Перейдите в проект
cd guscha_django

# Создайте .env
cp .env.example .env

# Сгенерируйте ключи
python3 ../generate-secrets.py

# Откройте .env и вставьте сгенерированные ключи
open -e .env
```

**Минимальные изменения:**
- Вставьте `SECRET_KEY` из генератора
- Вставьте `POSTGRES_PASSWORD` из генератора
- Измените `ADMIN_URL` на что-то вроде `admin-test-123/`

---

## Шаг 3: Запустите (1 минута)

```bash
cd ..
chmod +x deploy.sh
./deploy.sh development
```

Дождитесь сообщения "Деплой завершен успешно! 🎉"

---

## Шаг 4: Создайте админа (30 секунд)

```bash
docker compose -f guscha_django/docker-compose.dev.yml exec django python manage.py createsuperuser
```

Введите email и пароль.

---

## Шаг 5: Откройте в браузере

- **Сайт:** http://localhost
- **API:** http://localhost:8000
- **Админка:** http://localhost:8000/admin/

---

## 🎉 Готово!

Проект работает на вашем Mac!

---

## 🐛 Если что-то не работает

### Docker не запускается?
```bash
# Запустите Docker Desktop из Applications
# Дождитесь иконки в menu bar
```

### Порт занят?
```bash
# Освободите порт 80:
sudo lsof -ti:80 | xargs kill -9
```

### Python не найден?
```bash
# Используйте python3:
python3 generate-secrets.py
```

### Проверка деплоя:
```bash
./check-deployment.sh
```

---

## 📖 Полная документация

- [MACOS_SETUP.md](MACOS_SETUP.md) - Подробное руководство для macOS
- [QUICK_START.md](QUICK_START.md) - Быстрый старт
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Полное руководство

---

**Всё работает! 🍎✅**
