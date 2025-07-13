import React from 'react';
import Button from '../../ui/Button';

const ProductCard = React.memo(({ product, onAddToCart, className = '' }) => (
  <div className={`bg-white rounded-lg shadow p-4 flex flex-col items-center ${className}`}>
    <div className="w-full flex justify-center mb-4">
      <img src={product.primary_image || product.image_url} alt={product.name} className="object-contain h-40 w-full" loading="lazy" />
    </div>
    <div className="w-full flex flex-col items-center">
      <div className="text-lg font-semibold mb-2 text-center">{product.name}</div>
      <div className="text-gray-800 font-bold mb-4">{product.price} ₽</div>
      {onAddToCart && (
        <Button className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800 transition" onClick={() => onAddToCart(product.id)}>
          В корзину
        </Button>
      )}
    </div>
  </div>
));

export default ProductCard; 