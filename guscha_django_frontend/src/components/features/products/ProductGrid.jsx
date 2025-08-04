import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axiosInstance from '../../../api/axiosInstance';
import './ProductGrid.css';

export default function ProductGrid() {
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    setStatus('loading');
    axiosInstance.get('/api/products/products/')
      .then(response => {
        const data = response.data;
        console.log('API Response:', data);
        const productList = Array.isArray(data) ? data : (data.results || data.products || []);
        console.log('Product List:', productList);
        const filteredProducts = productList.filter(p => p.is_active !== false);
        console.log('Filtered Products:', filteredProducts);
        setProducts(filteredProducts);
        setStatus('success');
      })
      .catch(() => setStatus('error'));
  }, []);

  if (status === 'loading') {
    return (
      <div className="product-grid-loading">
        <div className="loading-spinner"></div>
        <p>Загрузка товаров...</p>
      </div>
    );
  }
  
  if (status === 'error') {
    return (
      <div className="product-grid-error">
        <div className="error-content">
          <h3>Ошибка загрузки товаров</h3>
          <p>Попробуйте обновить страницу</p>
        </div>
      </div>
    );
  }

  return (
    <section className="product-grid-section">
      <div className="product-grid-container">
        <div className="product-grid">
          {products.map(product => (
            <div key={product.id} className="product-card">
              <Link to={`/products/${product.slug}`} className="product-link">
                <div className="product-image-container">
                  <img 
                    src={product.image_url || product.primary_image} 
                    alt={product.name} 
                    loading="lazy"
                    className="product-image"
                    onContextMenu={(e) => e.preventDefault()}
                    onDragStart={(e) => e.preventDefault()}
                    draggable="false"
                  />
                </div>
                
                <div className="product-info">
                  <h3 className="product-name">{product.name}</h3>
                  <div className="product-price">{product.price} ₽</div>
                </div>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}