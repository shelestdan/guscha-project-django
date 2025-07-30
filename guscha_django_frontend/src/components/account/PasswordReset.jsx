import React, { useState } from 'react';
import { requestPasswordReset } from '../../api/authApi';
import { useToast } from '../../hooks/useToast';
import '../../styles/PasswordReset.css';

/**
 * Компонент для сброса пароля
 */
const PasswordReset = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isEmailSent, setIsEmailSent] = useState(false);
  const { showSuccess, showError } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email.trim()) {
      showError('Пожалуйста, введите email адрес');
      return;
    }

    // Простая валидация email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      showError('Пожалуйста, введите корректный email адрес');
      return;
    }

    setIsLoading(true);
    
    try {
      await requestPasswordReset(email);
      setIsEmailSent(true);
      showSuccess('Инструкции по сбросу пароля отправлены на ваш email');
    } catch (error) {
      console.error('Ошибка при запросе сброса пароля:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.email?.[0] ||
                          'Произошла ошибка при отправке запроса';
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setEmail('');
    setIsEmailSent(false);
  };

  if (isEmailSent) {
    return (
      <div className="password-reset-container">
        <div className="password-reset-success">
          <div className="success-icon">✓</div>
          <h3>Письмо отправлено!</h3>
          <p>
            Мы отправили инструкции по сбросу пароля на адрес <strong>{email}</strong>.
            Проверьте свою почту и следуйте указаниям в письме.
          </p>
          <p className="check-spam">
            Если письмо не пришло в течение нескольких минут, проверьте папку "Спам".
          </p>
          <button 
            type="button" 
            className="reset-form-btn"
            onClick={handleReset}
          >
            Отправить повторно
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="password-reset-container">
      <div className="password-reset-form">
        <h3>Сброс пароля</h3>
        <p className="reset-description">
          Введите ваш email адрес, и мы отправим вам инструкции по сбросу пароля.
        </p>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email адрес*</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Введите ваш email"
              required
              disabled={isLoading}
            />
          </div>
          
          <button 
            type="submit" 
            className="reset-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? 'Отправка...' : 'Отправить инструкции'}
          </button>
        </form>
        
        <div className="reset-info">
          <p>
            <strong>Безопасность:</strong> Ссылка для сброса пароля будет действительна 
            в течение 24 часов и может быть использована только один раз.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PasswordReset;