import React, { useState, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './styles/BurgerMenu.css';

const BurgerMenu = ({ black = false, menuLabelVisible = true }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleMenu = useCallback(() => {
    setIsOpen(prev => !prev);
  }, []);
  
  const closeMenu = useCallback(() => {
    setIsOpen(false);
  }, []);

  // Закрытие меню по Escape
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        closeMenu();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, closeMenu]);

  // Функция плавной прокрутки к элементу
  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
    closeMenu(); // Закрываем меню после прокрутки
  };

  // Цвет полосок: если белая панель и меню открыто — белый, иначе по логике
  const barColor = black && isOpen ? '#fff' : black ? '#111' : '#fff';
  const labelColor = black && isOpen ? '#fff' : black ? '#111' : '#fff';

  return (
    <div>
      {/* Кнопка меню */}
      <button
        className={`burger-menu-btn${isOpen ? ' open' : ''}`}
        onClick={toggleMenu}
        aria-label={isOpen ? 'Закрыть меню' : 'Открыть меню'}
        style={{ '--label-color': labelColor, '--bar-color': barColor }}
      >
        <span
          className={`burger-menu-label${menuLabelVisible ? ' burger-menu-label-animated' : ' burger-menu-label-hidden'}`}
          style={{ color: labelColor }}
        >
          MENU
        </span>
        <span className="burger-menu-icon">
          <span className="burger-menu-bar top" style={{ background: barColor }} />
          <span className="burger-menu-bar middle" style={{ background: barColor }} />
          <span className="burger-menu-bar bottom" style={{ background: barColor }} />
        </span>
      </button>
      
      {/* Overlay и панель */}
      <div 
        className={`burger-overlay${isOpen ? ' open' : ''}`} 
        onClick={closeMenu}
        onKeyDown={(e) => e.key === 'Escape' && closeMenu()}
        role="button"
        tabIndex={isOpen ? 0 : -1}
        aria-label="Close menu"
      />
      <aside className={`burger-panel${isOpen ? ' open' : ''}`}> 
        <nav className="burger-nav">
          <Link to="/collections" onClick={closeMenu}>Коллекции</Link>
          <Link to="/account" onClick={closeMenu}>Аккаунт</Link>
          <button 
            className="burger-nav-button" 
            onClick={() => scrollToSection('box-office')}
          >
            BOX OFFICE
          </button>
          <button 
            className="burger-nav-button" 
            onClick={() => scrollToSection('contacts')}
          >
            Контакты
          </button>
        </nav>
      </aside>
    </div>
  );
};

export default BurgerMenu;