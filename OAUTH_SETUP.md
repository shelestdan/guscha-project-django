# 🔐 Настройка OAuth для входа через Google и Telegram

## 📋 Обзор
После установки проекта через `FULL_SETUP.sh` нужно настроить OAuth для полноценной работы входа через социальные сети.

---

## 🔵 Google OAuth Setup

### 1. Создание проекта в Google Cloud Console
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите необходимые API:
   - **Google+ API** (если доступен)
   - **Google OAuth2 API**
   - **People API** (для получения информации о пользователе)

### 2. Создание OAuth 2.0 Client ID
1. Перейдите в раздел **APIs & Services** → **Credentials**
2. Нажмите **Create Credentials** → **OAuth 2.0 Client ID**
3. Выберите **Web application**
4. Добавьте **Authorized redirect URIs**:
   ```
   http://localhost/auth/google/callback/
   http://localhost/api/accounts/users/google_login/callback/
   ```
5. Сохраните и получите **Client ID** и **Client Secret**

### 3. Настройка в проекте
Откройте файл `guscha_django/.env` и добавьте:
```bash
GOOGLE_CLIENT_ID=ваш_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=ваш_client_secret
```

### 4. Перезапуск
```bash
cd guscha_django
docker-compose -f docker-compose.dev.yml restart
```

---

## 📱 Telegram Bot Setup

### 1. Создание бота через @BotFather
1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: "Guscha Shop Bot")
   - Введите username бота (например: `guscha_shop_bot`)
4. Получите токен бота (выглядит как: `1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Настройка в проекте
Откройте файл `guscha_django/.env` и добавьте:
```bash
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

### 3. Перезапуск
```bash
cd guscha_django
docker-compose -f docker-compose.dev.yml restart
```

---

## ✅ Проверка работоспособности

### 1. Google OAuth
- Перейдите на http://localhost
- Нажмите кнопку "Войти через Google"
- Вы должны быть перенаправлены на страницу авторизации Google
- После успешной авторизации вы войдете в систему

### 2. Telegram Bot
- Перейдите на http://localhost
- Нажмите кнопку "Войти через Telegram"
- Введите ваш номер телефона
- Перейдите в Telegram бота и подтвердите номер
- Вы будете автоматически авторизованы на сайте

---

## 🔧 Troubleshooting

### Google OAuth не работает
- **Ошибка redirect_uri**: Убедитесь что в Google Cloud Console добавлены правильные redirect URIs
- **Ошибка invalid_client**: Проверьте правильность CLIENT_ID и CLIENT_SECRET
- **Ошибка access_denied**: Убедитесь что OAuth consent screen настроен и опубликован

### Telegram Bot не работает
- **Бот не отвечает**: Проверьте правильность токена в .env файле
- **Ошибка верификации**: Убедитесь что база данных работает и миграции применены
- **Код не приходит**: Проверьте логи телеграм бота: `docker-compose logs telegram-bot`

---

## 📝 Дополнительные настройки

### Production окружение
Для продакшн развертывания измените redirect URIs:
```bash
# В Google Cloud Console добавьте:
https://yourdomain.com/auth/google/callback/
https://yourdomain.com/api/accounts/users/google_login/callback/
```

### Безопасность
- Никогда не храните токены и секреты в Git репозитории
- Используйте переменные окружения
- Регулярно обновляйте секретные ключи
- Настройте HTTPS для продакшн

---

## 🆘 Поддержка
Если возникли проблемы:
1. Проверьте логи контейнеров: `docker-compose logs`
2. Убедитесь что все переменные окружения установлены
3. Проверьте сетевую доступность сервисов
4. Перезапустите контейнеры: `docker-compose restart`
