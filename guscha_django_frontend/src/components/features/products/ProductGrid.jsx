import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axiosInstance from '../../../api/axiosInstance';
import './ProductGrid.css';

export default function ProductGrid() {
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    let isMounted = true;
    const abortController = new AbortController();
    
    setStatus('loading');
    axiosInstance.get('/api/products/products/', { signal: abortController.signal })
      .then(response => {
        if (!isMounted) return;
        const data = response.data;
        const productList = Array.isArray(data) ? data : (data.results || data.products || []);
        const filteredProducts = productList.filter(p => p.is_active !== false);
        setProducts(filteredProducts);
        setStatus('success');
      })
      .catch((err) => {
        if (err.name === 'AbortError' || err.name === 'CanceledError') return;
        if (isMounted) setStatus('error');
      });
      
    return () => {
      isMounted = false;
      abortController.abort();
    };
  }, []);

  if (status === 'loading') {
    return (
      <div className="products-loading">
        <p>Загрузка...</p>
      </div>
    );
  }
  
  if (status === 'error') {
    return (
      <div className="products-error">
        <p>Ошибка загрузки</p>
      </div>
    );
  }

  return (
    <section className="products-section">
      <div className="products-grid">
        {products.map(product => (
          <Link 
            key={product.id} 
            to={`/products/${product.slug || product.id}`}
            className="product-card"
          >
            <div className="product-image">
              <img 
                src={product.image_url || product.primary_image} 
                alt={product.name}
                loading="lazy"
                draggable="false"
              />
            </div>
            <div className="product-info">
              <div className="product-row">
                <h3 className="product-name">{product.name}</h3>
                {product.colors && product.colors.length > 0 && (
                  <div className="product-colors">
                    {product.colors.map((color) => (
                      <span 
                        key={color.id || color.name}
                        className="color-dot"
                        style={{ backgroundColor: color.hex_code }}
                        title={color.name}
                      />
                    ))}
                  </div>
                )}
              </div>
              <div className="product-row">
                <p className="product-price">{product.price} ₽</p>
                {product.sizes && product.sizes.length > 0 && (
                  <div className="product-sizes">
                    {product.sizes.map((size) => (
                      <span 
                        key={size.id || size.size_name}
                        className={`size-text ${size.is_available ? '' : 'unavailable'}`}
                      >
                        {size.size_name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
