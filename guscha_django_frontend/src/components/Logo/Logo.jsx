import React from 'react';
import logo from '../../assets/icons/logo.svg';

const Logo = ({ isVisible, black = false, size = 64 }) => {
  return (
    <div
      className="logo-main-container"
      style={{ width: size, height: size }}
      aria-hidden={!isVisible}
    >
      <a
        href="/"
        aria-label="Guscha - перейти на главную страницу"
        className="logo-link"
      >
        <img
          src={logo}
          alt="Guscha logo"
          className={`logo-image ${black ? 'black' : 'white'} ${isVisible ? 'visible' : 'hidden'}`}
        />
      </a>
    </div>
  );
};

export default React.memo(Logo); 