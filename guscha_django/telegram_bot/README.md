# Telegram Bot - Современная архитектура

## Обзор

Этот проект представляет собой полностью рефакторенный Telegram бот с современной архитектурой, следующей лучшим практикам разработки на Python в 2025 году.

## 🏗️ Архитектура

### Слоистая архитектура

```
┌─────────────────────────────────────────┐
│                Handlers                 │  ← Обработка команд и событий
├─────────────────────────────────────────┤
│                Services                 │  ← Бизнес-логика
├─────────────────────────────────────────┤
│              Repositories               │  ← Работа с данными
├─────────────────────────────────────────┤
│                 Utils                   │  ← Вспомогательные функции
└─────────────────────────────────────────┘
```

### Структура проекта

```
telegram_bot/
├── __init__.py
├── bot.py                    # Основной класс бота с DI
├── README.md                 # Документация
├── config/                   # Конфигурация
│   ├── __init__.py
│   ├── settings.py          # Настройки бота
│   └── messages.py          # Централизованные сообщения
├── handlers/                 # Обработчики команд
│   ├── __init__.py
│   ├── base_handler.py      # Базовый класс обработчиков
│   ├── start_handler.py     # Обработчик /start
│   ├── contact_handler.py   # Обработчик контактов
│   └── callback_handler.py  # Обработчик callback запросов
├── services/                 # Бизнес-логика
│   ├── __init__.py
│   ├── verification_service.py  # Сервис верификации
│   ├── user_service.py         # Сервис пользователей
│   ├── phone_service.py        # Сервис телефонов
│   ├── rate_limit_service.py   # Сервис rate limiting
│   └── message_service.py      # Сервис сообщений
├── repositories/             # Слой данных
│   ├── __init__.py
│   ├── verification_code_repository.py
│   ├── user_repository.py
│   └── qr_code_repository.py
├── utils/                    # Утилиты
│   ├── __init__.py
│   ├── validators.py        # Валидаторы данных
│   ├── formatters.py        # Форматтеры сообщений
│   └── helpers.py           # Вспомогательные функции
├── exceptions/               # Кастомные исключения
│   ├── __init__.py
│   └── bot_exceptions.py
└── management/
    └── commands/
        └── run_telegram_bot.py  # Улучшенная команда запуска
```

## 🚀 Ключевые улучшения

### 1. Dependency Injection (DI)
- Все зависимости внедряются через конструктор
- Легкое тестирование и замена компонентов
- Слабая связанность между модулями

### 2. Принципы SOLID
- **Single Responsibility**: Каждый класс отвечает за одну задачу
- **Open/Closed**: Легко расширяется без изменения существующего кода
- **Liskov Substitution**: Компоненты легко заменяются
- **Interface Segregation**: Четкие интерфейсы для каждого слоя
- **Dependency Inversion**: Зависимость от абстракций, а не от конкретных реализаций

### 3. Современные инструменты
- **python-telegram-bot v20+** с полной поддержкой async/await
- **Type hints** везде для лучшей читаемости и IDE поддержки
- **Pydantic-style валидация** данных
- **Структурированное логирование** с контекстом
- **Rate limiting** для защиты от злоупотреблений

### 4. Обработка ошибок
- Централизованная обработка исключений
- Кастомные исключения для разных типов ошибок
- Graceful degradation при ошибках
- Подробное логирование для отладки

### 5. Безопасность
- Валидация всех входных данных
- Rate limiting для предотвращения спама
- Маскирование чувствительных данных в логах
- Безопасная обработка номеров телефонов

## 📋 Использование

### Запуск бота

```bash
# Обычный запуск
python manage.py run_telegram_bot

# Асинхронный режим
python manage.py run_telegram_bot --async

# Проверка здоровья
python manage.py run_telegram_bot --health-check

# Информация о боте
python manage.py run_telegram_bot --info

# С кастомным таймаутом shutdown
python manage.py run_telegram_bot --shutdown-timeout 60
```

### Конфигурация

В `settings.py` Django добавьте:

```python
# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = 'your_bot_token_here'
TELEGRAM_VERIFICATION_TIMEOUT_MINUTES = 10
TELEGRAM_REGISTRATION_RATE_LIMIT_MINUTES = 5
TELEGRAM_MAX_REGISTRATION_ATTEMPTS = 3
TELEGRAM_LOG_LEVEL = 'INFO'
```

## 🔧 Расширение функционала

### Добавление нового обработчика

1. Создайте новый файл в `handlers/`:

```python
from .base_handler import CommandHandler

class MyHandler(CommandHandler):
    async def handle(self, update, context):
        # Ваша логика
        pass
```

2. Зарегистрируйте в `bot.py`:

```python
self.application.add_handler(
    CommandHandler("mycommand", self.my_handler)
)
```

### Добавление нового сервиса

1. Создайте файл в `services/`:

```python
class MyService:
    def __init__(self):
        # Инициализация
        pass
    
    async def my_method(self):
        # Бизнес-логика
        pass
```

2. Внедрите в нужные обработчики через конструктор

## 🧪 Тестирование

### Структура тестов

```python
import pytest
from unittest.mock import AsyncMock, Mock
from telegram_bot.services import VerificationService

@pytest.fixture
def verification_service():
    return VerificationService()

@pytest.mark.asyncio
async def test_verification_service(verification_service):
    # Тестирование сервиса
    result = await verification_service.some_method()
    assert result is not None
```

### Запуск тестов

```bash
# Все тесты
pytest telegram_bot/tests/

# Конкретный модуль
pytest telegram_bot/tests/test_services.py

# С покрытием
pytest --cov=telegram_bot telegram_bot/tests/
```

## 📊 Мониторинг и логирование

### Структурированные логи

```python
logger.info(
    "Пользователь выполнил действие",
    extra={
        'user_id': user.id,
        'action': 'registration',
        'chat_id': chat_id,
        'timestamp': timezone.now().isoformat()
    }
)
```

### Метрики

- Количество активных пользователей
- Частота использования команд
- Время отклика сервисов
- Количество ошибок по типам

## 🔒 Безопасность

### Лучшие практики

1. **Валидация входных данных**: Все данные проверяются перед обработкой
2. **Rate limiting**: Ограничение частоты запросов
3. **Логирование безопасности**: Маскирование чувствительных данных
4. **Обработка ошибок**: Не раскрываем внутреннюю структуру в сообщениях об ошибках

### Конфиденциальность

- Номера телефонов хешируются в логах
- Персональные данные не сохраняются в plain text
- Временные токены с ограниченным сроком действия

## 🚀 Развертывание

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "manage.py", "run_telegram_bot"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  telegram-bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
    restart: unless-stopped
    depends_on:
      - db
```

## 📈 Производительность

### Оптимизации

1. **Асинхронная обработка**: Все операции выполняются асинхронно
2. **Кеширование**: Rate limiting и временные данные кешируются
3. **Пулы соединений**: Эффективное использование БД соединений
4. **Lazy loading**: Данные загружаются по требованию

### Масштабирование

- Горизонтальное масштабирование через несколько инстансов
- Использование Redis для shared state
- Балансировка нагрузки через webhook режим

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте feature branch
3. Следуйте code style проекта
4. Добавьте тесты для нового функционала
5. Создайте Pull Request

## 📝 Лицензия

MIT License - см. файл LICENSE для деталей.

## 🆘 Поддержка

Для вопросов и поддержки:
- Создайте Issue в репозитории
- Проверьте документацию
- Используйте `--health-check` для диагностики

---

**Версия**: 2.0.0  
**Дата обновления**: Январь 2025  
**Совместимость**: Python 3.11+, python-telegram-bot 20+