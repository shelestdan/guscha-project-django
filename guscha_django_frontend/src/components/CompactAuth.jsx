import React, { useState } from 'react';
import AdvancedAuth from './AdvancedAuth';
import { FiX, FiUser, FiUserPlus } from 'react-icons/fi';
import '../styles/CompactAuth.css';

const CompactAuth = ({ onLogin, onRegister, onGoogleLogin, onClose }) => {
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' или 'register'

  const handleShowLogin = () => {
    setAuthMode('login');
    setShowAuth(true);
  };

  const handleShowRegister = () => {
    setAuthMode('register');
    setShowAuth(true);
  };

  const handleClose = () => {
    setShowAuth(false);
    if (onClose) onClose();
  };

  if (!showAuth) {
    return (
      <div className="compact-auth-trigger">
        <button 
          className="auth-trigger-btn login-btn"
          onClick={handleShowLogin}
          title="Войти в аккаунт"
        >
          <FiUser size={16} />
          Войти
        </button>
        <button 
          className="auth-trigger-btn register-btn"
          onClick={handleShowRegister}
          title="Создать аккаунт"
        >
          <FiUserPlus size={16} />
          Регистрация
        </button>
      </div>
    );
  }

  return (
    <div className="compact-auth-overlay">
      <div className="compact-auth-wrapper">
        <button 
          className="compact-auth-close"
          onClick={handleClose}
          title="Закрыть"
        >
          <FiX size={18} />
        </button>
        
        <AdvancedAuth
          onLogin={async (email, password) => {
            await onLogin({ email, password });
            handleClose();
          }}
          onRegister={async (data) => {
            const result = await onRegister(data);
            // Не закрываем сразу, так как может потребоваться Telegram-верификация
            return result;
          }}
          onGoogleLogin={async () => {
            await onGoogleLogin();
            handleClose();
          }}
          onClose={handleClose}
        />
      </div>
    </div>
  );
};

export default CompactAuth;