import React, { useState, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useCartStore } from '../../../store/cartStore';
import InstrumentCartIcon from '../../../assets/icons/instrument_x4fdrqsfczqn.svg';

const HeaderCartIcon = ({ isDark = false }) => {
  const [iconTop, setIconTop] = useState('28px');
  const [iconRight, setIconRight] = useState('24px');
  
  const cartCount = useCartStore((state) => state.count);
  const toggleCart = useCartStore((state) => state.toggleCart);
  const isCartOpen = useCartStore((state) => state.isOpen);

  // Функция для обновления позиции иконки корзины
  const updateIconPos = useCallback(() => {
    const header = document.querySelector('.header-container');
    // Не пересчитываем позицию если хедер скрыт или анимируется
    if (header && (header.classList.contains('header-hidden') || 
        getComputedStyle(header).transform !== 'none')) {
      return;
    }
    
    const headerRight = document.querySelector('.header-right');
    if (headerRight) {
      const rect = headerRight.getBoundingClientRect();
      const iconHeight = 40;
      const top = rect.top + rect.height / 2 - iconHeight / 2;
      const right = window.innerWidth - rect.right + 8;
      setIconTop(`${Math.max(top, 8)}px`);
      setIconRight(`${Math.max(right, 8)}px`);
    } else {
      setIconTop('28px');
      setIconRight('24px');
    }
  }, []);

  // Отслеживание изменений позиции и состояния хедера
  useEffect(() => {
    updateIconPos();
    window.addEventListener('resize', updateIconPos);
    window.addEventListener('scroll', updateIconPos);

    const header = document.querySelector('.header-container');
    let observer = null;
    let debounceTimer = null;
    
    if (header && typeof MutationObserver !== 'undefined') {
      observer = new MutationObserver((mutations) => {
        // Проверяем, что изменились именно классы видимости
        const hasVisibilityChange = mutations.some(mutation => {
          const target = mutation.target;
          return target.classList.contains('header-visible') && 
                 !target.classList.contains('header-hidden');
        });
        
        if (hasVisibilityChange) {
          // Debounce для предотвращения множественных вызовов во время анимации
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(updateIconPos, 100);
        }
      });
      observer.observe(header, { attributes: true, attributeFilter: ['class'] });
    }

    return () => {
      window.removeEventListener('resize', updateIconPos);
      window.removeEventListener('scroll', updateIconPos);
      if (observer) observer.disconnect();
      if (debounceTimer) clearTimeout(debounceTimer);
    };
  }, [updateIconPos]);

  // Portal контент: фиксированная иконка корзины
  const portalContent = (
    <div className="cart-portal-root" aria-hidden="false">
      <button
        className={`header-cart-icon portal ${isDark ? 'white-theme' : 'dark-theme'}`}
        onClick={toggleCart}
        aria-label="Открыть корзину"
        style={{
          position: 'fixed',
          top: iconTop,
          right: iconRight,
          zIndex: 3001,
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          pointerEvents: 'auto',
          opacity: isCartOpen ? 0 : 1,
          visibility: isCartOpen ? 'hidden' : 'visible'
        }}
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
    </div>
  );

  // Render placeholder в хедере (сохраняет layout) и portal контент в body
  return (
    <>
      <div
        className="cart-icon-placeholder"
        aria-hidden="true"
        style={{
          width: 64,
          height: 40,
          opacity: isCartOpen ? 0 : 1,
          visibility: isCartOpen ? 'hidden' : 'visible',
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
        }}
      />
      {typeof document !== 'undefined' && document.body
        ? createPortal(portalContent, document.body)
        : portalContent}
    </>
  );
};

export default HeaderCartIcon;