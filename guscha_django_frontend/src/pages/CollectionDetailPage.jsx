import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import '../styles/CollectionDetailPage.css';

const CollectionDetailPage = () => {
  const { slug } = useParams();
  const [collection, setCollection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);

  useEffect(() => {
    const fetchCollection = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/collections/${slug}/`);
        if (!response.ok) {
          throw new Error('Коллекция не найдена');
        }
        const data = await response.json();
        setCollection(data);
        // Устанавливаем первое изображение как выбранное
        if (data.images && data.images.length > 0) {
          setSelectedImage(data.images[0]);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCollection();
  }, [slug]);

  if (loading) {
    return (
      <div className="collection-detail-page">
        <div className="container">
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Загрузка коллекции...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="collection-detail-page">
        <div className="container">
          <div className="error-state">
            <h2>Ошибка загрузки</h2>
            <p>{error}</p>
            <Link to="/collections" className="back-button">
              ← Вернуться к коллекциям
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!collection) {
    return (
      <div className="collection-detail-page">
        <div className="container">
          <div className="error-state">
            <h2>Коллекция не найдена</h2>
            <Link to="/collections" className="back-button">
              ← Вернуться к коллекциям
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="collection-detail-page">
      <div className="container">
        {/* Навигация */}
        <nav className="breadcrumb">
          <Link to="/collections">Коллекции</Link>
          <span className="separator">→</span>
          <span className="current">{collection.name}</span>
        </nav>

        {/* Заголовок коллекции */}
        <header className="collection-header">
          <div className="collection-title-section">
            <h1 className="collection-title">
              {collection.name}
              {collection.is_featured && (
                <span className="featured-badge">★ Рекомендуемое</span>
              )}
            </h1>
            {collection.short_description && (
              <p className="collection-subtitle">{collection.short_description}</p>
            )}
          </div>
        </header>

        {/* Основной контент */}
        <div className="collection-content">
          {/* Описание коллекции */}
          {collection.description && (
            <div className="collection-description">
              <h2>Описание</h2>
              <div 
                className="description-content"
                dangerouslySetInnerHTML={{ __html: collection.description }}
              />
            </div>
          )}

          {/* Галерея изображений */}
          {collection.images && collection.images.length > 0 ? (
            <div className="collection-gallery">
              {/* Главное изображение */}
              <div className="main-image-container">
                {selectedImage && (
                  <img 
                    src={selectedImage.image} 
                    alt={selectedImage.alt_text || collection.name}
                    className="main-image"
                  />
                )}
              </div>

              {/* Миниатюры */}
              {collection.images.length > 1 && (
                <div className="thumbnails-container">
                  <div className="thumbnails-grid">
                    {collection.images.map((image, index) => (
                      <button
                        key={image.id}
                        className={`thumbnail ${selectedImage?.id === image.id ? 'active' : ''}`}
                        onClick={() => setSelectedImage(image)}
                      >
                        <img 
                          src={image.thumbnail || image.image} 
                          alt={image.alt_text || `${collection.name} ${index + 1}`}
                        />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Показать все изображения в виде сетки, если их больше одного */}
              {collection.images.length > 1 && (
                <div className="all-images-grid">
                  <h3>Все изображения коллекции</h3>
                  <div className="images-grid">
                    {collection.images.map((image, index) => (
                      <div key={image.id} className="grid-image-container">
                        <img 
                          src={image.image} 
                          alt={image.alt_text || `${collection.name} ${index + 1}`}
                          className="grid-image"
                          onClick={() => setSelectedImage(image)}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="no-images">
              <p>В этой коллекции пока нет изображений</p>
            </div>
          )}

          {/* Информация о коллекции */}
          <div className="collection-info">
            <div className="info-item">
              <span className="info-label">Количество изображений:</span>
              <span className="info-value">{collection.images?.length || 0}</span>
            </div>
            {collection.created_at && (
              <div className="info-item">
                <span className="info-label">Создано:</span>
                <span className="info-value">
                  {new Date(collection.created_at).toLocaleDateString('ru-RU')}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Кнопка возврата */}
        <div className="collection-actions">
          <Link to="/collections" className="back-button">
            ← Вернуться к коллекциям
          </Link>
        </div>
      </div>
    </div>
  );
};

export default CollectionDetailPage;