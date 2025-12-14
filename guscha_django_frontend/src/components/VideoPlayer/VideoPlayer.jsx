import React from 'react';
import ReactPlayer from 'react-player';
import './VideoPlayer.css';

const VideoPlayer = ({
  url,
  autoplay = false,
  muted = false,
  loop = false,
  onEnded = null,
  className = '',
  ...props
}) => {
  const playerConfig = {
    youtube: {
      playerVars: {
        controls: 0,
        showinfo: 0,
        rel: 0,
        modestbranding: 1,
        iv_load_policy: 3,
        disablekb: 1,
        fs: 0,
        playsinline: 1,
        autoplay: autoplay ? 1 : 0,
        mute: muted ? 1 : 0,
        loop: loop ? 1 : 0,
        origin: window.location.origin
      },
      embedOptions: {
        host: 'https://www.youtube-nocookie.com'
      }
    },
    vimeo: {
      playerOptions: {
        controls: false,
        autoplay: autoplay,
        muted: muted,
        loop: loop,
        background: true
      }
    },
    file: {
      attributes: {
        controlsList: 'nodownload nofullscreen noremoteplayback',
        disablePictureInPicture: true
      }
    }
  };

  console.log('🎥 VideoPlayer rendering with URL:', url);

  return (
    <div className={`video-player-container ${className}`}>
      <ReactPlayer
        url={url}
        playing={autoplay}
        muted={muted}
        loop={loop}
        width="100%"
        height="100%"
        config={playerConfig}
        onEnded={onEnded}
        onError={(error) => {
          console.error('❌ Ошибка воспроизведения видео:', error);
        }}
        onReady={() => {
          console.log('✅ Видео готово к воспроизведению');
        }}
        {...props}
      />
      {/* Защитный слой для предотвращения взаимодействия */}
      <div className="video-protection-layer" />
    </div>
  );
};

export default VideoPlayer;
