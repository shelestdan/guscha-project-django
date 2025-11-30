import React, { useState, useEffect } from 'react';
import axiosInstance from '../../../api/axiosInstance';
import ChromaGrid from './ChromaGrid';
import './ChromaGrid.css';
import './ProductGrid.css';

export default function ProductGrid() {
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    setStatus('loading');
    axiosInstance.get('/api/products/products/')
      .then(response => {
        const data = response.data;
        const productList = Array.isArray(data) ? data : (data.results || data.products || []);
        const filteredProducts = productList.filter(p => p.is_active !== false);
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

  // Преобразуем продукты в формат ChromaGrid
  const chromaItems = products.map(product => ({
    id: product.id,
    slug: product.slug,
    image: product.image_url || product.primary_image,
    title: product.name,
    price: product.price,
    sizes: product.sizes || []
  }));

  return (
    <section className="product-grid-section">
      <div className="product-grid-container chroma-container">
        <ChromaGrid 
          items={chromaItems}
          radius={300}
          damping={0.45}
          fadeOut={0.6}
          ease="power3.out"
        />
      </div>
    </section>
  );
}
