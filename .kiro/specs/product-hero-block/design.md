# Design Document: Product Hero Block

## Overview

Компонент Product Hero Block — это визуально привлекательная секция для демонстрации товара на странице коллекций. Блок включает информацию о товаре (название, цена), кнопку предзаказа, фото модели в геометрической маске и фото товара с текстурным эффектом.

Дизайн основан на референсе с:
- Светло-бежевым фоном (#F5F3EE)
- Крупной типографикой слева
- Шестиугольной маской для фото модели (clip-path)
- Эффектом "рваной бумаги" для фото товара
- Минималистичной кнопкой предзаказа

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ProductHeroBlock Component                       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────────┐  ┌──────────────────┐   │
│  │   TextInfo   │  │   ModelImageMask    │  │  ProductImage    │   │
│  │              │  │                     │  │                  │   │
│  │  - Title     │  │  ┌───────────────┐  │  │  ┌────────────┐  │   │
│  │  - Price     │  │  │   Hexagon     │  │  │  │  Textured  │  │   │
│  │  - Button    │  │  │   Clip-Path   │  │  │  │   Border   │  │   │
│  │  - Arrow     │  │  │               │  │  │  │            │  │   │
│  │              │  │  └───────────────┘  │  │  └────────────┘  │   │
│  └──────────────┘  └─────────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Django Admin → API → React Component → Rendered UI
     │                    │
     ├── model_image ────►├── ModelImageMask
     ├── product_image ──►├── ProductImage
     ├── title ──────────►├── TextInfo
     └── price ──────────►└── TextInfo
```

## Components and Interfaces

### ProductHeroBlock Component

```jsx
interface ProductHeroBlockProps {
  title: string;           // Название товара (например, "ДЖИНСЫ")
  price: number;           // Цена в рублях
  modelImage: string;      // URL фото модели
  productImage: string;    // URL фото товара
  onPreorder: () => void;  // Callback для кнопки предзаказа
  onNavigate: () => void;  // Callback для стрелки навигации
  productSlug?: string;    // Slug для навигации к товару
}
```

### CSS Structure

```css
.product-hero-block {
  background: #F5F3EE;
  display: flex;
  align-items: center;
  padding: 60px 80px;
  min-height: 500px;
  position: relative;
}

.hero-text-info {
  flex: 0 0 30%;
  z-index: 2;
}

.hero-model-image {
  flex: 1;
  position: relative;
}

.hero-product-image {
  flex: 0 0 20%;
  position: relative;
}
```

### Hexagon Clip-Path

```css
.model-image-mask {
  clip-path: polygon(
    25% 0%,
    75% 0%,
    100% 50%,
    75% 100%,
    25% 100%,
    0% 50%
  );
}
```

### Textured Border Effect

Для эффекта "рваной бумаги" используется:
- SVG маска или filter
- Псевдо-элементы с текстурой
- Небольшой поворот (transform: rotate)

## Data Models

### Backend Model (Django)

```python
class ProductHeroContent(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    model_image = models.ImageField(upload_to='hero/models/')
    product_image = models.ImageField(upload_to='hero/products/')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
```

### API Response

```json
{
  "id": 1,
  "title": "ДЖИНСЫ",
  "price": 7900.00,
  "model_image": "/media/hero/models/model1.jpg",
  "product_image": "/media/hero/products/jeans1.png",
  "product_slug": "jeans-wide-leg"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

После анализа prework, следующие свойства были объединены или исключены:
- Свойства 6.1 и 6.2 объединены в одно свойство о загрузке изображений
- Визуальные свойства (hover states) исключены как нетестируемые программно
- Свойства позиционирования объединены в тесты компонентов

### Property 1: Price Format Consistency

*For any* valid price number, the formatted output should match the pattern "X XXX.XX ₽" with proper thousand separators and two decimal places.

**Validates: Requirements 1.2**

### Property 2: Component Renders Required Elements

*For any* valid ProductHeroBlockProps, the rendered component should contain all required elements: title, price, preorder button, navigation arrow, model image, and product image.

**Validates: Requirements 1.1, 4.1, 5.1**

### Property 3: Click Handler Invocation

*For any* click event on the preorder button, the onPreorder callback should be invoked exactly once.

**Validates: Requirements 4.2**

### Property 4: Navigation Handler Invocation

*For any* click event on the navigation arrow, the onNavigate callback should be invoked exactly once.

**Validates: Requirements 5.2**

### Property 5: Image URL Propagation

*For any* image URL provided via props, the corresponding img element should have that URL as its src attribute.

**Validates: Requirements 6.1, 6.2, 6.3**

## Error Handling

### Missing Images

```jsx
const handleImageError = (e) => {
  e.target.src = '/images/placeholder.png';
  e.target.classList.add('image-error');
};
```

### Loading States

- Skeleton loader для изображений
- Плавное появление (fade-in) после загрузки

### API Errors

- Fallback UI при ошибке загрузки данных
- Retry механизм для повторной загрузки

## Testing Strategy

### Unit Testing

Используем Jest + React Testing Library для:
- Проверки рендеринга компонента
- Тестирования click handlers
- Проверки форматирования цены

### Property-Based Testing

Используем **fast-check** для property-based тестов:

```javascript
import fc from 'fast-check';
```

Каждый property-based тест должен:
- Выполнять минимум 100 итераций
- Быть помечен комментарием с номером свойства из design.md
- Использовать формат: `**Feature: product-hero-block, Property {number}: {property_text}**`

### Test Examples

```javascript
// **Feature: product-hero-block, Property 1: Price Format Consistency**
test('price formatting follows pattern', () => {
  fc.assert(
    fc.property(fc.float({ min: 0, max: 1000000 }), (price) => {
      const formatted = formatPrice(price);
      return /^\d{1,3}(\s\d{3})*\.\d{2}\s₽$/.test(formatted);
    }),
    { numRuns: 100 }
  );
});
```

### Visual Testing

- Snapshot тесты для CSS классов
- Storybook для визуальной проверки
