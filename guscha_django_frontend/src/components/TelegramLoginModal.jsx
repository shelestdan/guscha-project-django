import React, { useState } from 'react';
import { FaTimes } from 'react-icons/fa';
import { isValidPhoneNumber } from 'libphonenumber-js';
import { ReactComponent as TelegramIcon } from '../assets/TelegramIcon.svg';
import '../styles/TelegramLoginModal.css';

const TelegramLoginModal = ({ isOpen, onClose, onSubmit, isLoading }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState('');
  const [isValidating, setIsValidating] = useState(false);

  // Валидация номера телефона
  const validatePhoneNumber = (phone) => {
    if (!phone) return false;
    return isValidPhoneNumber(phone);
  };

  const handlePhoneChange = (e) => {
    setPhoneNumber(e.target.value);
    
    // Очищаем ошибку при вводе
    if (error) {
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!phoneNumber.trim()) {
      setError('Введите номер телефона');
      return;
    }
    
    if (!validatePhoneNumber(phoneNumber)) {
      setError('Введите корректный номер телефона');
      return;
    }
    
    setIsValidating(true);
    setError('');
    
    try {
      await onSubmit(phoneNumber);
    } catch (err) {
      setError(err.message || 'Произошла ошибка при отправке');
    } finally {
      setIsValidating(false);
    }
  };

  const handleClose = () => {
    setPhoneNumber('');
    setError('');
    setIsValidating(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="telegram-modal-overlay" onClick={handleClose}>
      <div className="telegram-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="telegram-modal-header">
          <div className="telegram-modal-title">
            <TelegramIcon className="telegram-icon" />
            <h2>Вход через Telegram</h2>
          </div>
          <button 
            className="telegram-modal-close" 
            onClick={handleClose}
            disabled={isValidating || isLoading}
          >
            <FaTimes />
          </button>
        </div>
        
        <div className="telegram-modal-body">
          <p className="telegram-modal-description">
            Введите номер телефона, привязанный к вашему аккаунту Telegram.
            Мы отправим запрос на подтверждение в ваш Telegram бот.
          </p>
          
          <form onSubmit={handleSubmit} className="telegram-form">
            <div className="telegram-input-group">
              <label htmlFor="phone" className="telegram-label">
                Номер телефона
              </label>
              <input
                type="tel"
                id="phone"
                className={`telegram-input ${error ? 'error' : ''}`}
                value={phoneNumber}
                onChange={handlePhoneChange}
                placeholder="+1 234 567-8900"
                disabled={isValidating || isLoading}
                autoFocus
              />
              {error && <span className="telegram-error">{error}</span>}
            </div>
            
            <button 
              type="submit" 
              className="telegram-submit-btn"
              disabled={isValidating || isLoading || !phoneNumber.trim()}
            >
              {isValidating || isLoading ? (
                <>
                  <div className="telegram-spinner"></div>
                  Отправляем...
                </>
              ) : (
                <>
                  <TelegramIcon />
                  Войти через Telegram
                </>
              )}
            </button>
          </form>
          
          <div className="telegram-modal-footer">
            <p className="telegram-footer-text">
              После отправки откройте Telegram бот и подтвердите вход
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TelegramLoginModal;