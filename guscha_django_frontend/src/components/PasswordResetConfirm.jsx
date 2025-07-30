import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { confirmPasswordReset } from '../api/authApi';
import { useToast } from '../hooks/useToast';
import Header from './layout/Header/Header';
import '../styles/PasswordResetConfirm.css';

/**
 * Компонент для подтверждения сброса пароля по ссылке из email
 */
const PasswordResetConfirm = () => {
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
  
  const uid = searchParams.get('uid');
  const token = searchParams.get('token');

  useEffect(() => {
    // Проверяем наличие необходимых параметров
    if (!uid || !token) {
      showError('Неверная ссылка для сброса пароля');
      navigate('/account');
    }
  }, [uid, token, navigate, showError]);

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
      await confirmPasswordReset(uid, token, formData.newPassword);
      setIsSuccess(true);
      showSuccess('Пароль успешно изменен! Теперь вы можете войти с новым паролем.');
    } catch (error) {
      console.error('Ошибка при подтверждении сброса пароля:', error);
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
        <Header isHome={false} />
        <div className="password-reset-confirm-wrapper">
          <div className="password-reset-confirm-container">
            <div className="password-reset-success">
              <div className="success-icon">✓</div>
              <h2>Пароль успешно изменен!</h2>
              <p>
                Ваш пароль был успешно обновлен. Теперь вы можете войти в систему 
                используя новый пароль.
              </p>
              <button 
                type="button" 
                className="login-btn"
                onClick={handleGoToLogin}
              >
                Перейти к входу
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header isHome={false} />
      <div className="password-reset-confirm-wrapper">
        <div className="password-reset-confirm-container">
          <div className="password-reset-confirm-form">
            <h2>Создание нового пароля</h2>
            <p className="reset-description">
              Введите новый пароль для вашего аккаунта. Убедитесь, что он надежный и безопасный.
            </p>
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="newPassword">Новый пароль*</label>
                <input
                  type="password"
                  id="newPassword"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleInputChange}
                  placeholder="Введите новый пароль"
                  required
                  disabled={isLoading}
                  className={errors.newPassword ? 'error' : ''}
                />
                {errors.newPassword && (
                  <span className="error-message">{errors.newPassword}</span>
                )}
              </div>
              
              <div className="form-group">
                <label htmlFor="confirmPassword">Подтвердите пароль*</label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  placeholder="Повторите новый пароль"
                  required
                  disabled={isLoading}
                  className={errors.confirmPassword ? 'error' : ''}
                />
                {errors.confirmPassword && (
                  <span className="error-message">{errors.confirmPassword}</span>
                )}
              </div>
              
              <button 
                type="submit" 
                className="reset-submit-btn"
                disabled={isLoading}
              >
                {isLoading ? 'Сохранение...' : 'Сохранить новый пароль'}
              </button>
            </form>
            
            <div className="password-requirements">
              <h4>Требования к паролю:</h4>
              <ul>
                <li>Минимум 8 символов</li>
                <li>Минимум одна строчная буква (a-z)</li>
                <li>Минимум одна заглавная буква (A-Z)</li>
                <li>Минимум одна цифра (0-9)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default PasswordResetConfirm;