import React, { useState, useEffect, useCallback } from 'react';
import VideoPlayer from '../VideoPlayer';
import './VideoPlaylist.css';

const VideoPlaylist = ({ 
  videos = [], 
  autoplay = false, 
  muted = false, 
  loop = false,
  className = '',
  ...props 
}) => {
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoplay);

  // Получаем текущее видео
  const currentVideo = videos[currentVideoIndex];

  // Обработчик завершения видео
  const handleVideoEnded = useCallback(() => {
    console.log(`✅ Видео ${currentVideoIndex + 1} завершено`);
    
    if (currentVideoIndex < videos.length - 1) {
      // Переходим к следующему видео
      setCurrentVideoIndex(prev => prev + 1);
      console.log(`🎬 Переключение на видео ${currentVideoIndex + 2}`);
    } else if (loop) {
      // Если включено зацикливание, начинаем сначала
      setCurrentVideoIndex(0);
      console.log('🔄 Плейлист завершен, начинаем сначала');
    } else {
      // Плейлист завершен
      setIsPlaying(false);
      console.log('🏁 Плейлист завершен');
    }
  }, [currentVideoIndex, videos.length, loop]);

  // Сброс индекса при изменении списка видео
  useEffect(() => {
    if (videos.length > 0 && currentVideoIndex >= videos.length) {
      setCurrentVideoIndex(0);
    }
  }, [videos, currentVideoIndex]);

  // Логирование изменений плейлиста
  useEffect(() => {
    if (videos.length > 0) {
      console.log(`🎵 Плейлист загружен: ${videos.length} видео`);
      console.log(`▶️ Текущее видео: ${currentVideoIndex + 1}/${videos.length}`);
    }
  }, [videos, currentVideoIndex]);

  if (!videos || videos.length === 0) {
    return (
      <div className={`video-playlist-container empty ${className}`}>
        <div className="no-videos-message">
          <p>Нет доступных видео для воспроизведения</p>
        </div>
      </div>
    );
  }

  if (!currentVideo) {
    return (
      <div className={`video-playlist-container error ${className}`}>
        <div className="video-error-message">
          <p>Ошибка загрузки видео</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`video-playlist-container ${className}`}>
      <VideoPlayer
        url={currentVideo.video_type === 'file' ? currentVideo.video_url : currentVideo.embed_url}
        autoplay={isPlaying}
        muted={currentVideo.muted !== false}
        loop={false} // Отключаем loop для отдельного видео, управляем на уровне плейлиста
        onEnded={handleVideoEnded}
        onError={(error) => {
          console.error(`❌ Ошибка воспроизведения видео ${currentVideoIndex + 1}:`, error);
          // При ошибке пытаемся перейти к следующему видео
          handleVideoEnded();
        }}
        onReady={() => {
          console.log(`✅ Видео ${currentVideoIndex + 1} готово к воспроизведению`);
          setIsPlaying(autoplay);
        }}
        {...props}
      />
      
      {/* Индикатор плейлиста */}
      {videos.length > 1 && (
        <div className="playlist-indicator">
          <span className="playlist-counter">
            {currentVideoIndex + 1} / {videos.length}
          </span>
          <div className="playlist-progress">
            <div 
              className="playlist-progress-bar"
              style={{ width: `${((currentVideoIndex + 1) / videos.length) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoPlaylist;