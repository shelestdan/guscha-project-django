import { useState, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { createPortal } from 'react-dom';
import './styles/BurgerMenu.css';

const BurgerMenu = ({
  black = false,
  menuLabelVisible = true,
  isOpen: isOpenProp,
  setIsOpen: setIsOpenProp,
}) => {
  const [internalOpen, setInternalOpen] = useState(false);
  const [btnTop, setBtnTop] = useState('28px');
  const [btnLeft, setBtnLeft] = useState('24px');

  const isControlled = typeof isOpenProp === 'boolean' && typeof setIsOpenProp === 'function';
  const isOpen = typeof isOpenProp === 'boolean' ? isOpenProp : internalOpen;

  const toggleMenu = useCallback(() => {
    if (isControlled) {
      setIsOpenProp((prev) => !prev);
    } else {
      setInternalOpen((prev) => !prev);
    }
  }, [isControlled, setIsOpenProp]);

  const closeMenu = useCallback(() => {
    if (isControlled) {
      setIsOpenProp(false);
    } else {
      setInternalOpen(false);
    }
  }, [isControlled, setIsOpenProp]);

  // keep body class when menu is open (prevents color flips)
  useEffect(() => {
    if (typeof document !== 'undefined') {
      if (isOpen) document.body.classList.add('burger-open');
      else document.body.classList.remove('burger-open');
    }
    return () => {
      if (typeof document !== 'undefined') document.body.classList.remove('burger-open');
    };
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) closeMenu();
    };
    if (isOpen) document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, closeMenu]);

  // calculate fixed position for portal button once (on mount/resize/when header changes)
  useEffect(() => {
    const updateBtnPos = () => {
      const header = document.querySelector('.header-container');
      // Не пересчитываем позицию если хедер скрыт или анимируется
      if (header && (header.classList.contains('header-hidden') || 
          getComputedStyle(header).transform !== 'none')) {
        return;
      }
      
      const headerLeft = document.querySelector('.header-left');
      if (headerLeft) {
        const rect = headerLeft.getBoundingClientRect();
        const btnHeight = 40;
        const top = rect.top + rect.height / 2 - btnHeight / 2;
        const left = rect.left + 8;
        setBtnTop(`${Math.max(top, 8)}px`);
        setBtnLeft(`${Math.max(left, 8)}px`);
      } else {
        setBtnTop('28px');
        setBtnLeft('24px');
      }
    };

    updateBtnPos();
    window.addEventListener('resize', updateBtnPos);

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
          debounceTimer = setTimeout(updateBtnPos, 100);
        }
      });
      observer.observe(header, { attributes: true, attributeFilter: ['class'] });
    }

    return () => {
      window.removeEventListener('resize', updateBtnPos);
      if (observer) observer.disconnect();
      if (debounceTimer) clearTimeout(debounceTimer);
    };
  }, []);

  // Smooth scroll to section
  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    closeMenu();
  };

  const barColor = black && isOpen ? '#fff' : black ? '#111' : '#fff';
  const labelColor = black && isOpen ? '#fff' : black ? '#111' : '#fff';

  // Portal content: button + overlay + panel — all rendered into body so layering is consistent
  const portalContent = (
    <div className="burger-portal-root" aria-hidden={!isOpen}>
      <button
        type="button"
        className={`burger-menu-btn portal ${isOpen ? 'open' : ''}`}
        onClick={toggleMenu}
        aria-expanded={isOpen}
        aria-label={isOpen ? 'Закрыть меню' : 'Открыть меню'}
        style={{
          position: 'fixed',
          top: btnTop,
          left: btnLeft,
          zIndex: 3002,
          '--label-color': labelColor,
          '--bar-color': barColor,
        }}
      >
        <span
          className={`burger-menu-label ${
            menuLabelVisible ? 'burger-menu-label-animated' : 'burger-menu-label-hidden'
          }`}
          style={{ color: labelColor }}
        >
          MENU
        </span>

        <span className="burger-menu-icon" aria-hidden="true">
          <span className="burger-menu-bar top" style={{ background: barColor }} />
          <span className="burger-menu-bar middle" style={{ background: barColor }} />
          <span className="burger-menu-bar bottom" style={{ background: barColor }} />
        </span>
      </button>

      <div
        className={`burger-overlay ${isOpen ? 'open' : ''}`}
        onClick={closeMenu}
        onKeyDown={(e) => {
          if (e.key === ' ' || e.key === 'Enter') closeMenu();
        }}
        role="button"
        tabIndex={isOpen ? 0 : -1}
        aria-label="Close menu"
        style={{ zIndex: 2000 }}
      />

      <aside
        className={`burger-panel ${isOpen ? 'open' : ''}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-hidden={!isOpen}
        style={{ zIndex: 2001 }}
      >
        <nav className="burger-nav" role="navigation" aria-label="Main menu">
          <Link to="/collections" onClick={closeMenu}>
            Коллекции
          </Link>
          <Link to="/account" onClick={closeMenu}>
            Аккаунт
          </Link>
          <button className="burger-nav-button" onClick={() => scrollToSection('box-office')}>
            BOX OFFICE
          </button>
          <button className="burger-nav-button" onClick={() => scrollToSection('contacts')}>
            Контакты
          </button>
        </nav>
      </aside>
    </div>
  );

  // Render placeholder in header (keeps layout) and portal content in body
  return (
    <>
      <div
        className="burger-menu-placeholder"
        aria-hidden="true"
        style={{ width: 64, height: 40 }}
      />
      {typeof document !== 'undefined' && document.body
        ? createPortal(portalContent, document.body)
        : portalContent}
    </>
  );
};

export default BurgerMenu;
