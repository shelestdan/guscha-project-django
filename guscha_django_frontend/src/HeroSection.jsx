import React from 'react';
import useScrollDirection from './hooks/useScrollDirection';
import BackgroundContent from './components/BackgroundContent/BackgroundContent';
import './styles/App.css';

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
  
  // Логика анимации стрелки: показываем в самом верху, плавно скрываем при скролле
  const showArrow = scrollPosition < 150;
  
  return (
    <section 
      className="hero-section hero-section-main" 
      style={{
        marginTop: -96,
        position: 'relative'
      }}
    >
      <BackgroundContent />
      <ScrollDownArrow visible={showArrow} />
    </section>
  );
}

export default HeroSection;