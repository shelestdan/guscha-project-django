import React, { useState, useEffect } from 'react';
import AdvancedRegistration from './AdvancedRegistration';
import { FiMail, FiLock, FiEye, FiEyeOff } from 'react-icons/fi';
import { FcGoogle } from 'react-icons/fc';
import '../styles/AdvancedAuth.css';
import { PasswordSecurityBadge } from './SecurityIndicator';

const AdvancedAuth = ({ onLogin, onRegister, onGoogleLogin, initialMode = 'login' }) => {
  const [isLogin, setIsLogin] = useState(initialMode === 'login');
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  // Обновляем режим при изменении initialMode
  useEffect(() => {
    setIsLogin(initialMode === 'login');
  }, [initialMode]);

  // Скролл теперь разрешен на страницах аутентификации

  // Валидация для входа
  const validateLogin = () => {
    const newErrors = {};
    
    if (!loginData.email.trim()) {
      newErrors.email = 'Email обязателен';
    } else if (!/\S+@\S+\.\S+/.test(loginData.email)) {
      newErrors.email = 'Некорректный формат email';
    }
    
    if (!loginData.password) {
      newErrors.password = 'Пароль обязателен';
    } else if (loginData.password.length < 6) {
      newErrors.password = 'Пароль должен содержать минимум 6 символов';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Обработка входа
  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!validateLogin()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      // 🔐 СТАНДАРТ OWASP: Передаем пароль в открытом виде через HTTPS
      // Хеширование происходит только на сервере
      await onLogin({
        email: loginData.email.toLowerCase().trim(),
        password: loginData.password // Пароль в открытом виде
      });
      
      console.log('🔐 Вход выполнен согласно стандартам OWASP');
    } catch (error) {
      setErrors({ 
        general: error.message || 'Ошибка входа. Проверьте данные и попробуйте снова.' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Обработка регистрации
  const handleRegister = async (registrationData) => {
    try {
      await onRegister(registrationData);
    } catch (error) {
      throw error;
    }
  };

  // Обработка Google входа
  const handleGoogleLogin = async () => {
    try {
      await onGoogleLogin();
    } catch (error) {
      console.error('Ошибка Google входа:', error);
      // Показываем ошибку в общем баннере вместо alert
      setErrors({ 
        general: 'Ошибка входа через Google. Попробуйте еще раз.' 
      });
    }
  };

  // Переключение между входом и регистрацией
  const switchToRegistration = () => {
    setIsLogin(false);
    setErrors({});
    setLoginData({ email: '', password: '' });
  };

  const switchToLogin = () => {
    setIsLogin(true);
    setErrors({});
  };

  // Если показываем регистрацию
  if (!isLogin) {
    return (
      <AdvancedRegistration
        onRegister={handleRegister}
        onSwitchToLogin={switchToLogin}
      />
    );
  }

  // Форма входа
  return (
    <div className="advanced-auth">
      <div className="auth-container">
        <div className="auth-header">
          <h1>Вход в аккаунт</h1>
          <p>Введите данные для входа</p>
        </div>

        <form className="auth-form" onSubmit={handleLogin}>
          {errors.general && (
            <div className="error-banner">
              {errors.general}
            </div>
          )}

          <div className="form-group">
            <label>
              <FiMail />
              Email
            </label>
            <input
              type="email"
              value={loginData.email}
              onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
              className={`form-input ${errors.email ? 'invalid' : ''}`}
              placeholder="Введите ваш email"
              disabled={isSubmitting}
              autoComplete="email"
            />
            {errors.email && (
              <div className="error-message">
                {errors.email}
              </div>
            )}
          </div>

          <div className="form-group">
            <label>
              <FiLock />
              Пароль
            </label>
            <div className="password-input-container">
              <input
                type={showPassword ? 'text' : 'password'}
                value={loginData.password}
                onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                className={`form-input ${errors.password ? 'invalid' : ''}`}
                placeholder="Введите ваш пароль"
                disabled={isSubmitting}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isSubmitting}
                aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
            {errors.password && (
              <div className="error-message">
                {errors.password}
              </div>
            )}
            <PasswordSecurityBadge show={loginData.password.length > 0} />
          </div>

          <button
            type="submit"
            className="auth-btn primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <div className="btn-spinner" />
                Вход...
              </>
            ) : (
              'Войти'
            )}
          </button>

          <div className="divider">
            <span>или</span>
          </div>

          <button
            type="button"
            className="auth-btn google"
            onClick={handleGoogleLogin}
            disabled={isSubmitting}
          >
            <FcGoogle />
            Войти через Google
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Нет аккаунта?{' '}
            <button
              type="button"
              className="link-btn"
              onClick={switchToRegistration}
              disabled={isSubmitting}
            >
              Зарегистрироваться
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdvancedAuth; 