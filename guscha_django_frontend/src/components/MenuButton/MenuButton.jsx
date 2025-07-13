import React, { useState } from 'react';
import styles from './MenuButton.module.css';

const MenuButton = () => {
  const [open, setOpen] = useState(false);

  return (
    <button
      className={`${styles.menuButton} menu-button-container`}
      aria-label={open ? 'Закрыть меню' : 'Открыть меню'}
      onClick={() => setOpen((v) => !v)}
    >
      <div className={open ? styles.burgerOpen : styles.burger}>
        <span />
        <span />
      </div>
      <span className="menu-button-label">MENU</span>
    </button>
  );
};

export default React.memo(MenuButton); 