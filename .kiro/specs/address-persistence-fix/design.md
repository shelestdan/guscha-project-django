# Дизайн исправления системы адресов доставки

## Обзор

Система управления адресами доставки имеет критические проблемы с персистентностью данных и отображением. Адреса не сохраняются между сессиями и отображаются неполно. Необходимо создать полноценную backend модель для адресов и исправить frontend логику.

## Архитектура

### Текущее состояние
- **Backend**: Приложение `addresses` существует, но модели не реализованы (нужно найти, реализация есть)
- **Frontend**: API вызовы настроены, но backend endpoints не существуют (тоже должно быть настроено, нужно найти)
- **База данных**: Они есть 
- **Аутентификация**: Настроена через Token Authentication

### Целевая архитектура
- **Backend**: Django модель Address с полными CRUD операциями
- **API**: RESTful endpoints через Django REST Framework
- **Frontend**: Исправленная логика загрузки и отображения
- **Персистентность**: Данные сохраняются в SQLite базе данных

## Компоненты и интерфейсы

### Backend компоненты

#### 1. Модель Address
```python
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=[('shipping', 'Доставка'), ('billing', 'Оплата')])
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address_line1 = models.CharField(max_length=255)  # Улица, дом
    address_line2 = models.CharField(max_length=255, blank=True)  # Квартира, офис
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # Для soft delete
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 2. Serializer
```python
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address_type', 'first_name', 'last_name', 
                 'address_line1', 'address_line2', 'city', 'postal_code', 
                 'phone', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
```

#### 3. ViewSet
```python
class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user, is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        # Логика установки адреса по умолчанию
```

#### 4. URL Configuration
```python
# addresses/urls.py
router = DefaultRouter()
router.register(r'addresses', AddressViewSet, basename='address')

# guscha_project/urls.py
path('api/', include('apps.addresses.urls')),
```

### Frontend исправления

#### 1. Исправление отображения адресов
- Добавить отображение `address_line2` (квартира/офис)
- Правильно форматировать полный адрес
- Показывать все поля адреса

#### 2. Исправление загрузки данных
- Убедиться что API вызовы происходят при монтировании компонента
- Добавить правильную обработку ошибок аутентификации
- Исправить логику фильтрации по типу адреса

#### 3. Улучшение UX
- Добавить индикаторы загрузки
- Показывать уведомления об успешных операциях
- Улучшить обработку ошибок

## Модели данных

### Address Model Schema
```sql
CREATE TABLE addresses_address (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES accounts_user(id),
    address_type VARCHAR(20) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    phone VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

### API Response Format
```json
{
  "id": 1,
  "address_type": "shipping",
  "first_name": "Иван",
  "last_name": "Петров",
  "address_line1": "ул. Ленина, д. 10",
  "address_line2": "кв. 25",
  "city": "Тольятти",
  "postal_code": "445013",
  "phone": "+79372172232",
  "is_default": true,
  "created_at": "2025-01-17T10:00:00Z",
  "updated_at": "2025-01-17T10:00:00Z"
}
```

## Обработка ошибок

### Backend Error Handling
- Валидация обязательных полей
- Проверка формата телефона и почтового индекса
- Ограничение на один адрес по умолчанию на тип
- Проверка прав доступа (пользователь может управлять только своими адресами)

### Frontend Error Handling
- Обработка 401 (неавторизован) - редирект на страницу входа
- Обработка 400 (валидация) - показ ошибок в форме
- Обработка 500 (серверная ошибка) - общее сообщение об ошибке
- Обработка сетевых ошибок - уведомление о проблемах с подключением

## Стратегия тестирования

### Backend Tests
- Unit тесты для модели Address
- Тесты API endpoints (CRUD операции)
- Тесты валидации данных
- Тесты прав доступа

### Frontend Tests
- Тесты компонентов AddressList и AddressForm
- Тесты API интеграции
- Тесты пользовательских сценариев

### Integration Tests
- End-to-end тесты полного цикла работы с адресами
- Тесты аутентификации и авторизации

## Миграция данных

### Создание миграций
```bash
python manage.py makemigrations addresses
python manage.py migrate
```

### Обратная совместимость
- Новая система не нарушает существующий функционал
- Старые API endpoints (если есть) остаются работоспособными
- Graceful degradation при отсутствии данных

## Безопасность

### Аутентификация
- Все endpoints требуют аутентификации
- Пользователи видят только свои адреса

### Валидация
- Серверная валидация всех входных данных
- Защита от XSS через правильное экранирование
- Ограничение длины полей

### Авторизация
- Пользователи могут управлять только своими адресами
- Проверка владельца при всех операциях