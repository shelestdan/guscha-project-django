import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { confirmPasswordResetWithToken } from '../api/authApi';
import { useToast } from '../hooks/useToast';

import '../styles/features/auth/password-reset-confirm.css';

/**
 * Компонент для сброса пароля по токену из Telegram ссылки
 */
const TelegramPasswordReset = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();
  
  const [formData, setFormData] = useState({
    newPassword: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState({});
  
  const token = searchParams.get('token');

  useEffect(() => {
    // Проверяем наличие токена
    if (!token) {
      showError('Неверная ссылка для сброса пароля');
      navigate('/account');
    }
  }, [token, navigate, showError]);

  const validatePassword = (password) => {
    const errors = [];
    
    if (password.length < 8) {
      errors.push('Пароль должен содержать минимум 8 символов');
    }
    
    if (!/(?=.*[a-z])/.test(password)) {
      errors.push('Пароль должен содержать минимум одну строчную букву');
    }
    
    if (!/(?=.*[A-Z])/.test(password)) {
      errors.push('Пароль должен содержать минимум одну заглавную букву');
    }
    
    if (!/(?=.*\d)/.test(password)) {
      errors.push('Пароль должен содержать минимум одну цифру');
    }
    
    return errors;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Очищаем ошибки при изменении поля
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const newErrors = {};
    
    // Валидация нового пароля
    const passwordErrors = validatePassword(formData.newPassword);
    if (passwordErrors.length > 0) {
      newErrors.newPassword = passwordErrors.join('. ');
    }
    
    // Проверка совпадения паролей
    if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Пароли не совпадают';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setIsLoading(true);
    
    try {
      await confirmPasswordResetWithToken(token, formData.newPassword);
      setIsSuccess(true);
      showSuccess('Пароль успешно изменен! Теперь вы можете войти с новым паролем.');
    } catch (error) {
      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.new_password?.[0] ||
                          error.response?.data?.token?.[0] ||
                          'Произошла ошибка при сбросе пароля. Возможно, ссылка устарела.';
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoToLogin = () => {
    navigate('/account');
  };

  if (isSuccess) {
    return (
      <>
        <div className="password-reset-confirm-wrapper">
          <div className="password-reset-confirm-container">
            <div className="password-reset-confirm-content">
              <div className="success-icon">✓</div>
              <h1>Пароль успешно изменен!</h1>
              <p>Теперь вы можете войти в свой аккаунт с новым паролем.</p>
              <button 
                onClick={handleGoToLogin}
                className="btn btn-primary"
              >
                Войти в аккаунт
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="password-reset-confirm-wrapper">
        <div className="password-reset-confirm-container">
          <div className="password-reset-confirm-content">
            <h1>Создание нового пароля</h1>
            <p>Введите новый пароль для вашего аккаунта</p>
            
            <form onSubmit={handleSubmit} className="password-reset-form">
              <div className="form-group">
                <label htmlFor="newPassword">Новый пароль</label>
                <input
                  type="password"
                  id="newPassword"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleInputChange}
                  className={errors.newPassword ? 'error' : ''}
                  placeholder="Введите новый пароль"
                  required
                />
                {errors.newPassword && (
                  <span className="error-message">{errors.newPassword}</span>
                )}
              </div>
              
              <div className="form-group">
                <label htmlFor="confirmPassword">Подтвердите пароль</label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className={errors.confirmPassword ? 'error' : ''}
                  placeholder="Повторите новый пароль"
                  required
                />
                {errors.confirmPassword && (
                  <span className="error-message">{errors.confirmPassword}</span>
                )}
              </div>
              
              <div className="password-requirements">
                <p>Пароль должен содержать:</p>
                <ul>
                  <li>Минимум 8 символов</li>
                  <li>Одну строчную букву (a-z)</li>
                  <li>Одну заглавную букву (A-Z)</li>
                  <li>Одну цифру (0-9)</li>
                </ul>
              </div>
              
              <button 
                type="submit" 
                disabled={isLoading}
                className="btn btn-primary"
              >
                {isLoading ? 'Сохранение...' : 'Сохранить новый пароль'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default TelegramPasswordReset;