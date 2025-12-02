import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import FlowingMenu from '../components/FlowingMenu';
import ProductHeroBlock from '../components/ProductHeroBlock';
import '../styles/CollectionsPage.css';

const CollectionsPage = () => {
  const navigate = useNavigate();
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [heroPreorder, setHeroPreorder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCollections = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/collections/');
        if (!response.ok) {
          throw new Error('Ошибка загрузки коллекций');
        }
        const data = await response.json();
        const collectionsData = data.collections || data.results || data;
        setCollections(collectionsData);
        // Автоматически выбираем первую коллекцию
        if (collectionsData.length > 0) {
          setSelectedCollection(collectionsData[0]);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCollections();
  }, []);

  // Загрузка featured предзаказа для hero блока
  useEffect(() => {
    const fetchHeroPreorder = async () => {
      try {
        const response = await fetch('/api/products/preorders/?is_featured=true&is_active=true');
        if (response.ok) {
          const data = await response.json();
          const preorders = data.results || data;
          if (preorders.length > 0) {
            setHeroPreorder(preorders[0]);
          }
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

  const handleCollectionSelect = (collectionId) => {
    const collection = collections.find(c => c.id === collectionId);
    if (collection) {
      setSelectedCollection(collection);
    }
  };

  // Преобразуем коллекции в формат для FlowingMenu
  const menuItems = collections.map(collection => ({
    id: collection.id,
    text: collection.name,
    image: collection.primary_image?.url || collection.images?.[0]?.image || null
  }));

  if (loading) {
    return (
      <div className="collections-page">
        <div className="collections-loading">
          <div className="loading-spinner"></div>
          <p>Загрузка коллекций...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="collections-page">
        <div className="collections-error">
          <h2>Ошибка загрузки</h2>
          <p>{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="retry-button"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  if (collections.length === 0) {
    return (
      <div className="collections-page">
        <div className="collections-empty">
          <h2>Коллекции не найдены</h2>
          <p>Скоро здесь появятся новые коллекции</p>
        </div>
      </div>
    );
  }

  return (
    <div className="collections-page">
      {/* Hero блок с featured предзаказом */}
      {heroPreorder && (
        <ProductHeroBlock
          title={heroPreorder.name}
          price={heroPreorder.price}
          modelImage={heroPreorder.model_image}
          productImage={heroPreorder.product_image}
          onPreorder={handlePreorder}
          onNavigate={handleNavigateToProduct}
          productId={heroPreorder.id}
        />
      )}

      {/* FlowingMenu в центре */}
      <div className="collections-menu-section">
        <FlowingMenu 
          items={menuItems}
          onItemClick={handleCollectionSelect}
          activeId={selectedCollection?.id}
        />
      </div>

      {/* Контент выбранной коллекции под меню */}
      {selectedCollection && (
        <div className="collection-content-section">
          {selectedCollection.description && (
            <div className="collection-description">
              <div 
                className="description-content"
                dangerouslySetInnerHTML={{ __html: selectedCollection.description }}
              />
            </div>
          )}

          {selectedCollection.images && selectedCollection.images.length > 0 && (
            <div className="collection-gallery">
              {selectedCollection.images.map((image, index) => (
                <div key={image.id || index} className="gallery-item">
                  <img 
                    src={image.image || image.image_url} 
                    alt={image.alt_text || `${selectedCollection.name} ${index + 1}`}
                    loading="lazy"
                  />
                  {image.caption && (
                    <p className="image-caption">{image.caption}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CollectionsPage;
