import { useState, useEffect, useMemo, useCallback } from 'react';
import FlowingMenu from '../components/FlowingMenu';
import Masonry from '../components/Masonry';
import SplitText from '../components/SplitText';
import '../styles/CollectionsPage.css';

// Вынесено за компонент — не пересоздаётся при рендере
const heights = [300, 350, 400, 450, 500, 550, 600, 650, 700];

const generateHeight = (id, index) => {
  const hash = String(id || index).split('').reduce((acc, char) => {
    return char.charCodeAt(0) + ((acc << 5) - acc);
  }, 0);
  return heights[Math.abs(hash) % heights.length];
};

const CollectionsPage = () => {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    
    const fetchCollections = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/collections/', {
          signal: controller.signal
        });
        if (!response.ok) {
          throw new Error('Ошибка загрузки коллекций');
        }
        const data = await response.json();
        const collectionsData = data.collections || data.results || data;
        setCollections(collectionsData);
        if (collectionsData.length > 0) {
          setSelectedCollection(collectionsData[0]);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchCollections();
    
    return () => controller.abort();
  }, []);

  const handleCollectionSelect = useCallback((collectionId) => {
    setSelectedCollection(prev => {
      if (prev?.id === collectionId) return prev;
      return collections.find(c => c.id === collectionId) || prev;
    });
  }, [collections]);

  const menuItems = useMemo(() => 
    collections.map(collection => ({
      id: collection.id,
      text: collection.name,
      image: collection.primary_image?.url || collection.images?.[0]?.image || null
    })),
    [collections]
  );

  const masonryItems = useMemo(() => {
    if (!selectedCollection?.images) return [];
    return selectedCollection.images.map((image, index) => ({
      id: image.id?.toString() || `img-${index}`,
      img: image.image || image.image_url,
      url: image.image || image.image_url,
      height: generateHeight(image.id, index),
      caption: image.caption || image.alt_text || null
    }));
  }, [selectedCollection?.images]);

  const descriptionText = useMemo(() => 
    selectedCollection?.description?.replace(/<[^>]*>/g, '') || '',
    [selectedCollection?.description]
  );

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
      <div className="collections-menu-section">
        <FlowingMenu 
          items={menuItems}
          onItemClick={handleCollectionSelect}
          activeId={selectedCollection?.id}
        />
      </div>

      {selectedCollection && (
        <div className="collection-content-section">
          <div className="collection-content-wrapper">
            {descriptionText && (
              <div className="collection-description">
                <SplitText
                  key={selectedCollection.id}
                  text={descriptionText}
                  splitBy="word"
                  animateFrom="bottom"
                  duration={0.4}
                  stagger={0.015}
                  delay={0.2}
                  className="description-text"
                  animationKey={selectedCollection.id}
                />
              </div>
            )}

            {masonryItems.length > 0 && (
              <div className="collection-gallery">
                <Masonry
                  items={masonryItems}
                  ease="power3.out"
                  duration={0.6}
                  stagger={0.05}
                  animateFrom="bottom"
                  scaleOnHover={true}
                  hoverScale={0.95}
                  blurToFocus={true}
                  colorShiftOnHover={false}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CollectionsPage;
