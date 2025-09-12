import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCartStore } from '../../../store/cartStore';
import { useToast } from '../../../hooks/useToast';

const ProductCard = ({ product, showAddToCart = true }) => {
  const { addToCart } = useCartStore();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [selectedSize, setSelectedSize] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleAddToCart = async () => {
    if (!product.is_available) {
      showToast('Товар недоступен', 'error');
      return;
    }

    if (product.sizes && product.sizes.length > 0 && !selectedSize) {
      showToast('Пожалуйста, выберите размер', 'warning');
      return;
    }

    setIsLoading(true);
    try {
      await addToCart({
        product_id: product.id,
        quantity: 1,
        size_id: selectedSize || null
      });
      showToast('Товар добавлен в корзину', 'success');
    } catch (error) {
      console.error('Ошибка при добавлении в корзину:', error);
      showToast('Ошибка при добавлении в корзину', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const formatPrice = (price) => {
    const numPrice = parseFloat(price);
    return new Intl.NumberFormat('ru-RU').format(numPrice) + ' ₽';
  };

  const handleCardClick = () => {
    navigate(`/products/${product.slug}`);
  };

  return (
    <div className="product-card" onClick={handleCardClick}>
      <div className="product-image">
        <img 
          src={product.primary_image || '/default-product.jpg'} 
          alt={product.name}
          loading="lazy"
        />
      </div>
      
      <div className="product-info">
        <h3 className="product-name">{product.name}</h3>
        <div className="product-price">
          {product.discounted_price ? (
            <>
              <span className="discounted-price">{formatPrice(product.discounted_price)}</span>
              <span className="original-price line-through">{formatPrice(product.price)}</span>
            </>
          ) : (
            formatPrice(product.price)
          )}
        </div>
        
        {showAddToCart && (
          <div className="product-actions">
            {product.sizes && product.sizes.length > 0 && (
              <div className="product-sizes">
                <select
                  value={selectedSize}
                  onChange={(e) => {
                    e.stopPropagation();
                    setSelectedSize(e.target.value);
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <option value="">Размер</option>
                  {product.sizes.map(size => (
                    <option key={size.id} value={size.id}>
                      {size.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            
            <button
              className="add-to-cart-btn"
              onClick={(e) => {
                e.stopPropagation();
                handleAddToCart();
              }}
              disabled={!product.is_available || isLoading}
            >
              {isLoading ? 'Добавление...' : 
               !product.is_available ? 'Недоступен' : 'В корзину'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductCard;