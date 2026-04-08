import React, { memo, useCallback, useMemo } from 'react';
import './Cart.css';
import { getProductImageUrl, getProductName } from '../../../utils/imageUtils';

const CartItem = memo(({ item, onUpdateQuantity, onRemove }) => {
  const handleQuantityChange = useCallback((newQuantity) => {
    if (newQuantity > 0) {
      onUpdateQuantity(item.id, newQuantity);
    }
  }, [item.id, onUpdateQuantity]);

  // Мемоизированная проверка возможности увеличения количества
  const canIncrease = useMemo(() => {
    // Для предзаказов проверяем ограничения
    if (item.item_type === 'preorder') {
      // Проверяем остатки размера предзаказа
      if (item.size_stock_quantity !== undefined) {
        if (item.quantity >= item.size_stock_quantity) {
          return false;
        }
      }
      
      // Проверяем максимальное количество для размера предзаказа
      if (item.size_max_quantity !== undefined && item.size_max_quantity > 0) {
        if (item.quantity >= item.size_max_quantity) {
          return false;
        }
      }
      
      return true;
    }
    
    // Для обычных товаров - приоритет: остатки конкретного размера товара
    if (item.size_stock_quantity !== undefined) {
      // Проверяем остатки
      if (item.quantity >= item.size_stock_quantity) {
        return false;
      }
      
      // Проверяем максимальное количество для размера
      if (item.size_max_quantity !== undefined && item.size_max_quantity > 0) {
        if (item.quantity >= item.size_max_quantity) {
          return false;
        }
      }
      
      return true;
    }
    
    // Если нет информации о размере, проверяем общие остатки товара (fallback)
    if (item.product?.stock_quantity !== undefined) {
      return item.quantity < item.product.stock_quantity;
    }
    
    // По умолчанию разрешаем (если нет информации об остатках)
    return true;
  }, [item.item_type, item.quantity, item.size_stock_quantity, item.size_max_quantity, item.product?.stock_quantity]);

  // Мемоизированные значения для имени и изображения
  const productImage = useMemo(() => getProductImageUrl(item), [item]);
  const productName = useMemo(() => getProductName(item), [item]);
  
  // Мемоизированные handlers
  const handleDecrease = useCallback(() => handleQuantityChange(item.quantity - 1), [handleQuantityChange, item.quantity]);
  const handleIncrease = useCallback(() => handleQuantityChange(item.quantity + 1), [handleQuantityChange, item.quantity]);
  const handleRemove = useCallback(() => onRemove(item.id), [onRemove, item.id]);

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
            <button onClick={handleDecrease} disabled={item.quantity <= 1}>−</button>
            <span>{item.quantity}</span>
            <button 
              onClick={handleIncrease} 
              disabled={!canIncrease}
              title={!canIncrease ? 'Недостаточно товара на складе' : 'Увеличить количество'}
            >
              +
            </button>
          </div>
          <button className="remove-btn" onClick={handleRemove} title="Удалить товар">
            🗑️
          </button>
        </div>
      </div>

      <div className="cart-item-total">
        {((item.quantity || 0) * (parseFloat(item.price) || 0)).toFixed(2)} ₽
      </div>
    </div>
  );
});

CartItem.displayName = 'CartItem';

export default CartItem;