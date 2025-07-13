import React, { useEffect, useState } from 'react';
import useScrollDirection from './hooks/useScrollDirection';
import './styles/App.css';
import GuschaBack from './assets/images/Guscha_back.png'; // Оставляем как запасной вариант

// Стрелка для скролла с интегрированной логикой анимации
function ScrollDownArrow({ visible }) {
  const handleClick = () => {
    const el = document.getElementById('products');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  
  return (
    <button
      onClick={handleClick}
      className={`scroll-down-arrow ${visible ? 'visible' : 'hidden'}`}
      aria-label="Прокрутить к товарам"
    >
      <svg
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        width={48}
        height={48}
      >
        <path d="M16 8V24" stroke="#fff" strokeWidth="2.5" strokeLinecap="round"></path>
        <path d="M8 16L16 24L24 16" stroke="#fff" strokeWidth="2.5" strokeLinecap="round"></path>
      </svg>
    </button>
  );
}

const HeroSection = () => {
  const hookResult = useScrollDirection();
  const scrollPosition = hookResult.scrollPosition;
  const [backgrounds, setBackgrounds] = useState([]);
  const [currentBackgroundIndex, setCurrentBackgroundIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  
  // Логика анимации стрелки: показываем в самом верху, плавно скрываем при скролле
  const showArrow = scrollPosition < 150;
  
  // Загрузка активных фонов с сервера
  useEffect(() => {
    const fetchBackgrounds = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/public/active-background');
        if (!response.ok) {
          throw new Error('Не удалось загрузить фоны');
        }
        const data = await response.json();
        if (data.backgrounds && data.backgrounds.length > 0) {
          setBackgrounds(data.backgrounds);
        }
      } catch (error) {
        console.error('Ошибка при загрузке фонов:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchBackgrounds();
  }, []);
  
  // Если есть несколько активных фонов, меняем их каждые 5 секунд
  useEffect(() => {
    if (backgrounds.length <= 1) return;
    
    const interval = setInterval(() => {
      setCurrentBackgroundIndex((prevIndex) => 
        prevIndex === backgrounds.length - 1 ? 0 : prevIndex + 1
      );
    }, 5000);
    
    return () => clearInterval(interval);
  }, [backgrounds]);
  
  // Определяем текущий фон для отображения
  const currentBackground = backgrounds.length > 0 
    ? backgrounds[currentBackgroundIndex].file_url 
    : GuschaBack;
  
  // Определяем тип фона (изображение или видео)
  const isVideo = backgrounds.length > 0 && backgrounds[currentBackgroundIndex].file_type === 'video';
  
  return (
    <section 
      className="hero-section hero-section-main" 
      style={{
        marginTop: -96,
        ...(isVideo ? {} : { background: `url(${currentBackground}) center/cover no-repeat` })
      }}
    >
      {isVideo && (
        <video 
          autoPlay 
          muted 
          loop 
          playsInline
          className="hero-video-background"
        >
          <source src={currentBackground} type="video/mp4" />
          Ваш браузер не поддерживает видео.
        </video>
      )}
      <ScrollDownArrow visible={showArrow} />
    </section>
  );
}

export default HeroSection;