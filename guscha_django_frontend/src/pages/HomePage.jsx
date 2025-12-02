import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import HeroSection from '../HeroSection';
import { ProductGrid } from '../components/features/products';
import ProductHeroBlock from '../components/ProductHeroBlock';
import BoxOfficeSection from '../components/BoxOfficeSection';

export default function HomePage() {
  const navigate = useNavigate();
  const [heroPreorder, setHeroPreorder] = useState(null);

  // Загрузка предзаказа для hero блока
  useEffect(() => {
    const fetchHeroPreorder = async () => {
      try {
        // Сначала пробуем получить featured предзаказ
        let response = await fetch('/api/products/preorders/?is_featured=true&is_active=true');
        let data = await response.json();
        let preorders = data.results || data;
        
        // Если нет featured, берём первый активный
        if (!preorders || preorders.length === 0) {
          response = await fetch('/api/products/preorders/?is_active=true');
          data = await response.json();
          preorders = data.results || data;
        }
        
        if (preorders && preorders.length > 0) {
          console.log('Hero preorder loaded:', preorders[0]);
          setHeroPreorder(preorders[0]);
        } else {
          console.log('No preorders found');
        }
      } catch (err) {
        console.error('Ошибка загрузки hero предзаказа:', err);
      }
    };

    fetchHeroPreorder();
  }, []);

  const handlePreorder = () => {
    if (heroPreorder) {
      navigate(`/preorders/${heroPreorder.id}`);
    }
  };

  const handleNavigateToProduct = () => {
    if (heroPreorder) {
      navigate(`/preorders/${heroPreorder.id}`);
    }
  };

  return (
    <>
      <HeroSection />
      <ProductHeroBlock
        title={heroPreorder?.name || 'ДЖИНСЫ'}
        price={heroPreorder?.price || 7900}
        modelImage={heroPreorder?.model_image || heroPreorder?.image_url || ''}
        productImage={heroPreorder?.product_image || heroPreorder?.image_url || ''}
        description={heroPreorder?.description || heroPreorder?.short_description || ''}
        onPreorder={handlePreorder}
        onNavigate={handleNavigateToProduct}
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