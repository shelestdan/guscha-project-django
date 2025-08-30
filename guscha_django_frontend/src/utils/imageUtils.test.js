import {
  getProductImageUrl,
  getProductName,
  getProductShortName,
  getProductSize
} from './imageUtils';

describe('imageUtils', () => {
  describe('getProductImageUrl', () => {
    it('должен возвращать null для null/undefined item', () => {
      expect(getProductImageUrl(null)).toBeNull();
      expect(getProductImageUrl(undefined)).toBeNull();
    });

    it('должен возвращать URL изображения для предзаказа из preorder_image_url', () => {
      const item = {
        item_type: 'preorder',
        preorder_image_url: 'https://example.com/preorder.jpg'
      };

      expect(getProductImageUrl(item)).toBe('https://example.com/preorder.jpg');
    });

    it('должен возвращать URL изображения для предзаказа из preorder.image_url', () => {
      const item = {
        item_type: 'preorder',
        preorder: {
          image_url: 'https://example.com/preorder2.jpg'
        }
      };

      expect(getProductImageUrl(item)).toBe('https://example.com/preorder2.jpg');
    });

    it('должен приоритизировать preorder_image_url над preorder.image_url', () => {
      const item = {
        item_type: 'preorder',
        preorder_image_url: 'https://example.com/priority.jpg',
        preorder: {
          image_url: 'https://example.com/secondary.jpg'
        }
      };

      expect(getProductImageUrl(item)).toBe('https://example.com/priority.jpg');
    });

    it('должен возвращать URL изображения для товара из product_image_url', () => {
      const item = {
        item_type: 'product',
        product_image_url: 'https://example.com/product.jpg'
      };

      expect(getProductImageUrl(item)).toBe('https://example.com/product.jpg');
    });

    it('должен возвращать URL изображения для товара из product.primary_image', () => {
      const item = {
        item_type: 'product',
        product: {
          primary_image: 'https://example.com/primary.jpg'
        }
      };

      expect(getProductImageUrl(item)).toBe('https://example.com/primary.jpg');
    });

    it('должен возвращать URL изображения для товара из product.image_url', () => {
      const item = {
        item_type: 'product',
        product: {
          image_url: 'https://example.com/image.jpg'
        }
      };

      expect(getProductImageUrl(item)).toBe('https://example.com/image.jpg');
    });

    it('должен приоритизировать product_image_url над другими источниками', () => {
      const item = {
        item_type: 'product',
        product_image_url: 'https://example.com/priority.jpg',
        product: {
          primary_image: 'https://example.com/primary.jpg',
          image_url: 'https://example.com/image.jpg'
        }
      };

      expect(getProductImageUrl(item)).toBe('https://example.com/priority.jpg');
    });

    it('должен возвращать null для неизвестного типа товара', () => {
      const item = {
        item_type: 'unknown',
        some_image_url: 'https://example.com/image.jpg'
      };

      expect(getProductImageUrl(item)).toBeNull();
    });

    it('должен возвращать null если нет изображения для предзаказа', () => {
      const item = {
        item_type: 'preorder',
        preorder: {}
      };

      expect(getProductImageUrl(item)).toBeNull();
    });

    it('должен возвращать null если нет изображения для товара', () => {
      const item = {
        item_type: 'product',
        product: {}
      };

      expect(getProductImageUrl(item)).toBeNull();
    });
  });

  describe('getProductName', () => {
    it('должен возвращать "Товар" для null/undefined item', () => {
      expect(getProductName(null)).toBe('Товар');
      expect(getProductName(undefined)).toBe('Товар');
    });

    it('должен возвращать название предзаказа из preorder_name', () => {
      const item = {
        item_type: 'preorder',
        preorder_name: 'Предзаказ товара'
      };

      expect(getProductName(item)).toBe('Предзаказ товара');
    });

    it('должен возвращать название предзаказа из preorder.name', () => {
      const item = {
        item_type: 'preorder',
        preorder: {
          name: 'Название предзаказа'
        }
      };

      expect(getProductName(item)).toBe('Название предзаказа');
    });

    it('должен возвращать название предзаказа из item_name', () => {
      const item = {
        item_type: 'preorder',
        item_name: 'Общее название'
      };

      expect(getProductName(item)).toBe('Общее название');
    });

    it('должен возвращать название товара из product_name', () => {
      const item = {
        item_type: 'product',
        product_name: 'Название товара'
      };

      expect(getProductName(item)).toBe('Название товара');
    });

    it('должен возвращать название товара из product.name', () => {
      const item = {
        item_type: 'product',
        product: {
          name: 'Товар из объекта'
        }
      };

      expect(getProductName(item)).toBe('Товар из объекта');
    });

    it('должен добавлять размер к названию если он есть', () => {
      const item = {
        item_type: 'product',
        product_name: 'Футболка',
        size_name: 'L'
      };

      expect(getProductName(item)).toBe('Футболка (L)');
    });

    it('должен приоритизировать preorder_name над другими источниками для предзаказа', () => {
      const item = {
        item_type: 'preorder',
        preorder_name: 'Приоритетное название',
        preorder: {
          name: 'Вторичное название'
        },
        item_name: 'Общее название'
      };

      expect(getProductName(item)).toBe('Приоритетное название');
    });

    it('должен приоритизировать product_name над другими источниками для товара', () => {
      const item = {
        item_type: 'product',
        product_name: 'Приоритетное название',
        product: {
          name: 'Вторичное название'
        },
        item_name: 'Общее название'
      };

      expect(getProductName(item)).toBe('Приоритетное название');
    });

    it('должен возвращать "Предзаказ" по умолчанию для предзаказа без названия', () => {
      const item = {
        item_type: 'preorder'
      };

      expect(getProductName(item)).toBe('Предзаказ');
    });

    it('должен возвращать "Товар" по умолчанию для товара без названия', () => {
      const item = {
        item_type: 'product'
      };

      expect(getProductName(item)).toBe('Товар');
    });
  });

  describe('getProductShortName', () => {
    it('должен возвращать "Товар" для null/undefined item', () => {
      expect(getProductShortName(null)).toBe('Товар');
      expect(getProductShortName(undefined)).toBe('Товар');
    });

    it('должен возвращать название предзаказа без размера', () => {
      const item = {
        item_type: 'preorder',
        preorder_name: 'Предзаказ товара',
        size_name: 'XL'
      };

      expect(getProductShortName(item)).toBe('Предзаказ товара');
    });

    it('должен возвращать название товара без размера', () => {
      const item = {
        item_type: 'product',
        product_name: 'Футболка',
        size_name: 'M'
      };

      expect(getProductShortName(item)).toBe('Футболка');
    });

    it('должен приоритизировать preorder_name для предзаказа', () => {
      const item = {
        item_type: 'preorder',
        preorder_name: 'Приоритетное название',
        preorder: {
          name: 'Вторичное название'
        },
        item_name: 'Общее название'
      };

      expect(getProductShortName(item)).toBe('Приоритетное название');
    });

    it('должен приоритизировать product_name для товара', () => {
      const item = {
        item_type: 'product',
        product_name: 'Приоритетное название',
        product: {
          name: 'Вторичное название'
        },
        item_name: 'Общее название'
      };

      expect(getProductShortName(item)).toBe('Приоритетное название');
    });

    it('должен возвращать "Товар" для неизвестного типа', () => {
      const item = {
        item_type: 'unknown',
        some_name: 'Какое-то название'
      };

      expect(getProductShortName(item)).toBe('Товар');
    });
  });

  describe('getProductSize', () => {
    it('должен возвращать null для null/undefined item', () => {
      expect(getProductSize(null)).toBeNull();
      expect(getProductSize(undefined)).toBeNull();
    });

    it('должен возвращать размер из size_name', () => {
      const item = {
        size_name: 'XL'
      };

      expect(getProductSize(item)).toBe('XL');
    });

    it('должен возвращать null если размер не указан', () => {
      const item = {
        item_type: 'product',
        product_name: 'Товар без размера'
      };

      expect(getProductSize(item)).toBeNull();
    });

    it('должен возвращать null для пустого size_name', () => {
      const item = {
        size_name: ''
      };

      expect(getProductSize(item)).toBeNull();
    });

    it('должен корректно обрабатывать различные размеры', () => {
      const sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '42', '44', 'One Size'];
      
      sizes.forEach(size => {
        const item = { size_name: size };
        expect(getProductSize(item)).toBe(size);
      });
    });
  });
});