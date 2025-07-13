import React, { useEffect, useState } from "react";
import { Link } from 'react-router-dom';
import { fetchPreorders } from '../../../api/preordersApi';
import "../../../styles/ProductShowcase.css";

export default function ProductShowcase() {
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState('loading'); // 'loading', 'success', 'error', 'empty'
  const [current, setCurrent] = useState(0);
  const [animating, setAnimating] = useState(false);
  const [nextIndex, setNextIndex] = useState(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 900);
  
  useEffect(() => {
    setStatus('loading');
    fetchPreorders({ is_active: 'true' })
      .then((data) => {
        // API возвращает объект с полями count, next, previous, results
        const preordersList = data?.results || [];
        if (preordersList.length > 0) {
          setProducts(preordersList);
          setStatus('success');
        } else {
          setStatus('empty');
        }
      })
      .catch((error) => {
        console.error("Could not fetch preorders:", error);
        setStatus('error');
      });
  }, []);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth <= 900);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const nextProductHandler = () => {
    if (animating || products.length <= 1) return;
    
    const ni = (current + 1) % products.length;
    setNextIndex(ni);
    setAnimating(true);
    
    setTimeout(() => {
      setCurrent(ni);
      setNextIndex(null);
      setAnimating(false);
    }, 350);
  };

  if (status === 'loading') {
    return <div className="product-showcase-root status-message">Загрузка предзаказов...</div>;
  }

  if (status === 'error') {
    return <div className="product-showcase-root status-message">Ошибка загрузки. Попробуйте позже.</div>;
  }

  if (status === 'empty') {
    return <div className="product-showcase-root status-message">Предзаказы не найдены.</div>;
  }

  const product = products[current];
  const nextProduct = typeof nextIndex === 'number' ? products[nextIndex] : null;

  return (
    <div className="product-showcase-root">
      <Link to={`/preorders/${product.id}`} className="product-showcase-link">
        <div className="product-showcase-images">
          {(!animating && !nextProduct) && (
            <>
              {!isMobile && (
                <div className="product-showcase-left product-anim-in">
                  <div className="product-showcase-model">
                  {(product.model_image || product.image_url) ? (
                    <img src={product.model_image || product.image_url} alt={product.name} loading="lazy" />
                  ) : (
                    <div className="placeholder-image">Нет изображения</div>
                  )}
                  </div>
                </div>
              )}
              <div className="product-showcase-center product-anim-in">
                <div className="product-showcase-product">
                  {(product.product_image || product.image_url) ? (
                    <img src={product.product_image || product.image_url} alt={product.name} loading="lazy" />
                  ) : (
                    <div className="placeholder-image">Нет изображения</div>
                  )}
                </div>
              </div>
            </>
          )}
          {(animating && nextProduct) && (
            <>
              {/* Старый комплект */}
              <div className="product-showcase-overlay">
                {!isMobile && (
                  <div className="product-showcase-left product-anim-out">
                    <div className="product-showcase-model">
                      {(product.model_image || product.image_url) ? (
                        <img src={product.model_image || product.image_url} alt={product.name} loading="lazy" />
                      ) : (
                        <div className="placeholder-image">Нет изображения</div>
                      )}
                    </div>
                  </div>
                )}
                <div className="product-showcase-center product-anim-out">
                  <div className="product-showcase-product">
                    {(product.product_image || product.image_url) ? (
                      <img src={product.product_image || product.image_url} alt={product.name} loading="lazy" />
                    ) : (
                      <div className="placeholder-image">Нет изображения</div>
                    )}
                  </div>
                </div>
              </div>
              {/* Новый комплект */}
              {!isMobile && (
                <div className="product-showcase-left product-anim-in product-anim-new">
                  <div className="product-showcase-model">
                    {(nextProduct.model_image || nextProduct.image_url) ? (
                      <img src={nextProduct.model_image || nextProduct.image_url} alt={nextProduct.name} loading="lazy" />
                    ) : (
                      <div className="placeholder-image">Нет изображения</div>
                    )}
                  </div>
                </div>
              )}
              <div className="product-showcase-center product-anim-in product-anim-new">
                <div className="product-showcase-product">
                  {(nextProduct.product_image || nextProduct.image_url) ? (
                    <img src={nextProduct.product_image || nextProduct.image_url} alt={nextProduct.name} loading="lazy" />
                  ) : (
                    <div className="placeholder-image">Нет изображения</div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </Link>
      <button className="product-showcase-arrow" onClick={e => { e.preventDefault(); nextProductHandler(); }} aria-label="Следующий предзаказ">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 25 25" className="product-showcase-arrow-icon"><path className="product-showcase-arrow-path" d="m17.5 5.999-.707.707 5.293 5.293H1v1h21.086l-5.294 5.295.707.707L24 12.499l-6.5-6.5z" data-name="Right"/></svg>
      </button>
      <div className="product-showcase-right">
        <div className="product-showcase-title">{product.name}</div>
        <div className="product-showcase-price">{product.price} ₽</div>
        <Link to={`/preorders/${product.id}`} className="product-showcase-preorder">Предзаказ</Link>
      </div>
      <div className={`product-showcase-anim-overlay${animating ? " anim" : ""}`}></div>
    </div>
  );
}