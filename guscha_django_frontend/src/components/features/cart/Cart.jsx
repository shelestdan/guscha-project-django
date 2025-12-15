import { useToast } from '../../../hooks/useToast';

import React from 'react';
import InstrumentCartIcon from '../../../assets/icons/instrument_x4fdrqsfczqn.svg';
import { useCartStore } from '../../../store/cartStore';
import CartItem from './CartItem';
import './Cart.css';

// Компонент иконки корзины на Zustand
export const CartIcon = () => {
  const cartCount = useCartStore((state) => state.count);
  const toggleCart = useCartStore((state) => state.toggleCart);

  return (
    <button className="cart-icon" onClick={toggleCart}>
      <img src={InstrumentCartIcon} alt="Корзина" width={28} height={28} />
      {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
    </button>
  );
};

// Компонент боковой панели корзины на Zustand
export const CartSidebar = () => {
  const cartItems = useCartStore((state) => state.items);
  const cartTotal = useCartStore((state) => state.total);
  const isOpen = useCartStore((state) => state.isOpen);
  const updateQuantity = useCartStore((state) => state.updateQuantity);
  const removeFromCart = useCartStore((state) => state.removeFromCart);
  const toggleCart = useCartStore((state) => state.toggleCart);

  return (
    <div className={`cart-overlay${isOpen ? ' open' : ''}`} onClick={toggleCart}>
      <div className={`cart-sidebar${isOpen ? ' open' : ''}`} onClick={(e) => e.stopPropagation()}>
        <div className="cart-header">
          <h3>Корзина</h3>
          <button className="cart-close" onClick={toggleCart}>×</button>
        </div>

        <div className="cart-content">
          {cartItems.length === 0 ? (
            <div className="cart-empty">
              <p>Корзина пуста</p>
            </div>
          ) : (
            <>
              <div className="cart-items">
                {cartItems.map((item) => (
                  <CartItem
                    key={item.id}
                    item={item}
                    onUpdateQuantity={updateQuantity}
                    onRemove={removeFromCart}
                  />
                ))}
              </div>

              <div className="cart-footer">
                <div className="cart-total">
                  <strong>Итого: {(typeof cartTotal === 'number' && !isNaN(cartTotal) ? cartTotal : 0).toFixed(2)} ₽</strong>
                </div>
                <button 
                  className="checkout-btn"
                  onClick={() => {
                    toggleCart();
                    window.location.href = '/checkout';
                  }}
                >
                  Оформить заказ
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// Компонент кнопки "Добавить в корзину"
export const AddToCartButton = ({ productId, sizeId = null, quantity = 1, className = '', disabled = false, children = 'Добавить в корзину' }) => {
  const addToCart = useCartStore((state) => state.addToCart);
  const { showSuccess, showError } = useToast();
  const [loading, setLoading] = React.useState(false);

  const handleClick = async () => {
    if (disabled) return;
    
    setLoading(true);
    try {
      const success = await addToCart(productId, sizeId, quantity);
      if (success) {
        showSuccess('Товар добавлен в корзину');
      } else {
        showError('Не удалось добавить товар');
      }
    } catch (error) {
      showError(error.message || 'Произошла ошибка');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button className={className} onClick={handleClick} disabled={disabled || loading}>
      {loading ? 'Добавление...' : children}
    </button>
  );
};

// Компонент кнопки "Добавить предзаказ в корзину"
export const AddToPreorderButton = ({ preorderId, sizeId = null, quantity = 1, className = '', disabled = false, children = 'Предзаказать' }) => {
  const addPreorderToCart = useCartStore((state) => state.addPreorderToCart);
  const { showSuccess, showError } = useToast();
  const [loading, setLoading] = React.useState(false);

  const handleClick = async () => {
    if (disabled) return;
    
    setLoading(true);
    try {
      const success = await addPreorderToCart(preorderId, sizeId, quantity);
      if (success) {
        showSuccess('Предзаказ добавлен в корзину');
      } else {
        showError('Не удалось добавить предзаказ');
      }
    } catch (error) {
      showError(error.message || 'Произошла ошибка');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button className={className} onClick={handleClick} disabled={disabled || loading}>
      {loading ? 'Добавление...' : children}
    </button>
  );
};

// Компонент страницы оформления заказа
export const CheckoutPage = () => {
  const clearCart = useCartStore((state) => state.clearCart);
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    // ... логика оформления заказа ...
    await clearCart();
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* ... форма ... */}
      <button type="submit" disabled={loading}>
        {loading ? 'Оформление...' : 'Оформить заказ'}
      </button>
    </form>
  );
};

export default CartSidebar;