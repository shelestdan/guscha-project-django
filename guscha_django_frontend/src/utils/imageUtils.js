/**
 * Получение URL изображения для товара или предзаказа
 * @param {Object} item - Элемент корзины
 * @returns {string|null} URL изображения или null
 */
export const getProductImageUrl = (item) => {
  if (!item) return null;
  
  // Для предзаказов
  if (item.item_type === 'preorder') {
    return item.preorder_image_url || 
           item.preorder?.image_url || 
           null;
  }
  
  // Для обычных товаров
  if (item.item_type === 'product') {
    return item.product_image_url || 
           item.product?.primary_image || 
           item.product?.image_url || 
           null;
  }
  
  return null;
};

/**
 * Получение названия товара или предзаказа с размером
 * @param {Object} item - Элемент корзины
 * @returns {string} Название товара
 */
export const getProductName = (item) => {
  if (!item) return 'Товар';
  
  let baseName = '';
  
  if (item.item_type === 'preorder') {
    baseName = item.preorder_name || 
               item.preorder?.name || 
               item.item_name || 
               item.name || 
               'Предзаказ';
  } else if (item.item_type === 'product') {
    baseName = item.product_name || 
               item.product?.name || 
               item.item_name || 
               item.name || 
               'Товар';
  }
  
  // Добавляем размер если есть
  if (item.size_name) {
    return `${baseName} (${item.size_name})`;
  }
  
  return baseName;
};

/**
 * Получение краткого названия (без размера)
 * @param {Object} item - Элемент корзины
 * @returns {string} Название товара без размера
 */
export const getProductShortName = (item) => {
  if (!item) return 'Товар';
  
  if (item.item_type === 'preorder') {
    return item.preorder_name || 
           item.preorder?.name || 
           item.item_name || 
           'Предзаказ';
  } else if (item.item_type === 'product') {
    return item.product_name || 
           item.product?.name || 
           item.item_name || 
           'Товар';
  }
  
  return 'Товар';
};

/**
 * Получение размера товара
 * @param {Object} item - Элемент корзины
 * @returns {string|null} Размер или null
 */
export const getProductSize = (item) => {
  if (!item) return null;
  
  return item.size_name || null;
};
