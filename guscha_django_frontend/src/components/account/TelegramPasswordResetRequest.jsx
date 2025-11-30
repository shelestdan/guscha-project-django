import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../hooks/useToast';
import '../../styles/features/auth/password-reset.css';

/**
 * Компонент для инициации сброса пароля через Telegram
 * Автоматически отправляет запрос без формы ввода email
 */
const TelegramPasswordResetRequest = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isRequestSent, setIsRequestSent] = useState(false);
  const { user } = useAuth();
  const { showSuccess, showError } = useToast();

  const handleTelegramPasswordReset = async () => {
    if (!user?.is_telegram_verified) {
      showError('У вас не привязан Telegram аккаунт. Пожалуйста, привяжите Telegram для использования этой функции.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('/api/accounts/telegram/authenticated-password-reset/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (response.ok) {
        setIsRequestSent(true);
        showSuccess('Ссылка для сброса пароля отправлена в ваш Telegram!');
      } else {
        const errorData = await response.json();
        const errorMessage = errorData.detail || errorData.error || 'Произошла ошибка при отправке запроса';
        showError(errorMessage);
      }
    } catch (error) {
      console.error('Ошибка при запросе сброса пароля через Telegram:', error);
      showError('Произошла ошибка при отправке запроса');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setIsRequestSent(false);
  };

  if (isRequestSent) {
    return (
      <div className="password-reset-container">
        <div className="password-reset-success">
          <div className="success-icon">✓</div>
          <h3>Ссылка отправлена в Telegram!</h3>
          <p>
            Мы отправили ссылку для сброса пароля в ваш Telegram аккаунт.
            Проверьте сообщения от бота и перейдите по ссылке для сброса пароля.
          </p>
          <p className="check-spam">
            Если сообщение не пришло, убедитесь, что ваш Telegram аккаунт правильно привязан к профилю.
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
        <h3>Сброс пароля через Telegram</h3>
        <p className="reset-description">
          Нажмите кнопку ниже, чтобы получить ссылку для сброса пароля в вашем Telegram.
          {!user?.is_telegram_verified && (
            <span style={{ color: '#e74c3c', display: 'block', marginTop: '10px' }}>
              ⚠️ У вас не привязан Telegram аккаунт. Пожалуйста, привяжите Telegram в настройках профиля.
            </span>
          )}
        </p>

        <button
          type="button"
          className="reset-submit-btn"
          onClick={handleTelegramPasswordReset}
          disabled={isLoading || !user?.is_telegram_verified}
        >
          {isLoading ? 'Отправка...' : 'Отправить ссылку в Telegram'}
        </button>

        <div className="reset-info">
          <p>
            <strong>Безопасность:</strong> Ссылка для сброса пароля будет действительна
            в течение 24 часов и может быть использована только один раз.
          </p>
          {user?.is_telegram_verified && (
            <p>
              <strong>Telegram:</strong> Привязан ✓
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TelegramPasswordResetRequest;