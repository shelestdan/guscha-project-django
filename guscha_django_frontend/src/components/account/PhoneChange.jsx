import React, { useState, useEffect } from 'react';
import PhoneInput from 'react-phone-number-input';
import { isValidPhoneNumber } from 'libphonenumber-js';
import { useToast } from '../../hooks/useToast';
import 'react-phone-number-input/style.css';
import '../../styles/PhoneChange.css';

/**
 * Компонент для смены номера телефона через Telegram верификацию
 */
const PhoneChange = ({ user, onUserUpdate }) => {
  const [step, setStep] = useState('current'); // 'current', 'verify-current', 'new-phone', 'verify-new', 'telegram-confirm'
  const [currentPhoneCode, setCurrentPhoneCode] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newPhoneCode, setNewPhoneCode] = useState('');
  const [telegramLink, setTelegramLink] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [codeExpiry, setCodeExpiry] = useState(null);
  const [timeLeft, setTimeLeft] = useState('');

  const { showSuccess, showError, showInfo } = useToast();

  // Таймер для отображения времени до истечения кода
  useEffect(() => {
    let interval = null;

    if (codeExpiry) {
      interval = setInterval(() => {
        const now = new Date();
        const expiry = new Date(codeExpiry);
        const diff = expiry - now;

        if (diff <= 0) {
          setTimeLeft('');
          setCodeExpiry(null);
          if (step === 'verify-current' || step === 'verify-new') {
            showError('Время действия кода истекло. Повторите процедуру заново.');
            setStep('current');
          }
        } else {
          const minutes = Math.floor(diff / 60000);
          const seconds = Math.floor((diff % 60000) / 1000);
          setTimeLeft(`${minutes}:${seconds.toString().padStart(2, '0')}`);
        }
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [codeExpiry, step, showError]);

  // Отправка кода для подтверждения текущего номера
  const handleSendCurrentPhoneCode = async () => {
    if (!user.phone) {
      showError('У вас не указан номер телефона в профиле');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/accounts/phone-change/send-current-code/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          phone_number: user.phone
        })
      });

      const data = await response.json();

      if (response.ok) {
        setStep('verify-current');
        setCodeExpiry(new Date(Date.now() + 10 * 60 * 1000)); // 10 минут
        showSuccess('Код отправлен в ваш Telegram бот!');
      } else {
        showError(data.error || 'Ошибка отправки кода');
      }
    } catch (error) {
      console.error('Ошибка отправки кода:', error);
      showError('Ошибка отправки кода. Попробуйте позже.');
    } finally {
      setIsLoading(false);
    }
  };

  // Проверка кода для текущего номера
  const handleVerifyCurrentCode = async () => {
    if (!currentPhoneCode.trim() || currentPhoneCode.length !== 6) {
      showError('Введите 6-значный код');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/accounts/phone-change/verify-current/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          verification_code: currentPhoneCode
        })
      });

      const data = await response.json();

      if (response.ok) {
        setStep('new-phone');
        setCurrentPhoneCode('');
        setCodeExpiry(null);
        showSuccess('Текущий номер подтвержден! Теперь введите новый номер.');
      } else {
        showError(data.error || 'Неверный код');
      }
    } catch (error) {
      console.error('Ошибка проверки кода:', error);
      showError('Ошибка проверки кода. Попробуйте позже.');
    } finally {
      setIsLoading(false);
    }
  };

  // Отправка запроса на смену номера
  const handleSubmitNewPhone = async () => {
    if (!newPhone || !isValidPhoneNumber(newPhone)) {
      showError('Введите корректный номер телефона');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/accounts/phone-change/request-change/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          new_phone_number: newPhone
        })
      });

      const data = await response.json();

      if (response.ok) {
        setStep('telegram-confirm');
        setTelegramLink(data.telegram_link);
        showInfo('Перейдите по ссылке в Telegram для подтверждения смены номера');
      } else {
        showError(data.error || 'Ошибка запроса смены номера');
      }
    } catch (error) {
      console.error('Ошибка запроса смены номера:', error);
      showError('Ошибка запроса смены номера. Попробуйте позже.');
    } finally {
      setIsLoading(false);
    }
  };

  // Проверка статуса смены номера
  const handleCheckChangeStatus = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/accounts/phone-change/status/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        if (data.is_completed) {
          // Обновляем пользователя с новым номером
          onUserUpdate({
            ...user,
            phone: data.new_phone_number
          });
          showSuccess('Номер телефона успешно изменен!');
          setStep('current');
          setNewPhone('');
          setTelegramLink('');
        } else {
          showInfo('Смена номера еще не подтверждена в Telegram');
        }
      } else {
        showError(data.error || 'Ошибка проверки статуса');
      }
    } catch (error) {
      console.error('Ошибка проверки статуса:', error);
      showError('Ошибка проверки статуса. Попробуйте позже.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setStep('current');
    setCurrentPhoneCode('');
    setNewPhone('');
    setNewPhoneCode('');
    setTelegramLink('');
    setCodeExpiry(null);
  };

  return (
    <div className="phone-change-container">
      <div className="phone-change-header">
        <h2>Смена номера телефона</h2>
        <p>Измените номер телефона, привязанный к вашему аккаунту</p>
      </div>

      {step === 'current' && (
        <div className="phone-change-step">
          <div className="current-phone-info">
            <h3>Текущий номер телефона</h3>
            <div className="phone-display">
              {user.phone || 'Номер не указан'}
            </div>
            {user.phone && (
              <p className="step-description">
                Для смены номера сначала подтвердите текущий номер через Telegram код
              </p>
            )}
          </div>

          {user.phone ? (
            <button
              className="btn-primary"
              onClick={handleSendCurrentPhoneCode}
              disabled={isLoading}
            >
              {isLoading ? 'Отправка...' : 'Получить код подтверждения'}
            </button>
          ) : (
            <div className="no-phone-message">
              У вас не указан номер телефона. Сначала добавьте номер в настройках профиля.
            </div>
          )}
        </div>
      )}

      {step === 'verify-current' && (
        <div className="phone-change-step">
          <h3>Подтверждение текущего номера</h3>
          <p>Введите 6-значный код, отправленный в ваш Telegram</p>

          <div className="form-group">
            <label>Код подтверждения</label>
            <input
              type="text"
              value={currentPhoneCode}
              onChange={(e) => setCurrentPhoneCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="123456"
              maxLength="6"
              className="code-input"
            />
            {timeLeft && (
              <div className="code-timer">
                Код действителен еще: {timeLeft}
              </div>
            )}
          </div>

          <div className="button-group">
            <button
              className="btn-secondary"
              onClick={handleReset}
            >
              Отмена
            </button>
            <button
              className="btn-primary"
              onClick={handleVerifyCurrentCode}
              disabled={isLoading || currentPhoneCode.length !== 6}
            >
              {isLoading ? 'Проверка...' : 'Подтвердить'}
            </button>
          </div>
        </div>
      )}

      {step === 'new-phone' && (
        <div className="phone-change-step">
          <h3>Новый номер телефона</h3>
          <p>Введите новый номер телефона, который хотите привязать к аккаунту</p>

          <div className="form-group">
            <label>Новый номер телефона</label>
            <PhoneInput
              international
              defaultCountry="RU"
              value={newPhone}
              onChange={setNewPhone}
              placeholder="+7 (999) 123-45-67"
              className="phone-input"
            />
          </div>

          <div className="button-group">
            <button
              className="btn-secondary"
              onClick={handleReset}
            >
              Отмена
            </button>
            <button
              className="btn-primary"
              onClick={handleSubmitNewPhone}
              disabled={isLoading || !newPhone || !isValidPhoneNumber(newPhone)}
            >
              {isLoading ? 'Обработка...' : 'Продолжить'}
            </button>
          </div>
        </div>
      )}

      {step === 'telegram-confirm' && (
        <div className="phone-change-step">
          <h3>Подтверждение в Telegram</h3>
          <p>Для завершения смены номера перейдите по ссылке в Telegram и подтвердите операцию</p>

          <div className="telegram-link-container">
            <a
              href={telegramLink}
              target="_blank"
              rel="noopener noreferrer"
              className="telegram-link"
            >
              🔗 Открыть Telegram бот
            </a>
          </div>

          <div className="new-phone-display">
            <strong>Новый номер:</strong> {newPhone}
          </div>

          <p className="telegram-instructions">
            В Telegram боте:
            <br />1. Подтвердите обработку персональных данных
            <br />2. Поделитесь номером телефона
            <br />3. Бот проверит совпадение номеров и подтвердит смену
          </p>

          <div className="button-group">
            <button
              className="btn-secondary"
              onClick={handleReset}
            >
              Отмена
            </button>
            <button
              className="btn-primary"
              onClick={handleCheckChangeStatus}
              disabled={isLoading}
            >
              {isLoading ? 'Проверка...' : 'Проверить статус'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PhoneChange;