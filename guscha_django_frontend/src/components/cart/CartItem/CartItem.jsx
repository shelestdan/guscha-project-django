import React from 'react';
import { useCartStore } from '../../../store/cartStore';
import { useToast } from '../../../hooks/useToast';
import { getProductImageUrl, getProductName, getProductSize } from '../../../utils/imageUtils';

const CartItem = ({ item }) => {
  const { updateQuantity, removeItem } = useCartStore();
  const { showToast } = useToast();

  const handleQuantityChange = (e) => {
    const newQuantity = parseInt(e.target.value);
    if (newQuantity > 0) {
      updateQuantity(item.id, newQuantity);
    }
  };

  const handleIncrease = () => {
    updateQuantity(item.id, item.quantity + 1);
  };

  const handleDecrease = () => {
    if (item.quantity > 1) {
      updateQuantity(item.id, item.quantity - 1);
    }
  };

  const handleRemove = async () => {
    try {
      await removeItem(item.id);
      showToast('Товар удален из корзины', 'success');
    } catch (error) {
      showToast('Ошибка при удалении товара', 'error');
    }
  };

  const formatPrice = (price) => {
    const numPrice = parseFloat(price);
    return new Intl.NumberFormat('ru-RU').format(numPrice) + ' ₽';
  };

  const productName = getProductName(item);
  const productSize = getProductSize(item);
  const productImageUrl = getProductImageUrl(item);

  return (
    <div className="cart-item">
      <div className="cart-item__image">
        <img src={productImageUrl || '/default-image.jpg'} alt={productName} />
      </div>
      
      <div className="cart-item__details">
        <h3 className="cart-item__name">{productName}</h3>
        
        {item.item_type === 'preorder' && (
          <p className="cart-item__preorder">Предзаказ</p>
        )}
        
        {productSize && (
          <p className="cart-item__size">Размер: {productSize}</p>
        )}
        
        <div className="cart-item__price">
          {formatPrice(item.price)}
        </div>
      </div>
      
      <div className="cart-item__controls">
        <div className="cart-item__quantity">
          <label htmlFor={`quantity-${item.id}`}>Количество:</label>
          <div className="cart-item__quantity-controls">
            <button
              onClick={handleDecrease}
              disabled={item.quantity <= 1}
              className="cart-item__quantity-btn"
              aria-label="Уменьшить количество"
            >
              -
            </button>
            <input
              id={`quantity-${item.id}`}
              type="number"
              min="1"
              value={item.quantity}
              onChange={handleQuantityChange}
              className="cart-item__quantity-input"
            />
            <button
              onClick={handleIncrease}
              className="cart-item__quantity-btn"
              aria-label="Увеличить количество"
            >
              +
            </button>
          </div>
        </div>
        
        <button
          onClick={handleRemove}
          className="cart-item__remove-btn"
          aria-label="Удалить товар"
        >
          Удалить
        </button>
      </div>
    </div>
  );
};

export default CartItem;