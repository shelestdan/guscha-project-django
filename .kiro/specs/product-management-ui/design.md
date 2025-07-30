# Design Document

## Overview

Создание современного и интуитивно понятного интерфейса управления товарами в Django Admin панели с использованием Jazzmin. Дизайн направлен на решение текущих проблем: дублирование кнопок, отсутствие карточного отображения товаров и отсутствие удобного управления размерами товаров.

## Architecture

### Компоненты системы:

1. **Список товаров (Product List View)**
   - Кастомный шаблон `change_list.html`
   - Переключение между карточками и таблицей
   - Единственная кнопка "Добавить товар"

2. **Форма товара (Product Form View)**
   - Кастомный шаблон `change_form.html`
   - Современный дизайн с группировкой полей
   - Интегрированное управление размерами

3. **Управление размерами (Size Management)**
   - Динамическое добавление/удаление размеров
   - AJAX-обработка без перезагрузки страницы
   - Валидация данных размеров

4. **Стили и скрипты**
   - Модульная CSS архитектура
   - JavaScript модули для каждого компонента

## Components and Interfaces

### 1. Product List Component

**Файлы:**
- `templates/admin/products/product/change_list.html`
- `static/admin/css/product-list.css`
- `static/admin/js/product-list.js`

**Функциональность:**
- Отображение товаров в виде карточек с превью изображений
- Переключатель "Карточки/Таблица"
- Фильтрация и поиск товаров
- Единственная кнопка "Добавить товар"

**Интерфейс карточки товара:**
```html
<div class="product-card">
  <div class="product-image">
    <img src="image_url" alt="product_name" />
    <div class="product-badges">
      <span class="badge featured">Рекомендуемый</span>
      <span class="badge status">Активен</span>
    </div>
  </div>
  <div class="product-info">
    <h3 class="product-name">Название товара</h3>
    <p class="product-sku">Артикул: SKU123</p>
    <div class="product-price">₽1,999</div>
    <div class="product-stock">В наличии: 15 шт.</div>
  </div>
  <div class="product-actions">
    <a href="edit_url" class="btn btn-primary">Редактировать</a>
    <a href="view_url" class="btn btn-secondary">Просмотр</a>
  </div>
</div>
```

### 2. Product Form Component

**Файлы:**
- `templates/admin/products/product/change_form.html`
- `static/admin/css/product-form.css`
- `static/admin/js/product-form.js`

**Структура формы:**

1. **Основная информация**
   - Название товара (обязательное)
   - Артикул/SKU (обязательное)
   - Категория (выпадающий список)
   - Описание товара (текстовое поле)

2. **Изображение товара**
   - URL изображения с превью в реальном времени
   - Валидация URL изображения
   - Анимация загрузки

3. **Цена и склад**
   - Цена товара (обязательное, с символом ₽)
   - Общее количество на складе
   - Отслеживание запасов (чекбокс)

4. **Размеры товара**
   - Динамический список размеров
   - Для каждого размера: название, количество, макс. для заказа, активность
   - Кнопки добавления/удаления размеров

5. **Настройки товара**
   - Товар активен (переключатель)
   - Рекомендуемый товар (переключатель)

### 3. Size Management Component

**Интерфейс размера:**
```html
<div class="size-item" data-size-id="1">
  <div class="size-header">
    <h4>Размер S</h4>
    <button type="button" class="btn-remove" onclick="removeSize(1)">
      <i class="fas fa-times"></i>
    </button>
  </div>
  <div class="size-form">
    <div class="size-field">
      <label>Размер</label>
      <input type="text" name="size_1_name" value="S" required>
    </div>
    <div class="size-field">
      <label>Количество</label>
      <input type="number" name="size_1_stock" value="10" min="0">
    </div>
    <div class="size-field">
      <label>Макс. в заказе</label>
      <input type="number" name="size_1_max" min="1" placeholder="Без ограничений">
    </div>
    <div class="size-field">
      <label class="checkbox-label">
        <input type="checkbox" name="size_1_active" checked>
        <span class="checkmark"></span>
        Активен
      </label>
    </div>
  </div>
</div>
```

**JavaScript API:**
```javascript
// Добавление нового размера
function addSize()

// Удаление размера (с возможностью восстановления)
function removeSize(sizeId)

// Восстановление удаленного размера
function restoreSize(sizeId)

// Валидация размеров
function validateSizes()
```

## Data Models

### Существующие модели (используются без изменений):

1. **Product** - основная модель товара
2. **ProductSize** - размеры товара
3. **Category** - категории товаров

### Обработка данных размеров:

**При сохранении товара:**
1. Обработка удаленных размеров (по полям `delete_size_*`)
2. Обновление существующих размеров (по полям `size_*_*`)
3. Создание новых размеров (по полям `new_size_*_*`)

**Структура POST данных:**
```
# Существующие размеры
size_1_name = "S"
size_1_stock = "10"
size_1_max = "5"
size_1_active = "on"

# Новые размеры
new_size_1_name = "XXL"
new_size_1_stock = "5"
new_size_1_max = ""
new_size_1_active = "on"

# Удаленные размеры
delete_size_2 = "true"
```

## Error Handling

### Валидация формы:

1. **Обязательные поля:**
   - Подсветка красным цветом
   - Сообщения об ошибках под полями
   - Автоматическая прокрутка к первой ошибке

2. **Валидация цены:**
   - Проверка на положительное число
   - Форматирование с символом валюты

3. **Валидация размеров:**
   - Проверка заполнения названия размера
   - Проверка корректности числовых значений
   - Предотвращение дублирования размеров

4. **Валидация изображений:**
   - Проверка корректности URL
   - Обработка ошибок загрузки изображения
   - Показ заглушки при отсутствии изображения

### JavaScript обработка ошибок:

```javascript
// Подсветка поля с ошибкой
function highlightError(field, message)

// Удаление подсветки ошибки
function removeErrorHighlight(field)

// Показ общей ошибки формы
function showFormError(message)

// Прокрутка к первой ошибке
function scrollToFirstError()
```

## Testing Strategy

### Функциональное тестирование:

1. **Тестирование списка товаров:**
   - Отображение карточек товаров
   - Переключение между карточками и таблицей
   - Работа фильтров и поиска
   - Отсутствие дублированных кнопок

2. **Тестирование формы товара:**
   - Сохранение основной информации о товаре
   - Превью изображения в реальном времени
   - Валидация обязательных полей
   - Корректное отображение ошибок

3. **Тестирование управления размерами:**
   - Добавление новых размеров
   - Редактирование существующих размеров
   - Удаление размеров с возможностью восстановления
   - Сохранение размеров в базе данных

### Тестирование совместимости:

1. **Браузеры:** Chrome, Firefox, Safari, Edge
2. **Устройства:** Desktop, Tablet, Mobile
3. **Разрешения экрана:** 1920x1080, 1366x768, 768x1024, 375x667

### Тестирование производительности:

1. **Загрузка страниц:** < 2 секунд
2. **Отзывчивость интерфейса:** < 100ms на действия пользователя
3. **Размер ресурсов:** CSS < 50KB, JS < 100KB

## UI/UX Design Principles

### Цветовая схема:

```css
:root {
  /* Основные цвета */
  --primary-color: #007bff;
  --success-color: #28a745;
  --warning-color: #ffc107;
  --danger-color: #dc3545;
  --info-color: #17a2b8;
  
  /* Нейтральные цвета */
  --gray-100: #f8f9fa;
  --gray-200: #e9ecef;
  --gray-300: #dee2e6;
  --gray-400: #ced4da;
  --gray-500: #adb5bd;
  --gray-600: #6c757d;
  --gray-700: #495057;
  --gray-800: #343a40;
  --gray-900: #212529;
  
  /* Фон и текст */
  --bg-color: #ffffff;
  --text-color: #212529;
  --border-color: #dee2e6;
  --shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

### Типографика:

```css
/* Заголовки */
h1 { font-size: 2.5rem; font-weight: 600; }
h2 { font-size: 2rem; font-weight: 600; }
h3 { font-size: 1.75rem; font-weight: 600; }
h4 { font-size: 1.5rem; font-weight: 500; }

/* Основной текст */
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.text-small { font-size: 0.875rem; }
.text-muted { color: var(--gray-600); }
```

### Анимации:

```css
/* Переходы */
.transition { transition: all 0.3s ease; }
.fade-in { animation: fadeIn 0.5s ease; }
.slide-up { animation: slideUp 0.3s ease; }

/* Ключевые кадры */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
```

### Адаптивность:

```css
/* Мобильные устройства */
@media (max-width: 768px) {
  .product-grid { grid-template-columns: 1fr; }
  .form-row { flex-direction: column; }
  .btn { width: 100%; margin-bottom: 10px; }
}

/* Планшеты */
@media (min-width: 769px) and (max-width: 1024px) {
  .product-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Десктоп */
@media (min-width: 1025px) {
  .product-grid { grid-template-columns: repeat(3, 1fr); }
}
```

## Integration Points

### Django Admin Integration:

1. **Jazzmin настройки:**
   - Скрытие дублированных кнопок через `custom_css`
   - Кастомные иконки для товаров
   - Настройка темы и цветовой схемы

2. **Admin класс ProductAdmin:**
   - Кастомные методы для обработки размеров
   - Переопределение `save_model` для обработки POST данных
   - Добавление Media класса для подключения CSS/JS

3. **URL маршрутизация:**
   - Использование стандартных Django Admin URL
   - Дополнительные AJAX endpoints при необходимости

### Static Files Management:

```python
# settings.py
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "static_root"

# Подключение в шаблонах
{% load static %}
<link rel="stylesheet" href="{% static 'admin/css/product-form.css' %}">
<script src="{% static 'admin/js/product-form.js' %}"></script>
```

### Database Operations:

```python
# Обработка размеров в ProductAdmin
def handle_sizes(self, request, product):
    # Удаление размеров
    for key, value in request.POST.items():
        if key.startswith('delete_size_') and value == 'true':
            size_id = key.replace('delete_size_', '')
            ProductSize.objects.filter(id=size_id, product=product).delete()
    
    # Создание новых размеров
    # Обновление существующих размеров
```

## Security Considerations

1. **CSRF Protection:** Все формы включают CSRF токены
2. **Input Validation:** Серверная валидация всех данных
3. **XSS Prevention:** Экранирование пользовательского ввода
4. **Permission Checks:** Проверка прав доступа к админ-панели

## Performance Optimizations

1. **CSS/JS минификация** для production
2. **Lazy loading** изображений в карточках товаров
3. **Debounce** для поиска и фильтрации
4. **Оптимизация запросов** с использованием `select_related` и `prefetch_related`