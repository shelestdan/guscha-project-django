import React, { useState, useEffect } from 'react';
import { AddToCartButton, AddToPreorderButton } from '../components/features/cart/Cart';
import './ProductDetailPage.css';

const MAX_QUANTITY = 9;

const DetailPage = ({ item, itemType }) => {
  const [quantity, setQuantity] = useState(1);
  const [selectedSize, setSelectedSize] = useState(null);
  const [selectedColor, setSelectedColor] = useState(null);

  // Получаем максимальное доступное количество для выбранного размера
  const getMaxAvailableQuantity = () => {
    if (!selectedSize) return MAX_QUANTITY;
    
    // Если установлено ограничение max_quantity для размера, используем его
    if (selectedSize.max_quantity && selectedSize.max_quantity > 0) {
      return Math.min(selectedSize.max_quantity, MAX_QUANTITY);
    }
    
    return MAX_QUANTITY;
  };

  useEffect(() => {
    if (item && item.sizes && item.sizes.length > 0) {
      const firstAvailable = item.sizes.find(s => s.is_available && s.stock_quantity > 0) || item.sizes[0];
      setSelectedSize(firstAvailable);
    }
    if (item && item.colors && item.colors.length > 0) {
      const firstAvailableColor = item.colors.find(c => c.is_available && c.stock_quantity > 0) || item.colors[0];
      setSelectedColor(firstAvailableColor);
    }
  }, [item]);

  const handleQuantityClick = (clickedQuantity) => {
    setQuantity(clickedQuantity);
    console.log(`📦 Выбрано количество: ${clickedQuantity}`);
  };

  if (!item) return null;

  // Показываем только дополнительные изображения (тип 'additional')
  const extraImages = (item.product_images || []).filter(img => img.image_type === 'additional');

  const AddButton = itemType === 'product' ? AddToCartButton : AddToPreorderButton;
  const addButtonProps = itemType === 'product' 
    ? { productId: item.id, quantity, sizeId: selectedSize?.id }
    : { preorderId: item.id, sizeId: selectedSize?.id, quantity };

  return (
    <div className="pdp-root">
      <div className="pdp-left-panel">
        <div className="pdp-description-content">
          <h1 className="pdp-title">{item.name}</h1>
          <p className="pdp-price">{item.price} ₽</p>
          <div className="pdp-description-text">
            {item.description || 'No description available.'}
          </div>
        </div>
      </div>

      <div className="pdp-right-panel">
        <div className="pdp-sticky-controls">
          <div className="pdp-controls-grid">
            {/* Left side: Size & Color */}
            <div className="pdp-controls-left">
              {item.sizes && item.sizes.length > 0 && (
                <div className="pdp-control-group">
                  <span className="pdp-control-label">SIZE</span>
                  <div className="pdp-picker">
                    {item.sizes.map(size => (
                      <button
                        key={size.id}
                        className={`pdp-picker-btn${selectedSize?.id === size.id ? ' selected' : ''}${!size.is_available || size.stock_quantity === 0 ? ' disabled' : ''}`}
                        onClick={() => setSelectedSize(size)}
                        disabled={!size.is_available || size.stock_quantity === 0}
                      >
                        {size.size_name}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {item.colors && item.colors.length > 0 && (
                <div className="pdp-control-group">
                  <span className="pdp-control-label">COLOR</span>
                  <div className="pdp-picker">
                    {item.colors.map(color => (
                      <button
                        key={color.id}
                        className={`pdp-picker-btn pdp-color-btn${selectedColor?.id === color.id ? ' selected' : ''}${!color.is_available || color.stock_quantity === 0 ? ' disabled' : ''}`}
                        onClick={() => setSelectedColor(color)}
                        disabled={!color.is_available || color.stock_quantity === 0}
                        title={color.name}
                        style={{ backgroundColor: color.hex_code }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right side: Quantity & Add to Cart */}
            <div className="pdp-controls-right">
              <div className="pdp-control-group">
                <span className="pdp-control-label">QUANTITY</span>
                <div className="pdp-picker">
                  {Array.from({ length: MAX_QUANTITY }, (_, i) => i + 1).map(q => {
                    const maxAvailable = getMaxAvailableQuantity();
                    const isDisabledByStock = selectedSize && (!selectedSize.is_available || selectedSize.stock_quantity < q);
                    const isDisabledByLimit = q > maxAvailable;
                    const isDisabled = isDisabledByStock || isDisabledByLimit;
                    
                    return (
                      <button
                        key={q}
                        className={`pdp-picker-btn quantity${quantity === q ? ' selected' : ''}${isDisabled ? ' disabled' : ''}`}
                        onClick={() => !isDisabled && handleQuantityClick(q)}
                        disabled={isDisabled}
                        title={`Выбрать количество: ${q}`}
                      >
                        {q}
                      </button>
                    );
                  })}
                </div>
              </div>
              <AddButton
                {...addButtonProps}
                className="pdp-add-to-cart-btn"
                disabled={selectedSize && (!selectedSize.is_available || selectedSize.stock_quantity < quantity)}
              >
                {selectedSize && (!selectedSize.is_available || selectedSize.stock_quantity < quantity) ? 'SOLD OUT' : (itemType === 'product' ? 'ADD TO CART' : 'PREORDER')}
              </AddButton>
            </div>
          </div>
        </div>

        <div className="pdp-image-gallery">
          {extraImages.map((img, idx) => (
            <img key={idx} src={img.image_url} alt={img.alt_text || (item.name + ' - дополнительное фото ' + (idx + 1))} className="pdp-image" />
          ))}
        </div>
      </div>
    </div>
  );
};

export default DetailPage;
