import React, { useEffect } from 'react';
import useScrollDirection from '../../../hooks/useScrollDirection';
import Logo from '../../Logo/Logo';
import BurgerMenu from '../../../BurgerMenu';
import HeaderCartIcon from './HeaderCartIcon';
import { useCartStore } from '../../../store/cartStore';
import '../../../styles/Header.css';
import './HeaderCartIcon.css';

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



  // Главная страница: одна шапка, меняем стили
  if (isHome) {
    // НЕ делаем элементы "чёрными" когда открыто меню или корзина — это причина появления чёрного логотипа/иконки
    const black = !isAtTop && !isScrollingDown && !isBurgerMenuOpen && !cartIsOpen;
    const showMenuLabel = !isScrollingDown;
    // Скрываем логотип в хедере когда в самом верху (там есть RAVIX в hero)
    const showLogo = !isScrollingDown && !isAtTop;

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
            <Logo isVisible={showLogo} black={black} size={128} />
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
          <Logo isVisible={true} black={true} size={128} />
        </div>
        <div className="header-right">
          <HeaderCartIcon isDark={true} />
        </div>
      </div>
    </header>
  );
};

export default Header;
