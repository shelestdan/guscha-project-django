# Система валидации и безопасности Django

Комплексная система валидации, санитизации и мониторинга безопасности для Django приложения.

## Обзор

Эта система предоставляет:
- Централизованную валидацию входных данных
- Санитизацию и защиту от XSS/SQL инъекций
- Rate limiting и защиту от DDoS атак
- Мониторинг и логирование событий безопасности
- Валидацию файлов и проверку на вредоносное ПО
- Проверку силы паролей и email адресов

## Компоненты

### 1. AdvancedValidator

Класс для комплексной валидации различных типов данных.

```python
from apps.core.validation import AdvancedValidator

# Валидация строки
try:
    clean_string = AdvancedValidator.validate_string("user input", max_length=100)
except ValidationError as e:
    print(f"Ошибка валидации: {e}")

# Валидация email
try:
    clean_email = AdvancedValidator.validate_email("user@example.com")
except ValidationError as e:
    print(f"Невалидный email: {e}")

# Валидация пароля
try:
    AdvancedValidator.validate_password("StrongPass123!")
except ValidationError as e:
    print(f"Слабый пароль: {e}")
```

### 2. SecurityLogger

Система логирования событий безопасности.

```python
from apps.core.validation import log_security_event, SecurityEvent

# Логирование подозрительной активности
log_security_event(
    event_type='SUSPICIOUS_REQUEST',
    severity='HIGH',
    message='Обнаружена попытка SQL инъекции',
    details={'ip': '192.168.1.100', 'user_agent': 'BadBot/1.0'}
)
```

### 3. Middleware

#### InputValidationMiddleware

Автоматически валидирует все входящие запросы.

```python
# settings.py
MIDDLEWARE = [
    # ... другие middleware
    'apps.core.middleware.validation_middleware.InputValidationMiddleware',
    # ...
]
```

#### RateLimitMiddleware

Ограничивает частоту запросов для предотвращения DDoS атак.

```python
# settings.py
MIDDLEWARE = [
    # ... другие middleware
    'apps.core.middleware.validation_middleware.RateLimitMiddleware',
    # ...
]
```

### 4. Декораторы

#### @validate_json_input

Валидирует JSON данные в запросе.

```python
from apps.core.validation import validate_json_input

@validate_json_input(['name', 'email'])  # обязательные поля
def create_user(request):
    data = json.loads(request.body)
    # data уже валидирована
    return JsonResponse({'status': 'success'})
```

#### @validate_query_params

Валидирует параметры запроса.

```python
from apps.core.validation import validate_query_params

@validate_query_params(['page', 'limit'])
def list_users(request):
    page = request.GET.get('page', 1)
    # параметры уже валидированы
    return JsonResponse({'users': []})
```

#### @sanitize_input_data

Санитизирует все входные данные.

```python
from apps.core.validation import sanitize_input_data

@sanitize_input_data
def update_profile(request):
    # Все данные в request.POST и request.GET санитизированы
    return JsonResponse({'status': 'success'})
```

#### @validate_file_upload

Валидирует загружаемые файлы.

```python
from apps.core.validation import validate_file_upload

@validate_file_upload(
    allowed_extensions=['.jpg', '.png'],
    max_size=5*1024*1024  # 5MB
)
def upload_avatar(request):
    file = request.FILES['avatar']
    # файл уже валидирован
    return JsonResponse({'status': 'success'})
```

#### @require_authentication

Проверяет аутентификацию и разрешения.

```python
from apps.core.validation import require_authentication

@require_authentication(permissions=['can_edit_users'])
def edit_user(request, user_id):
    # пользователь аутентифицирован и имеет нужные права
    return JsonResponse({'status': 'success'})
```

## Конфигурация

### Настройки в settings.py

```python
# Максимальные размеры данных
MAX_JSON_BODY_SIZE = 1024 * 1024  # 1MB
MAX_FORM_FIELD_SIZE = 10000
MAX_FILE_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
MAX_STRING_FIELD_SIZE = 1000
MAX_TEXT_FIELD_SIZE = 10000

# Разрешенные расширения файлов
ALLOWED_FILE_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.pdf', 
    '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'
]

# Rate limiting
DEFAULT_RATE_LIMIT = 100  # запросов в минуту
AUTH_RATE_LIMIT = 10      # попыток входа в минуту
API_RATE_LIMIT = 60       # API запросов в минуту
UPLOAD_RATE_LIMIT = 5     # загрузок в минуту
CRITICAL_RATE_LIMIT = 10  # критических операций в минуту

# Блокировка IP
IP_BLOCKING_ENABLED = True
IP_BLOCK_DURATION = 3600  # секунд
MAX_SECURITY_VIOLATIONS = 5
IP_WHITELIST = ['127.0.0.1', '::1']

# Критические endpoints
CRITICAL_ENDPOINTS = [
    '/api/auth/login/',
    '/api/auth/register/',
    '/api/payments/',
    '/api/admin/',
]

# Исключенные пути
VALIDATION_EXCLUDED_PATHS = [
    '/static/',
    '/media/',
    '/favicon.ico',
    '/health/',
]

# Логирование безопасности
SECURITY_LOGGING_ENABLED = True
SECURITY_LOG_LEVEL = 'WARNING'
MAX_SECURITY_LOG_ENTRIES = 10000
SECURITY_ALERT_THRESHOLD = 10
SECURITY_ALERT_WINDOW = 300

# Email алерты
SECURITY_EMAIL_ALERTS = True
SECURITY_ALERT_RECIPIENTS = ['admin@example.com']
SECURITY_ALERT_FROM_EMAIL = 'security@example.com'

# Slack алерты
SECURITY_SLACK_ALERTS = True
SECURITY_SLACK_WEBHOOK = 'https://hooks.slack.com/...'
SECURITY_SLACK_CHANNEL = '#security'

# Валидация паролей
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True
CHECK_COMMON_PASSWORDS = True

# Валидация email
EMAIL_CHECK_MX_RECORD = False
EMAIL_CHECK_DISPOSABLE = True
EMAIL_MAX_LENGTH = 254

# Валидация телефонов
PHONE_ALLOWED_COUNTRIES = ['RU', 'US', 'GB']
PHONE_REQUIRE_COUNTRY_CODE = True
```

## Быстрое использование

```python
from apps.core.validation import (
    validate_string, validate_email, sanitize_html, 
    check_password_strength
)

# Быстрая валидация строки
try:
    clean_input = validate_string(user_input, max_length=100)
except ValidationError:
    return JsonResponse({'error': 'Невалидные данные'})

# Быстрая валидация email
try:
    clean_email = validate_email(email)
except ValidationError:
    return JsonResponse({'error': 'Невалидный email'})

# Санитизация HTML
clean_html = sanitize_html(user_html)

# Проверка силы пароля
password_check = check_password_strength(password)
if not password_check['valid']:
    return JsonResponse({'error': password_check['message']})
```

## Мониторинг и алерты

Система автоматически отслеживает:
- Попытки SQL инъекций
- XSS атаки
- Подозрительные запросы
- Превышение rate limits
- Неудачные попытки аутентификации
- Попытки доступа к запрещенным ресурсам

При обнаружении подозрительной активности система:
1. Логирует событие
2. Блокирует IP (при необходимости)
3. Отправляет алерты по email/Slack
4. Обновляет метрики безопасности

## Интеграция с существующим кодом

### Пошаговая интеграция

1. **Добавьте middleware в settings.py:**
```python
MIDDLEWARE = [
    # ... существующие middleware
    'apps.core.middleware.validation_middleware.InputValidationMiddleware',
    'apps.core.middleware.validation_middleware.RateLimitMiddleware',
]
```

2. **Добавьте декораторы к критическим view:**
```python
from apps.core.validation import validate_json_input, require_authentication

@require_authentication()
@validate_json_input(['username', 'password'])
def login_view(request):
    # ваш код
```

3. **Используйте валидаторы в формах:**
```python
from apps.core.validation import AdvancedValidator

class UserForm(forms.Form):
    def clean_email(self):
        email = self.cleaned_data['email']
        return AdvancedValidator.validate_email(email)
```

4. **Настройте логирование в settings.py:**
```python
LOGGING = {
    'loggers': {
        'security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
        },
    },
}
```

## Тестирование

```python
from django.test import TestCase
from apps.core.validation import AdvancedValidator

class ValidationTestCase(TestCase):
    def test_string_validation(self):
        # Тест валидной строки
        result = AdvancedValidator.validate_string("valid input")
        self.assertEqual(result, "valid input")
        
        # Тест XSS атаки
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_string("<script>alert('xss')</script>")
    
    def test_email_validation(self):
        # Тест валидного email
        result = AdvancedValidator.validate_email("user@example.com")
        self.assertEqual(result, "user@example.com")
        
        # Тест невалидного email
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_email("invalid-email")
```

## Производительность

- Валидация строк: ~0.1ms на строку
- Валидация JSON: ~1ms на объект
- Проверка файлов: ~10ms на файл
- Rate limiting: ~0.01ms на запрос

## Безопасность

Система защищает от:
- SQL инъекций
- XSS атак
- CSRF атак
- Path traversal
- Command injection
- LDAP injection
- XPath injection
- DDoS атак
- Brute force атак

## Поддержка

Для получения помощи:
1. Проверьте логи безопасности: `logs/security.log`
2. Используйте `get_security_status()` для диагностики
3. Обратитесь к команде безопасности

## Версионность

Текущая версия: 1.0.0

История изменений:
- 1.0.0: Первый релиз с базовой функциональностью