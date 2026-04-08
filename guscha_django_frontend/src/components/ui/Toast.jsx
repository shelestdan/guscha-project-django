import React, { useEffect, useState, useCallback, useRef } from 'react';
import './Toast.css';

const Toast = ({ 
  message, 
  type = 'info', // 'success', 'error', 'warning', 'info'
  duration = 4000, 
  onClose, 
  position = 'top-right' 
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isLeaving, setIsLeaving] = useState(false);
  const closeTimeoutRef = useRef(null);
  const onCloseRef = useRef(onClose);
  
  // Обновляем ref при изменении onClose
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  const handleClose = useCallback(() => {
    setIsLeaving(true);
    closeTimeoutRef.current = setTimeout(() => {
      setIsVisible(false);
      if (onCloseRef.current) onCloseRef.current();
    }, 300); // Время анимации
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    return () => {
      clearTimeout(timer);
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current);
      }
    };
  }, [duration, handleClose]);

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      default:
        return 'ℹ️';
    }
  };

  if (!isVisible) return null;

  return (
    <div 
      className={`toast toast--${type} toast--${position} ${isLeaving ? 'toast--leaving' : ''}`}
      onClick={handleClose}
    >
      <div className="toast__content">
        <span className="toast__icon">{getIcon()}</span>
        <span className="toast__message">{message}</span>
        <button className="toast__close" onClick={handleClose}>×</button>
      </div>
    </div>
  );
};

export default Toast;
