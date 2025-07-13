# Настройка системы управления адресами доставки

## Описание

Полная система управления адресами доставки с интеграцией Google Maps для автозаполнения адресов.

## Структура

### Backend (Django)

- **Приложение**: `apps.addresses`
- **Модель**: `Address` - управление адресами пользователей
- **API**: RESTful endpoints для CRUD операций
- **Админка**: Полный интерфейс управления в Django Admin

### Frontend (React)

- **Компоненты**:
  - `AddressList` - список адресов
  - `AddressForm` - форма добавления/редактирования
  - `GoogleAddressAutocomplete` - автозаполнение Google Maps
  - `AddressSelector` - выбор адреса при оформлении заказа
  - `AddressesPage` - отдельная страница управления адресами

## Установка и настройка

### 1. Настройка Django

```bash
# Применить миграции
python manage.py migrate addresses

# Создать суперпользователя (если нужно)
python manage.py createsuperuser
```

### 2. Настройка Google Maps API

1. Получите API ключ в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите следующие API:

   - Maps JavaScript API
   - Places API
   - Geocoding API

3. Создайте файл `.env` в `guscha_django_frontend/`:

```bash
REACT_APP_GOOGLE_MAPS_API_KEY=your_actual_api_key_here
REACT_APP_API_URL=http://localhost:8000/api
```

### 3. Установка зависимостей

```bash
# Frontend зависимости
cd guscha_django_frontend
npm install
```

## Использование API

### Эндпоинты

#### Получение адресов

- `GET /api/addresses/addresses/` - все адреса пользователя
- `GET /api/addresses/addresses/shipping/` - адреса доставки
- `GET /api/addresses/addresses/billing/` - адреса оплаты
- `GET /api/addresses/addresses/default/` - адреса по умолчанию

#### CRUD операции

- `POST /api/addresses/addresses/` - создание адреса
- `GET /api/addresses/addresses/{id}/` - получение адреса
- `PUT /api/addresses/addresses/{id}/` - обновление адреса
- `DELETE /api/addresses/addresses/{id}/` - удаление адреса (soft delete)

#### Дополнительные действия

- `POST /api/addresses/addresses/{id}/set_default/` - установить адрес по умолчанию

### Примеры использования

#### Создание адреса

```javascript
const addressData = {
  address_type: "shipping",
  first_name: "Иван",
  last_name: "Иванов",
  address_line1: "ул. Ленина, д. 1",
  city: "Москва",
  postal_code: "123456",
  country: "Russia",
  phone: "+7 (999) 123-45-67",
  is_default: true
};

const response = await addressesApi.createAddress(addressData);
```

## Интеграция в приложение

### 1. Добавление в страницу аккаунта

```javascript
import { AddressList } from './components/features/addresses';

// В компоненте Account
<AddressList addressType="shipping" />
<AddressList addressType="billing" />
```

### 2. Использование в процессе оформления заказа

```javascript
import AddressSelector from './components/features/checkout/AddressSelector';

// В компоненте checkout
<AddressSelector
  addressType="shipping"
  onAddressSelect={handleShippingAddressSelect}
/>

<AddressSelector
  addressType="billing"
  onAddressSelect={handleBillingAddressSelect}
/>
```

### 3. Отдельная страница управления адресами

```javascript
import AddressesPage from "./pages/AddressesPage";

// В маршрутах React Router
<Route path="/addresses" element={<AddressesPage />} />;
```

## Настройка Google Maps

### Подключение скрипта Google Maps

Добавьте в `public/index.html`:

```html
<script
  src="https://maps.googleapis.com/maps/api/js?key=%REACT_APP_GOOGLE_MAPS_API_KEY%&libraries=places"
  async
  defer
></script>
```

### Ограничения по странам

По умолчанию автозаполнение ограничено Россией. Для изменения страны измените параметр в `GoogleAddressAutocomplete.jsx`:

```javascript
componentRestrictions: {
  country: "ru";
} // Измените на нужную страну
```

## Формат данных адреса

```javascript
{
  id: 1,
  address_type: "shipping", // или "billing"
  first_name: "Иван",
  last_name: "Иванов",
  company: "ООО Ромашка", // опционально
  address_line1: "ул. Ленина, д. 1",
  address_line2: "кв. 10", // опционально
  city: "Москва",
  state: "Московская область", // опционально
  postal_code: "123456",
  country: "Russia",
  phone: "+7 (999) 123-45-67", // опционально
  is_default: true,
  is_active: true,
  full_address: "ул. Ленина, д. 1, кв. 10, Москва, Московская область, 123456, Russia",
  full_name: "Иван Иванов"
}
```

## Административный интерфейс

В Django Admin доступны следующие возможности:

- Просмотр всех адресов пользователей
- Фильтрация по типу адреса, стране, статусу
- Поиск по имени, адресу, email пользователя
- Быстрое редактирование адресов

## Тестирование

### Backend тесты

```bash
python manage.py test apps.addresses
```

### Frontend тесты

```bash
cd guscha_django_frontend
npm test
```

## Безопасность

- Все API endpoints требуют аутентификации
- Пользователи могут управлять только своими адресами
- Soft delete для предотвращения потери данных
- Валидация входных данных на сервере и клиенте

## Расширение функционала

### Добавление новых стран

1. Обновить список стран в `AddressForm.jsx`
2. Обновить валидацию в `serializers.py`
3. Добавить переводы в `models.py`

### Добавление новых полей

1. Обновить модель `Address`
2. Создать миграции
3. Обновить сериализаторы
4. Обновить компоненты frontend

## Поддержка

При возникновении проблем:

1. Проверьте настройки Google Maps API
2. Убедитесь в правильности API ключа
3. Проверьте CORS настройки Django
4. Проверьте логи браузера и сервера
