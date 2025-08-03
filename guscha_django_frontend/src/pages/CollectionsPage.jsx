import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/CollectionsPage.css';

const CollectionsPage = () => {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
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

  if (loading) {
    return (
      <div className="collections-page">
        <div className="collections-layout">
          <div className="collections-sidebar">
            <div className="loading-spinner"></div>
            <p>Загрузка...</p>
          </div>
          <div className="collections-main">
            <div className="loading-state">
              <p>Загрузка коллекций...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="collections-page">
        <div className="collections-layout">
          <div className="collections-sidebar">
            <h3>Коллекции</h3>
            <p>Ошибка загрузки</p>
          </div>
          <div className="collections-main">
            <div className="error-state">
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
        </div>
      </div>
    );
  }

  return (
    <div className="collections-page">
      <div className="collections-layout">
        {/* Левая панель со списком коллекций */}
        <div className="collections-sidebar">
          <h3>Коллекции</h3>
          {collections.length === 0 ? (
            <p>Коллекции не найдены</p>
          ) : (
            <div className="collections-list">
              {collections.map((collection) => (
                <div 
                  key={collection.id} 
                  className={`collection-item ${
                    selectedCollection?.id === collection.id ? 'active' : ''
                  }`}
                  onClick={() => setSelectedCollection(collection)}
                >
                  <span className="collection-name">{collection.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Основная область для отображения коллекции */}
        <div className="collections-main">
          {selectedCollection ? (
            <div className="collection-display">
              <div className="collection-header">
                <h1>{selectedCollection.name}</h1>
                {selectedCollection.short_description && (
                  <p className="collection-subtitle">{selectedCollection.short_description}</p>
                )}
              </div>
              
              <div className="collection-content-area">
                {selectedCollection.description && (
                  <div className="collection-description">
                    <h3>Описание коллекции</h3>
                    <div 
                      className="description-content"
                      dangerouslySetInnerHTML={{ __html: selectedCollection.description }}
                    />
                  </div>
                )}
                
                {/* Показываем все изображения коллекции */}
                 {selectedCollection.images && selectedCollection.images.length > 0 ? (
                   <div className="collection-images-gallery">
                     <div className="images-grid">
                      {selectedCollection.images.map((image, index) => (
                        <div key={image.id} className="image-item">
                          <img 
                            src={image.image} 
                            alt={image.alt_text || `${selectedCollection.name} ${index + 1}`}
                          />
                          {image.caption && (
                            <p className="image-caption">{image.caption}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : selectedCollection.primary_image ? (
                  <div className="collection-main-image">
                    <img 
                      src={selectedCollection.primary_image.url} 
                      alt={selectedCollection.primary_image.alt || selectedCollection.name}
                    />
                  </div>
                ) : (
                  <div className="collection-placeholder-main">
                    <div className="placeholder-content">
                      <h2>ФОТО КОЛЛЕКЦИИ</h2>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="no-collection-selected">
              <h2>Выберите коллекцию</h2>
              <p>Выберите коллекцию из списка слева для просмотра</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CollectionsPage;