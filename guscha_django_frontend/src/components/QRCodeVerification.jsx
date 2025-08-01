import React, { useState, useEffect, useRef } from 'react';
import { FiMessageCircle, FiCheck, FiX, FiRefreshCw } from 'react-icons/fi';
import { QRCodeSVG } from 'qrcode.react';
import { useToast } from '../hooks/useToast';
import { useAuth } from '../hooks/useAuth';
import axiosInstance from '../api/axiosInstance';
import '../styles/QRCodeVerification.css';

const QRCodeVerification = ({ onVerificationComplete, onBack, userData }) => {
  const [qrData, setQrData] = useState(null);
  const [step, setStep] = useState('loading'); // 'loading', 'qr', 'waiting', 'verify'
  const [telegramCode, setTelegramCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState('');
  const intervalRef = useRef(null);
  const statusCheckRef = useRef(null);
  const { showSuccess, showError } = useToast();
  const { verifyTelegramCode } = useAuth();

  // Создание нового QR-кода при загрузке компонента
  useEffect(() => {
    createNewQRCode();
    return () => {
      // Очистка интервалов при размонтировании
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (statusCheckRef.current) {
        clearInterval(statusCheckRef.current);
      }
    };
  }, []);

  // Проверка статуса QR-кода
  useEffect(() => {
    if (step === 'waiting' && qrData?.qr_id) {
      statusCheckRef.current = setInterval(async () => {
        try {
          const response = await axiosInstance.get(`/api/accounts/qr/status/${qrData.qr_id}/`);
          const status = response.data;
          
          // Проверяем новое поле verification_code_ready
          if (status.qr_data?.verification_code_ready) {
            clearInterval(statusCheckRef.current);
            setStep('verify');
            showSuccess('Код верификации готов! Введите код из Telegram');
            startExpirationTimer();
          } else if (status.bot_started) {
            clearInterval(statusCheckRef.current);
            setStep('verify');
            showSuccess('Бот запущен! Введите код из Telegram');
            startExpirationTimer();
          } else if (status.trigger_activated) {
            showSuccess('QR-код отсканирован! Ожидаем запуска бота...');
          }
        } catch (error) {
          console.error('Ошибка проверки статуса QR-кода:', error);
        }
      }, 2000);
    }

    return () => {
      if (statusCheckRef.current) {
        clearInterval(statusCheckRef.current);
      }
    };
  }, [step, qrData?.qr_id, showSuccess]);

  // Таймер истечения кода
  const startExpirationTimer = () => {
    const expirationTime = new Date().getTime() + (10 * 60 * 1000); // 10 минут
    
    intervalRef.current = setInterval(() => {
      const now = new Date().getTime();
      const difference = expirationTime - now;
      
      if (difference > 0) {
        const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((difference % (1000 * 60)) / 1000);
        setTimeLeft(`${minutes}:${seconds.toString().padStart(2, '0')}`);
      } else {
        setTimeLeft('Истек');
        clearInterval(intervalRef.current);
      }
    }, 1000);
  };

  const createNewQRCode = async () => {
    setIsLoading(true);
    setStep('loading');
    
    try {
      const response = await axiosInstance.post('/api/accounts/qr/create/', {
        type: 'qr_registration',
        description: 'QR код для регистрации',
        pending_registration_id: userData?.verification_id
      });
      
      const data = response.data;
      // Сохраняем данные QR-кода
      setQrData({
        qr_id: data.qr_code,
        qr_data: data.qr_data.trigger_url,  // Используем trigger_url для QR-кода
        telegram_url: data.qr_data.telegram_bot_url,
        verification_id: data.qr_code  // Используем qr_code как verification_id
      });
      setStep('qr');
      showSuccess('Новый QR-код создан!');
    } catch (error) {
      console.error('Ошибка создания QR-кода:', error);
      showError('Не удалось создать QR-код');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQRClick = () => {
    if (qrData?.qr_data) {
      // Открываем триггер-ссылку
      window.open(qrData.qr_data, '_blank');
      setStep('waiting');
      showSuccess('QR-код активирован! Ожидаем переход в Telegram...');
    }
  };

  const handleCodeSubmit = async (e) => {
    e.preventDefault();
    
    if (!telegramCode.trim() || telegramCode.length !== 6) {
      showError('Введите 6-значный код');
      return;
    }

    setIsLoading(true);
    
    try {
      const result = await verifyTelegramCode(userData.phone, telegramCode);
      if (result.success) {
        if (result.requires_registration) {
          showSuccess('Код подтвержден! Завершаем регистрацию...');
          // Для QR-регистрации нужно завершить регистрацию
          onVerificationComplete({ requiresRegistration: true, result: result });
        } else {
          showSuccess('Telegram успешно подтвержден!');
          onVerificationComplete(result.user ? result.user : result);
        }
      }
    } catch (error) {
      console.error('Ошибка верификации:', error);
      const errorMessage = error.message || 'Неверный код верификации';
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshQR = () => {
    // Очищаем интервалы
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    if (statusCheckRef.current) {
      clearInterval(statusCheckRef.current);
    }
    
    // Создаем новый QR-код
    createNewQRCode();
  };

  return (
    <div className="qr-verification">
      <div className="verification-container">
        <div className="verification-header">
          <div className="telegram-icon">
            <svg width="48" height="48" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="16" cy="16" r="14" fill="url(#paint0_linear_87_7225)"/>
              <path d="M22.9866 10.2088C23.1112 9.40332 22.3454 8.76755 21.6292 9.082L7.36482 15.3448C6.85123 15.5703 6.8888 16.3483 7.42147 16.5179L10.3631 17.4547C10.9246 17.6335 11.5325 17.541 12.0228 17.2023L18.655 12.6203C18.855 12.4821 19.073 12.7665 18.9021 12.9426L14.1281 17.8646C13.665 18.3421 13.7569 19.1512 14.314 19.5005L19.659 22.8523C20.2585 23.2282 21.0297 22.8506 21.1418 22.1261L22.9866 10.2088Z" fill="white"/>
              <defs>
                <linearGradient id="paint0_linear_87_7225" x1="16" y1="2" x2="16" y2="30" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#37BBFE"/>
                  <stop offset="1" stopColor="#007DBB"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        {step === 'loading' && (
          <div className="verification-step">
            <div className="step-content">
              <div className="loading-indicator">
                <div className="spinner"></div>
                <p>Создание уникального QR-кода...</p>
              </div>
            </div>
          </div>
        )}

        {step === 'qr' && qrData && (
          <div className="verification-step">
            <div className="step-content">
              <p className="qr-instruction-text">Нажмите или отсканируйте QR код, чтобы перейти TG бот и завершить регистрацию</p>
              <div className="qr-code-container" onClick={handleQRClick}>
                <QRCodeSVG 
                  value={qrData.qr_data}
                  size={250}
                  fgColor="#000000"
                  bgColor="#ffffff"
                  level="M"
                  className="qr-code"
                />
              </div>

              <button 
                className="refresh-btn"
                onClick={handleRefreshQR}
                disabled={isLoading}
              >
                <FiRefreshCw size={16} />
                Создать новый QR-код
              </button>
            </div>
          </div>
        )}

        {step === 'waiting' && (
          <div className="verification-step">
            <div className="step-content">
              <h3>Ожидание активации</h3>
              <p>QR-код отсканирован. Ожидаем запуска Telegram-бота...</p>
              
              <div className="waiting-indicator">
                <div className="pulse-animation"></div>
                <span>Проверяем статус...</span>
              </div>
              
              <div className="waiting-instructions">
                <p>1. ✅ QR-код отсканирован</p>
                <p>2. 🔄 Переход в Telegram</p>
                <p>3. ⏳ Ожидаем команду /start</p>
              </div>
            </div>
          </div>
        )}

        {step === 'verify' && (
          <div className="verification-step">
            <div className="step-content">
              <h3>Введите код из Telegram</h3>
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

export default QRCodeVerification;