import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import DetailPage from './DetailPage';

const ProductDetailPage = () => {
  const { slug } = useParams();
  const [product, setProduct] = useState(null);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    const abortController = new AbortController();
    
    const fetchProduct = async () => {
      setStatus('loading');
      try {
        const response = await fetch(`/api/products/products/${slug}/`, {
          signal: abortController.signal,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        });
        if (!response.ok) throw new Error('Product not found');
        const data = await response.json();
        setProduct(data.product || data);
        setStatus('success');
      } catch (error) {
        if (error.name === 'AbortError') return;
        setStatus('error');
      }
    };
    fetchProduct();
    
    return () => abortController.abort();
  }, [slug]);

  if (status === 'loading') return <div className="pdp-status">Loading...</div>;
  if (status === 'error') return <div className="pdp-status">Product not found.</div>;

  return <DetailPage item={product} itemType="product" />;
};

export default ProductDetailPage;