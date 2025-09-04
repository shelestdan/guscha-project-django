import React, { useState, useEffect, useCallback } from 'react';
import backgroundApi from '../../api/backgroundApi';
import VideoPlayer from '../VideoPlayer';
import VideoPlaylist from '../VideoPlaylist';
import './BackgroundContent.css';

const BackgroundContent = () => {
  const [backgroundData, setBackgroundData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [healthStatus, setHealthStatus] = useState('unknown');
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  const MAX_RETRY_ATTEMPTS = 3;
  const RETRY_DELAY = 2000;

  useEffect(() => {
    loadActiveBackground();
  }, []);

  const loadActiveBackground = useCallback(async (isRetry = false) => {
    try {
      if (!isRetry) {
        setLoading(true);
        setError(null);
        setHealthStatus('checking');
      } else {
        setIsRetrying(true);
      }
      
      console.log(`🔄 Загрузка фонового контента (попытка ${retryCount + 1}/${MAX_RETRY_ATTEMPTS + 1})`);
      const response = await backgroundApi.getActiveBackground();
      
      // Валидация полученных данных
      if (!response) {
        throw new Error('Получены пустые данные от сервера');
      }
      
      if (!response.success || !response.data) {
        throw new Error('Некорректная структура ответа сервера');
      }
      
      const data = response.data;
      
      if (!data.content_type) {
        throw new Error('Отсутствует тип контента в ответе сервера');
      }
      
      // Проверка целостности данных в зависимости от типа контента
      switch (data.content_type) {
        case 'image':
          if (!data.image_url) {
            throw new Error('Отсутствует URL изображения');
          }
          break;
        case 'slideshow':
          if (!data.images?.length) {
            throw new Error('Слайдшоу не содержит изображений');
          }
          // Проверяем, что у каждого изображения есть URL
          const invalidImages = data.images.filter(img => !img.image_url);
          if (invalidImages.length > 0) {
            throw new Error(`Найдены изображения без URL: ${invalidImages.length} из ${data.images.length}`);
          }
          // Сортируем изображения: основное изображение первым, затем по порядку
          data.images.sort((a, b) => {
            if (a.is_primary && !b.is_primary) return -1;
            if (!a.is_primary && b.is_primary) return 1;
            return (a.order || 0) - (b.order || 0);
          });
          break;
        case 'video':
          if (!data.video_url && !data.embed_url) {
            throw new Error('Отсутствует URL видео');
          }
          break;
        default:
          throw new Error(`Неизвестный тип контента: ${data.content_type}`);
      }
      
      setBackgroundData(data);
      setError(null);
      setRetryCount(0);
      setHealthStatus('healthy');
      console.log('✅ Фоновый контент успешно загружен');
      
    } catch (err) {
      console.error('❌ Ошибка загрузки фонового контента:', err);
      
      const errorMessage = err.response?.data?.error || err.message || 'Неизвестная ошибка';
      const statusCode = err.response?.status;
      
      let detailedError = `Ошибка загрузки: ${errorMessage}`;
      if (statusCode) {
        detailedError += ` (HTTP ${statusCode})`;
      }
      
      setHealthStatus('unhealthy');
      
      // Автоматический retry при определенных ошибках
      if (retryCount < MAX_RETRY_ATTEMPTS && shouldRetry(err)) {
        console.log(`🔄 Повторная попытка через ${RETRY_DELAY}ms...`);
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          loadActiveBackground(true);
        }, RETRY_DELAY);
        return;
      }
      
      setError(detailedError);
      
    } finally {
      setLoading(false);
      setIsRetrying(false);
    }
  }, [retryCount]);
  
  // Определяет, стоит ли повторять запрос при данной ошибке
  const shouldRetry = (error) => {
    const status = error.response?.status;
    // Повторяем при сетевых ошибках, таймаутах и серверных ошибках 5xx
    return !status || status >= 500 || status === 408 || status === 429;
  };
  
  // Ручной retry
  const handleRetry = () => {
    setRetryCount(0);
    loadActiveBackground();
  };

  // Функция плавного переключения слайдов
  const switchToNextSlide = useCallback(() => {
    if (!backgroundData?.images?.length) return;
    
    setIsTransitioning(true);
    
    // Через 300ms (время затухания) переключаем слайд
    setTimeout(() => {
      setCurrentSlideIndex(
        (currentIndex) => (currentIndex + 1) % backgroundData.images.length
      );
      setIsTransitioning(false);
    }, 300);
  }, [backgroundData?.images?.length]);

  // Автоматическое переключение слайдов для слайдшоу
  useEffect(() => {
    if (backgroundData?.content_type === 'slideshow' && backgroundData?.images?.length > 1) {
      const interval = setInterval(() => {
        switchToNextSlide();
      }, backgroundData.interval || 5000); // используем interval из API, а не transition_duration

      return () => clearInterval(interval);
    }
  }, [backgroundData, switchToNextSlide]);

  const renderBackgroundContent = () => {
    if (!backgroundData) return null;

    switch (backgroundData.content_type) {
      case 'image':
        return (
          <div className="background-image">
            <img 
              src={backgroundData.image_url} 
              alt="Фоновое изображение"
              className="background-img"
              onError={(e) => {
                console.error('❌ Ошибка загрузки изображения:', e.target.src);
                setError('Не удалось загрузить изображение');
              }}
              onLoad={() => console.log('✅ Изображение успешно загружено')}
            />
          </div>
        );

      case 'slideshow':
        if (!backgroundData.images?.length) return null;
        
        const currentImage = backgroundData.images[currentSlideIndex];
        return (
          <div className="background-slideshow">
            <img 
              src={currentImage.image_url} 
              alt={currentImage.alt_text || "Слайд фонового изображения"}
              className={`background-img slideshow-img ${currentImage.is_primary ? 'primary-image' : ''} ${isTransitioning ? 'fading-out' : ''}`}
              onError={(e) => {
                console.error('❌ Ошибка загрузки слайда:', e.target.src);
                // Переключаемся на следующий слайд при ошибке
                if (backgroundData.images.length > 1) {
          setCurrentSlideIndex(prev => (prev + 1) % backgroundData.images.length);
                }
              }}
              onLoad={() => console.log(`✅ Слайд ${currentSlideIndex + 1} загружен`)}
            />

          </div>
        );

      case 'video':
        // Проверяем, есть ли плейлист видео
        if (backgroundData.playlist && Array.isArray(backgroundData.playlist) && backgroundData.playlist.length > 1) {
          console.log(`🎵 Обнаружен плейлист из ${backgroundData.playlist.length} видео`);
          return (
            <div className="background-video">
              <VideoPlaylist
                videos={backgroundData.playlist}
                autoplay={backgroundData.autoplay !== false}
                muted={backgroundData.muted !== false}
                loop={backgroundData.loop !== false}
                className="background-video-player"
                onError={() => {
                  console.error('❌ Ошибка воспроизведения плейлиста');
                  setError('Не удалось воспроизвести плейлист видео');
                }}
              />
            </div>
          );
        } else {
          // Одиночное видео
          console.log('🎬 Воспроизведение одиночного видео');
          return (
            <div className="background-video">
              <VideoPlayer
                url={backgroundData.video_type === 'file' ? backgroundData.video_url : backgroundData.embed_url}
                autoplay={backgroundData.autoplay !== false}
                muted={backgroundData.muted !== false}
                loop={backgroundData.loop !== false}
                className="background-video-player"
                onError={() => {
                  console.error('❌ Ошибка воспроизведения видео:', backgroundData.video_url);
                  setError('Не удалось воспроизвести видео');
                }}
              />
            </div>
          );
        }

      default:
        return null;
    }
  };

  if (loading) {
    return null; // Скрываем экран загрузки от пользователя
  }

  if (error) {
    return (
      <div className="background-content error">
        <div className="error-container">
          <div className="error-message">{error}</div>
          <div className="error-details">
            <p>Статус системы: <span className={`health-status ${healthStatus}`}>{healthStatus}</span></p>
            {retryCount > 0 && <p>Попыток повтора: {retryCount}/{MAX_RETRY_ATTEMPTS}</p>}
          </div>
          <div className="error-actions">
            <button 
              onClick={handleRetry} 
              disabled={isRetrying}
              className="retry-button"
            >
              {isRetrying ? 'Повтор...' : 'Повторить'}
            </button>
          </div>
        </div>
        {/* Fallback контент */}
        <div className="fallback-background">
          <div className="fallback-pattern"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="background-content">
      {renderBackgroundContent()}
      {backgroundData && backgroundData.description && (
        <div className="background-overlay">
          <div className="background-info">
            <p className="background-description">{backgroundData.description}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default BackgroundContent;