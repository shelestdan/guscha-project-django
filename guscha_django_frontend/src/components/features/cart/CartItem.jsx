import React from 'react';
import './Cart.css';
import { getProductImageUrl, getProductName } from '../../../utils/imageUtils';

const CartItem = ({ item, onUpdateQuantity, onRemove }) => {
  const handleQuantityChange = (newQuantity) => {
    if (newQuantity > 0) {
      onUpdateQuantity(item.id, newQuantity);
    }
  };

  // Проверяем, можно ли увеличить количество
  const canIncrease = () => {
    // Отладочная информация для диагностики
    console.log('🔢 CartItem canIncrease debug:', {
      item_type: item.item_type,
      current_quantity: item.quantity,
      size_stock_quantity: item.size_stock_quantity,
      size_max_quantity: item.size_max_quantity,
      product_stock_quantity: item.product?.stock_quantity,
      product_name: item.product?.name
    });
    
    // Для предзаказов проверяем ограничения
    if (item.item_type === 'preorder') {
      // Проверяем остатки размера предзаказа
      if (item.size_stock_quantity !== undefined) {
        if (item.quantity >= item.size_stock_quantity) {
          console.log(`🔢 Preorder size stock limit reached: ${item.quantity} >= ${item.size_stock_quantity}`);
          return false;
        }
      }
      
      // Проверяем максимальное количество для размера предзаказа
      if (item.size_max_quantity !== undefined && item.size_max_quantity > 0) {
        if (item.quantity >= item.size_max_quantity) {
          console.log(`🔢 Preorder size max quantity limit reached: ${item.quantity} >= ${item.size_max_quantity}`);
          return false;
        }
      }
      
      return true;
    }
    
    // Для обычных товаров - приоритет: остатки конкретного размера товара
    if (item.size_stock_quantity !== undefined) {
      console.log(`🔢 Checking size stock: current quantity ${item.quantity}, size stock ${item.size_stock_quantity}`);
      
      // Проверяем остатки
      if (item.quantity >= item.size_stock_quantity) {
        return false;
      }
      
      // Проверяем максимальное количество для размера
      if (item.size_max_quantity !== undefined && item.size_max_quantity > 0) {
        if (item.quantity >= item.size_max_quantity) {
          console.log(`🔢 Product size max quantity limit reached: ${item.quantity} >= ${item.size_max_quantity}`);
          return false;
        }
      }
      
      return true;
    }
    
    // Если нет информации о размере, проверяем общие остатки товара (fallback)
    if (item.product?.stock_quantity !== undefined) {
      console.log(`🔢 Checking product stock: current quantity ${item.quantity}, product stock ${item.product.stock_quantity}`);
      return item.quantity < item.product.stock_quantity;
    }
    
    // По умолчанию разрешаем (если нет информации об остатках)
    console.log(`🔢 No stock info available, allowing increase`);
    return true;
  };

  // Используем универсальные утилиты для имени и изображения
  const productImage = getProductImageUrl(item);
  const productName = getProductName(item);
  
  // Отладочная информация
  console.log('🖼️ CartItem image debug:', {
    item_type: item.item_type,
    productImage,
    productName,
    product_image_url: item.product_image_url,
    preorder_image_url: item.preorder_image_url
  });

  return (
    <div className="cart-item">
      <div className="cart-item-image">
        {productImage ? (
          <img src={productImage} alt={productName} />
        ) : (
          <div className="cart-item-placeholder">
            <span>Нет фото</span>
          </div>
        )}
      </div>

      <div className="cart-item-details">
        <h4>{productName}</h4>
        <p className="cart-item-price">{(parseFloat(item.price) || 0).toFixed(2)} ₽</p>
        <div className="cart-item-controls">
          <div className="quantity-controls">
            <button onClick={() => handleQuantityChange(item.quantity - 1)} disabled={item.quantity <= 1}>−</button>
            <span>{item.quantity}</span>
            <button 
              onClick={() => handleQuantityChange(item.quantity + 1)} 
              disabled={!canIncrease()}
              title={!canIncrease() ? 'Недостаточно товара на складе' : 'Увеличить количество'}
            >
              +
            </button>
          </div>
          <button className="remove-btn" onClick={() => onRemove(item.id)} title="Удалить товар">
            🗑️
          </button>
        </div>
      </div>

      <div className="cart-item-total">
        {((item.quantity || 0) * (parseFloat(item.price) || 0)).toFixed(2)} ₽
      </div>
    </div>
  );
};

export default CartItem;