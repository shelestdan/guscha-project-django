import React from 'react';
import useScrollDirection from '../../../hooks/useScrollDirection';
import Logo from '../../Logo/Logo';
import BurgerMenu from '../../../BurgerMenu';
import { useCartStore } from '../../../store/cartStore';
import InstrumentCartIcon from '../../../assets/icons/instrument_x4fdrqsfczqn.svg';
import '../../../styles/Header.css';

// Специальный компонент иконки корзины для header
const HeaderCartIcon = ({ isDark = false }) => {
  const cartCount = useCartStore((state) => state.count);
  const toggleCart = useCartStore((state) => state.toggleCart);

  return (
    <button 
      className={`header-cart-icon ${isDark ? 'white-theme' : 'dark-theme'}`}
      onClick={toggleCart}
      aria-label="Открыть корзину"
    >
      <img 
        src={InstrumentCartIcon} 
        alt="Корзина" 
        width={24} 
        height={24}
        className={`header-cart-icon-filter ${isDark ? 'light' : 'dark'}`}
      />
      {cartCount > 0 && (
        <span className="header-cart-badge">
          {cartCount}
        </span>
      )}
    </button>
  );
};

const Header = ({ isHome }) => {
  const { scrollDirection, scrollPosition } = useScrollDirection();

  const isAtTop = scrollPosition < 100;
  const isScrollingDown = scrollDirection === 'down' && scrollPosition > 50;

  // Главная страница: одна шапка, меняем стили
  if (isHome) {
    // Цвет элементов
    const black = (!isAtTop && !isScrollingDown);
    const showMenuLabel = !isScrollingDown;
    const showLogo = !isScrollingDown;

    return (
      <header className={`header-container ${isScrollingDown ? 'header-hidden' : 'header-visible'}`}>
        {/* Белая подложка с анимацией opacity */}
        <div
          className="header-background-layer"
          style={{
            opacity: (!isAtTop && !isScrollingDown) ? 1 : 0,
            transition: 'opacity 0.4s cubic-bezier(0.4,0,0.2,1)'
          }}
        />
        <div className="header-content">
          <div className="header-left">
            <BurgerMenu black={black} menuLabelVisible={showMenuLabel} />
          </div>
          <div className="header-center"> 
            <Logo isVisible={showLogo} black={black} size={64} />
          </div>
          <div className="header-right">
            <HeaderCartIcon isDark={black} />
          </div>
        </div>
      </header>
    );
  }

  // Для остальных страниц — белая шапка
  const showMenuLabel = !isScrollingDown;
  
  return (
    <header className="header-container header-white header-visible">
      <div className="header-content">
        <div className="header-left">
          <BurgerMenu black={true} menuLabelVisible={showMenuLabel} />
        </div>
        <div className="header-center">
          <Logo isVisible={true} black={true} size={64} />
        </div>
        <div className="header-right">
          <HeaderCartIcon isDark={true} />
        </div>
      </div>
    </header>
  );
};

export default Header;