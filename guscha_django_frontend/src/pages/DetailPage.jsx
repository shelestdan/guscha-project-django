import React, { useState, useEffect } from 'react';
import { AddToCartButton, AddToPreorderButton } from '../components/features/cart/Cart';
import './ProductDetailPage.css';

const MAX_QUANTITY = 9;

const DetailPage = ({ item, itemType }) => {
  const [quantity, setQuantity] = useState(1);
  const [selectedSize, setSelectedSize] = useState(null);

  useEffect(() => {
    if (item && item.sizes && item.sizes.length > 0) {
      const firstAvailable = item.sizes.find(s => s.is_available && s.stock_quantity > 0) || item.sizes[0];
      setSelectedSize(firstAvailable);
    }
  }, [item]);

  const handleQuantityClick = (clickedQuantity) => {
    setQuantity(clickedQuantity);
    console.log(`📦 Выбрано количество: ${clickedQuantity}`);
  };

  if (!item) return null;

  const allImages = [item.image_url, ...(item.images || [])].filter(Boolean);
  const mainImage = allImages.find(img => typeof img === 'string');
  const extraImages = allImages.filter(img => typeof img === 'object' && img.image_url !== mainImage);

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
            <div className="pdp-control-group">
              <span className="pdp-control-label">QUANTITY</span>
              <div className="pdp-picker">
                {Array.from({ length: MAX_QUANTITY }, (_, i) => i + 1).map(q => (
                  <button
                    key={q}
                    className={`pdp-picker-btn quantity${quantity === q ? ' selected' : ''}`}
                    onClick={() => handleQuantityClick(q)}
                    disabled={selectedSize && (!selectedSize.is_available || selectedSize.stock_quantity < q)}
                    title={`Выбрать количество: ${q}`}
                  >
                    {q}
                  </button>
                ))}
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

        <div className="pdp-image-gallery">
          {mainImage && (
            <img src={mainImage} alt={item.name + ' - main'} className="pdp-image" />
          )}
          {extraImages.map((img, idx) => (
            <img key={idx} src={img.image_url} alt={img.alt_text || (item.name + ' - extra ' + (idx + 1))} className="pdp-image" />
          ))}
        </div>
      </div>
    </div>
  );
};

export default DetailPage;
