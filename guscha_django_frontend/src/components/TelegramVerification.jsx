import React, { useState, useEffect, useRef } from 'react';
import { FiMessageCircle, FiCheck, FiX, FiExternalLink } from 'react-icons/fi';
import { QRCodeSVG } from 'qrcode.react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { checkTelegramBotStatus } from '../api/authApi';
import '../styles/TelegramVerification.css';

const TelegramVerification = ({ verificationId, phoneNumber, onVerificationComplete, onBack }) => {
  const [step, setStep] = useState('setup'); // 'setup', 'waiting', 'verify'
  const [telegramCode, setTelegramCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [botActivated, setBotActivated] = useState(false);
  const [expiresAt, setExpiresAt] = useState(null);
  const [timeLeft, setTimeLeft] = useState('');
  const isCheckingRef = useRef(false);
  const intervalRef = useRef(null);
  const { verifyTelegramCode } = useAuth();
  const { showSuccess, showError } = useToast();

  // Проверка статуса бота каждые 3 секунды в режиме ожидания
  useEffect(() => {
    // Очищаем предыдущий интервал
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (step === 'waiting') {
      intervalRef.current = setInterval(async () => {
        if (isCheckingRef.current) return; // Предотвращаем множественные запросы
        
        isCheckingRef.current = true;
        
        try {
          const status = await checkTelegramBotStatus(verificationId);
          if (status.is_activated) {
            // Очищаем интервал при успешной активации
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
            setStep('verify');
            setBotActivated(true);
            showSuccess('Бот активирован! Теперь получите код в Telegram');
            setExpiresAt(status.expires_at);
          }
        } catch (error) {
          console.error('Ошибка проверки статуса бота:', error);
        } finally {
          isCheckingRef.current = false;
        }
      }, 3000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      isCheckingRef.current = false;
    };
  }, [step, verificationId, showSuccess]);

  // Таймер обратного отсчета
  useEffect(() => {
    if (expiresAt) {
      const timer = setInterval(() => {
        const now = new Date().getTime();
        const expiry = new Date(expiresAt).getTime();
        const difference = expiry - now;
        
        if (difference > 0) {
          const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((difference % (1000 * 60)) / 1000);
          setTimeLeft(`${minutes}:${seconds.toString().padStart(2, '0')}`);
        } else {
          setTimeLeft('Истек');
          clearInterval(timer);
        }
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [expiresAt]);

  const handleTelegramBotClick = () => {
    // Открываем Telegram бота
    const botUsername = process.env.REACT_APP_TELEGRAM_BOT_USERNAME || 'GuschaBot';
    const telegramUrl = `https://t.me/${botUsername}?start=${verificationId}`;
    window.open(telegramUrl, '_blank');
    
    // Переходим в режим ожидания активации
    setStep('waiting');
    showSuccess('Telegram-бот открыт! Отправьте /start в боте для активации');
  };

  const handleQRClick = async () => {
    // При клике на QR-код переходим в режим ожидания
    setStep('waiting');
    showSuccess('QR-код отсканирован! Проверяем активацию бота...');
    
    // Немедленно проверяем статус (для быстрого перехода при сканировании с телефона)
    setTimeout(async () => {
      try {
        const status = await checkTelegramBotStatus(verificationId);
        if (status.is_activated) {
          setStep('verify');
          setBotActivated(true);
          showSuccess('Бот активирован! Теперь получите код в Telegram');
        }
      } catch (error) {
        console.error('Ошибка быстрой проверки статуса:', error);
      }
    }, 2000); // Проверяем через 2 секунды после клика
  };

  const handleCodeSubmit = async (e) => {
    e.preventDefault();
    
    if (!telegramCode.trim() || telegramCode.length !== 6) {
      showError('Введите 6-значный код');
      return;
    }

    setIsLoading(true);
    
    try {
      const result = await verifyTelegramCode(phoneNumber, telegramCode);
      
      console.log('Результат верификации Telegram:', result);
      
      // Проверяем, требуется ли завершить регистрацию
      if (result.requires_registration) {
        showSuccess('Код подтвержден! Завершите регистрацию на сайте.');
        // Вызываем callback для обработки необходимости завершения регистрации
        if (onVerificationComplete) {
          onVerificationComplete({ requiresRegistration: true, result: result });
        }
      } else if (result.success || result.token || result.access_token) {
        showSuccess('Telegram успешно подтвержден!');
        if (onVerificationComplete) {
          // Передаем пользователя или весь результат, только если user существует
          onVerificationComplete(result.user ? result.user : result);
        }
      } else {
        showError('Ошибка верификации кода');
      }
    } catch (error) {
      console.error('Ошибка верификации:', error);
      const errorMessage = error.message || 'Неверный код верификации';
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="telegram-verification">
      <div className="verification-container">
        <div className="verification-header">
          <div className="telegram-icon">
            <FiMessageCircle size={48} />
          </div>
          <h2>Подтверждение через Telegram</h2>
          <p>Для завершения регистрации подтвердите свой аккаунт через Telegram-бота</p>
        </div>

        {step === 'setup' && (
          <div className="verification-step">
            <div className="step-content">
              <h3>Шаг 1: Активируйте бота</h3>
              <p>Нажмите кнопку ниже, чтобы открыть Telegram-бота и начать процесс верификации</p>
              
              <div className="qr-code-container" onClick={handleQRClick} style={{cursor: 'pointer'}}>
                <QRCodeSVG 
                  value={`https://t.me/${process.env.REACT_APP_TELEGRAM_BOT_USERNAME || 'GuschaBot'}?start=${verificationId}`}
                  size={200}
                  fgColor="#000000"
                  bgColor="#ffffff"
                  level="M"
                />
                <p className="qr-description">Отсканируйте QR-код или нажмите на него для перехода в бота</p>
              </div>

              <button 
                className="telegram-bot-btn"
                onClick={handleTelegramBotClick}
              >
                <FiExternalLink size={20} />
                Открыть Telegram-бота
              </button>
            </div>
          </div>
        )}

        {step === 'waiting' && (
          <div className="verification-step">
            <div className="step-content">
              <h3>Ожидание активации бота</h3>
              <p>Отправьте команду /start в Telegram-боте для активации</p>
              
              <div className="waiting-indicator">
                <div className="pulse-animation"></div>
                <span>Проверяем активацию бота...</span>
              </div>
              
              <div className="waiting-instructions">
                <p>1. Перейдите в Telegram-бота</p>
                <p>2. Отправьте команду <strong>/start</strong></p>
                <p>3. Дождитесь приветственного сообщения</p>
              </div>
            </div>
          </div>
        )}

        {step === 'verify' && (
          <div className="verification-step">
            <div className="step-content">
              <h3>Шаг 3: Введите код</h3>
              <p>Введите 6-значный код, который вы получили в Telegram-боте</p>
              
              {timeLeft && (
                <div className="timer-display">
                  <span className={timeLeft === 'Истек' ? 'expired' : 'active'}>
                    Код действителен: {timeLeft}
                  </span>
                </div>
              )}

              <form onSubmit={handleCodeSubmit} className="code-form">
                <div className="code-input-group">
                  <input
                    type="text"
                    className="code-input"
                    value={telegramCode}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                      setTelegramCode(value);
                    }}
                    placeholder="000000"
                    maxLength={6}
                    disabled={isLoading}
                    autoFocus
                  />
                </div>
                
                <button 
                  type="submit" 
                  className="verify-btn"
                  disabled={isLoading || telegramCode.length !== 6}
                >
                  {isLoading ? (
                    <>
                      <div className="btn-spinner" />
                      Проверка...
                    </>
                  ) : (
                    <>
                      <FiCheck size={20} />
                      Подтвердить
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        )}

        <div className="verification-footer">
          <button 
            type="button" 
            className="back-btn"
            onClick={onBack}
            disabled={isLoading}
          >
            <FiX size={16} />
            Вернуться к регистрации
          </button>
        </div>
      </div>
    </div>
  );
};

export default TelegramVerification;