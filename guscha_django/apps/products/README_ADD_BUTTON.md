# Кнопка "ДОБАВИТЬ" для размеров товаров и предзаказов

## Описание
Добавлена стилизованная кнопка "ДОБАВИТЬ" в админку Django для динамического создания новых полей размеров товаров и предзаказов.

## Функциональность
- ✅ Автоматическое обнаружение и стилизация кнопок "Add another" для inline форм размеров
- ✅ Красивый дизайн кнопки с градиентом и анимациями
- ✅ Поддержка как товаров (Product), так и предзаказов (Preorder)
- ✅ Адаптивный дизайн для мобильных устройств
- ✅ Поддержка темной темы
- ✅ Анимации при добавлении новых форм

## Файлы проекта

### JavaScript
- `apps/products/static/products/js/admin_inline_forms.js` - Основная логика стилизации кнопок

### CSS
- `apps/products/static/products/css/admin_inline_styles.css` - Стили для кнопки и анимации

### Шаблоны
- `apps/products/templates/admin/products/product/change_form.html` - Шаблон для товаров
- `apps/products/templates/admin/products/preorder/change_form.html` - Шаблон для предзаказов

### Админ-классы
- `apps/products/admin/product_admin.py` - Обновлен ProductAdmin
- `apps/products/admin/preorder_admin.py` - Обновлен PreorderAdmin

## Как это работает

1. **Автоматическое обнаружение**: JavaScript автоматически находит все кнопки "Add another" в inline формах
2. **Фильтрация**: Определяет, какие кнопки относятся к размерам товаров/предзаказов
3. **Стилизация**: Применяет кастомные стили и заменяет текст на "ДОБАВИТЬ"
4. **Динамическое обновление**: Отслеживает добавление новых форм и стилизует их

## Настройки inline-классов

### ProductSizeInline
```python
class ProductSizeInline(BaseSizeInline):
    model = ProductSize
    extra = 1  # Показывать одну пустую форму
    can_delete = True  # Разрешить удаление
    fields = ['size_name', 'stock_quantity', 'limit', 'is_active', 'is_sold_out']
```

### PreorderSizeInline
```python
class PreorderSizeInline(BaseSizeInline):
    model = PreorderSize
    extra = 1  # Показывать одну пустую форму
    can_delete = True  # Разрешить удаление
    fields = ['size_name', 'stock_quantity', 'max_quantity', 'is_active', 'is_sold_out']
```

## Использование

1. Перейдите в админку Django: `http://localhost:8000/admin/`
2. Откройте любой товар или предзаказ для редактирования
3. Прокрутите до секции "Размеры"
4. Увидите стилизованную кнопку "ДОБАВИТЬ" внизу таблицы размеров
5. Нажмите на кнопку для добавления нового размера

## Особенности дизайна

- **Градиентный фон**: Синий градиент с эффектом глубины
- **Анимации**: Плавные переходы при наведении и нажатии
- **Иконка плюса**: Вращается при наведении
- **Адаптивность**: Корректно отображается на всех устройствах
- **Accessibility**: Поддержка фокуса клавиатуры

## Совместимость

- ✅ Django 4.x+
- ✅ Django Unfold админка
- ✅ Все современные браузеры
- ✅ Мобильные устройства
- ✅ Темная тема

## Техническая реализация

### Обнаружение кнопок
```javascript
$('.add-row a').each(function() {
    const $button = $(this);
    const text = $button.text().trim();
    
    if (text.includes('размер') || text.includes('size')) {
        // Стилизация кнопки
    }
});
```

### Отслеживание динамических изменений
```javascript
const observer = new MutationObserver(function(mutations) {
    // Обновление стилей при добавлении новых форм
});
```

## Поддержка и расширение

Для добавления поддержки других inline форм:
1. Обновите условие в JavaScript для обнаружения нужных кнопок
2. Создайте соответствующий шаблон change_form.html
3. Добавьте `change_form_template` в админ-класс

## Отладка

Если кнопка не отображается:
1. Проверьте, что статические файлы собраны: `python manage.py collectstatic`
2. Убедитесь, что в inline-классе установлено `extra=1`
3. Проверьте консоль браузера на наличие JavaScript ошибок
4. Убедитесь, что шаблоны находятся в правильных директориях