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
    if (currentVideoIndex < videos.length - 1) {
      // Переходим к следующему видео
      setCurrentVideoIndex(prev => prev + 1);
    } else if (loop) {
      // Если включено зацикливание, начинаем сначала
      setCurrentVideoIndex(0);
    } else {
      // Плейлист завершен
      setIsPlaying(false);
    }
  }, [currentVideoIndex, videos.length, loop]);

  // Сброс индекса при изменении списка видео
  useEffect(() => {
    if (videos.length > 0 && currentVideoIndex >= videos.length) {
      setCurrentVideoIndex(0);
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
        url={currentVideo.platform === 'file' ? currentVideo.embed_url : (currentVideo.video_url || currentVideo.embed_url)}
        autoplay={isPlaying}
        muted={currentVideo.muted !== false}
        loop={false} // Отключаем loop для отдельного видео, управляем на уровне плейлиста
        onEnded={handleVideoEnded}
        onError={() => {
          // При ошибке пытаемся перейти к следующему видео
          handleVideoEnded();
        }}
        onReady={() => {
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