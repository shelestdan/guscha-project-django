import React from 'react';
import { FiShield, FiLock, FiEyeOff } from 'react-icons/fi';
import '../styles/SecurityIndicator.css';

/**
 * 🔐 Компонент индикатора безопасности
 * Показывает пользователю, что их пароли защищены клиентским хешированием
 */
const SecurityIndicator = ({ isActive = true, compact = false }) => {
  if (compact) {
    return (
      <div className="security-indicator compact">
        <FiShield className={`shield-icon ${isActive ? 'active' : ''}`} />
        <span className="security-text">
          {isActive ? 'Защищено' : 'Не защищено'}
        </span>
      </div>
    );
  }

  return (
    <div className={`security-indicator ${isActive ? 'active' : 'inactive'}`}>
      <div className="security-header">
        <FiShield className="shield-icon" />
        <h4>Клиентская защита паролей</h4>
      </div>
      
      <div className="security-details">
        <div className="security-feature">
          <FiLock className="feature-icon" />
          <div className="feature-text">
            <strong>Хеширование на устройстве</strong>
            <p>Ваш пароль хешируется локально перед отправкой</p>
          </div>
        </div>
        
        <div className="security-feature">
          <FiEyeOff className="feature-icon" />
          <div className="feature-text">
            <strong>Сервер не видит пароль</strong>
            <p>Сервер получает только криптографический хеш</p>
          </div>
        </div>
        
        <div className="security-feature">
          <FiShield className="feature-icon" />
          <div className="feature-text">
            <strong>Двойная защита</strong>
            <p>Дополнительное хеширование на сервере</p>
          </div>
        </div>
      </div>
      
      <div className="security-status">
        <div className={`status-dot ${isActive ? 'active' : 'inactive'}`}></div>
        <span className="status-text">
          {isActive ? 'Активна максимальная защита' : 'Защита отключена'}
        </span>
      </div>
    </div>
  );
};

/**
 * 🔐 Мини-индикатор для форм
 */
export const PasswordSecurityBadge = ({ show = true }) => {
  if (!show) return null;

  return (
    <div className="password-security-badge">
      <FiShield className="badge-icon" />
      <span className="badge-text">
        Пароль хешируется локально
      </span>
      <div className="badge-tooltip">
        <div className="tooltip-content">
          <p><strong>🔐 Ваша безопасность:</strong></p>
          <ul>
            <li>Пароль хешируется на вашем устройстве</li>
            <li>Сервер не видит оригинальный пароль</li>
            <li>Дополнительная защита от перехвата</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

/**
 * 🔐 Индикатор прогресса хеширования
 */
export const HashingProgress = ({ isHashing = false }) => {
  if (!isHashing) return null;

  return (
    <div className="hashing-progress">
      <div className="hashing-spinner"></div>
      <span className="hashing-text">
        🔐 Хеширование пароля...
      </span>
    </div>
  );
};

export default SecurityIndicator; 