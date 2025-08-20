import React, { useEffect } from 'react';
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
      {cartCount > 0 && <span className="header-cart-badge">{cartCount}</span>}
    </button>
  );
};

const Header = ({ isHome, isBurgerMenuOpen, setIsBurgerMenuOpen, mainRef }) => {
  // Получаем направление и позицию скролла (слушаем mainRef если передан)
  const { scrollDirection, scrollPosition } = useScrollDirection(mainRef);

  // Состояние корзины — запрет скрытия хедера, если корзина открыта
  const cartIsOpen = useCartStore((state) => state.isOpen);

  const isAtTop = scrollPosition < 100;
  // Разрешаем скрытие шапки только если оба панели (бургер и корзина) закрыты
  const canHide = !isBurgerMenuOpen && !cartIsOpen;
  // Уменьшил порог до 10px, чтобы анимация начиналась сразу при небольшой прокрутке
  const isScrollingDown = canHide && scrollDirection === 'down' && scrollPosition > 10;

  // Логи для диагностики: они видны в DevTools -> Console
  useEffect(() => {
    console.log('[Header] scrollDirection:', scrollDirection, 'scrollPosition:', scrollPosition);
  }, [scrollDirection, scrollPosition]);

  useEffect(() => {
    console.log(
      '[Header] isScrollingDown:',
      isScrollingDown,
      'isAtTop:',
      isAtTop,
      'isBurgerMenuOpen:',
      isBurgerMenuOpen,
      'cartIsOpen:',
      cartIsOpen
    );
  }, [isScrollingDown, isAtTop, isBurgerMenuOpen, cartIsOpen]);

  // Главная страница: одна шапка, меняем стили
  if (isHome) {
    // НЕ делаем элементы "чёрными" когда открыто меню или корзина — это причина появления чёрного логотипа/иконки
    const black = !isAtTop && !isScrollingDown && !isBurgerMenuOpen && !cartIsOpen;
    const showMenuLabel = !isScrollingDown;
    const showLogo = !isScrollingDown;

    return (
      <header
        className={`header-container ${isScrollingDown ? 'header-hidden' : 'header-visible'}`}
      >
        <div
          className="header-background-layer"
          style={{
            opacity: !isAtTop && !isScrollingDown && !isBurgerMenuOpen && !cartIsOpen ? 1 : 0,
            transition: 'opacity 0.4s cubic-bezier(0.4,0,0.2,1)',
          }}
        />
        <div className="header-content">
          <div className="header-left">
            <BurgerMenu
              black={black}
              menuLabelVisible={showMenuLabel}
              isOpen={isBurgerMenuOpen}
              setIsOpen={setIsBurgerMenuOpen}
            />
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

  const showMenuLabel = !isScrollingDown;

  return (
    <header className="header-container header-white header-visible">
      <div className="header-content">
        <div className="header-left">
          <BurgerMenu
            black={true}
            menuLabelVisible={showMenuLabel}
            isOpen={isBurgerMenuOpen}
            setIsOpen={setIsBurgerMenuOpen}
          />
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
