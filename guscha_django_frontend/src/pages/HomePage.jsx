import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import HeroSection from '../HeroSection';
import { ProductGrid } from '../components/features/products';
import ProductHeroBlock from '../components/ProductHeroBlock';
import BoxOfficeSection from '../components/BoxOfficeSection';

export default function HomePage() {
  const navigate = useNavigate();
  const [heroPreorder, setHeroPreorder] = useState(null);

  // Загрузка предзаказа для hero блока с AbortController для отмены при размонтировании
  useEffect(() => {
    const abortController = new AbortController();
    
    const fetchHeroPreorder = async () => {
      try {
        // Сначала пробуем получить featured предзаказ
        let response = await fetch('/api/products/preorders/?is_featured=true&is_active=true', {
          signal: abortController.signal
        });
        let data = await response.json();
        let preorders = data.results || data;
        
        // Если нет featured, берём первый активный
        if (!preorders || preorders.length === 0) {
          response = await fetch('/api/products/preorders/?is_active=true', {
            signal: abortController.signal
          });
          data = await response.json();
          preorders = data.results || data;
        }
        
        if (preorders && preorders.length > 0) {
          // Загружаем детальную информацию для получения product_images
          const detailResponse = await fetch(`/api/products/preorders/${preorders[0].id}/`, {
            signal: abortController.signal
          });
          const detailData = await detailResponse.json();
          setHeroPreorder(detailData);
        }
      } catch (err) {
        // Игнорируем ошибки отмены запроса
        if (err.name === 'AbortError') return;
      }
    };

    fetchHeroPreorder();
    
    return () => abortController.abort();
  }, []);

  // Мемоизированный callback для предзаказа
  const handlePreorder = useCallback(() => {
    if (heroPreorder) {
      navigate(`/preorders/${heroPreorder.id}`);
    }
  }, [heroPreorder, navigate]);

  // Мемоизированные изображения товаров - пересчитываются только при изменении heroPreorder
  const productImages = useMemo(() => {
    if (!heroPreorder) return [];
    const images = [];
    const modelImg = heroPreorder.model_image;
    
    // Берём из product_images только товарные изображения (не model)
    if (heroPreorder.product_images && Array.isArray(heroPreorder.product_images)) {
      heroPreorder.product_images.forEach(img => {
        // Пропускаем модельные и дубликаты с model_image
        if (img.image_type === 'model') return;
        if (img.image_url === modelImg) return;
        if (img.image_url && !images.includes(img.image_url)) {
          images.push(img.image_url);
        }
      });
    }
    
    // Fallback на product_image если массив пустой
    if (images.length === 0 && heroPreorder.product_image) {
      images.push(heroPreorder.product_image);
    }
    
    return images;
  }, [heroPreorder]);

  return (
    <>
      <HeroSection />
      <ProductHeroBlock
        title={heroPreorder?.name || 'КОЛЛЕКЦИЯ'}
        subtitle={heroPreorder?.subtitle || 'КАПСЕЛЬНАЯ КОЛЛЕКЦИЯ'}
        description={heroPreorder?.short_description || heroPreorder?.description || ''}
        modelImage={heroPreorder?.model_image || heroPreorder?.image_url || ''}
        productImages={productImages}
        onPreorder={handlePreorder}
        productId={heroPreorder?.id}
      />
      <div className="homepage-divider" />
      <div id="products">
        <ProductGrid />
      </div>
      <BoxOfficeSection />
    </>
  );
}