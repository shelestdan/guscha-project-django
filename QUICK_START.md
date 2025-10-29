# 🚀 Быстрый старт Guscha Project

## Для нового сервера (Production)

### 1. Установите Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. Клонируйте репозиторий
```bash
git clone <your-repo-url> guscha-project
cd guscha-project
```

### 3. Настройте .env файл
```bash
cd guscha_django
cp .env.example .env
nano .env  # Измените ВСЕ значения!
```

**ОБЯЗАТЕЛЬНО измените:**
- `SECRET_KEY` - сгенерируйте новый
- `POSTGRES_PASSWORD` - сильный пароль
- `ADMIN_URL` - секретный путь
- `DOMAIN_NAME` - ваш домен
- `TELEGRAM_BOT_TOKEN` - токен от @BotFather
- Все email настройки

### 4. Запустите деплой
```bash
cd ..
chmod +x deploy.sh
./deploy.sh production
```

### 5. Создайте суперпользователя
```bash
docker compose -f docker-compose.prod.yml exec django python manage.py createsuperuser
```

### 6. Готово! 🎉
Ваше приложение работает на `http://your-domain.com`

---

## Для разработки (Development)

### 1. Клонируйте и настройте
```bash
git clone <your-repo-url> guscha-project
cd guscha-project/guscha_django
cp .env.example .env
```

### 2. Запустите
```bash
docker compose -f docker-compose.dev.yml up -d --build
```

### 3. Выполните миграции
```bash
docker compose -f docker-compose.dev.yml exec django python manage.py migrate
docker compose -f docker-compose.dev.yml exec django python manage.py createsuperuser
```

### 4. Готово!
- Frontend: http://localhost
- Django API: http://localhost:8000
- Admin: http://localhost:8000/admin/

---

## Полезные команды

```bash
# Просмотр логов
docker compose logs -f

# Статус контейнеров
docker compose ps

# Остановка
docker compose down

# Перезапуск
docker compose restart

# Проверка деплоя
./check-deployment.sh

# Резервное копирование
./backup.sh
```

---

## Troubleshooting

**Контейнеры не запускаются?**
```bash
docker compose logs
docker compose down
docker compose up -d --build
```

**База данных не подключается?**
```bash
docker compose exec django python manage.py dbshell
```

**Статика не загружается?**
```bash
docker compose exec django python manage.py collectstatic --noinput --clear
```

---

📖 **Полная документация:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
