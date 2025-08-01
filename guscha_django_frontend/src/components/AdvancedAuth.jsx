import React, { useState, useEffect } from 'react';
import AdvancedRegistration from './AdvancedRegistration';
import TelegramVerification from './TelegramVerification';
import QRCodeVerification from './QRCodeVerification';
import TelegramLoginModal from './TelegramLoginModal';
import { FiMail, FiLock, FiEye, FiEyeOff } from 'react-icons/fi';
import { FcGoogle } from 'react-icons/fc';
import { SiTelegram } from 'react-icons/si';
import '../styles/AdvancedAuth.css';
// import { PasswordSecurityBadge } from './SecurityIndicator';

const AdvancedAuth = ({ onLogin, onRegister, onGoogleLogin, onTelegramLogin, onClose }) => {
  // Функция для получения CSRF токена
  const getCSRFToken = () => {
    const cookieValue = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
    return cookieValue;
  };
  const [mode, setMode] = useState('login'); // 'login', 'register', 'telegram-verify', 'qr-verify'
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [registrationResult, setRegistrationResult] = useState(null);
  const [originalRegistrationData, setOriginalRegistrationData] = useState(null);
  const [showTelegramModal, setShowTelegramModal] = useState(false);
  const [telegramLoginLoading, setTelegramLoginLoading] = useState(false);
  const [telegramStatusInterval, setTelegramStatusInterval] = useState(null);

  // Обработка Google OAuth callback при загрузке компонента
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');
    
    if (code || error) {
      console.log('🔵 Обнаружен Google OAuth callback в URL');
      handleGoogleCallback();
    }
  }, []);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await onLogin(loginData.email, loginData.password);
      // После успешного входа компонент Account автоматически обновится
      // благодаря изменению isLoggedIn в хуке useAuth
    } catch (error) {
      console.error('Ошибка входа:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          'Неверный email или пароль';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegistrationSuccess = async (registrationData) => {
    try {
      console.log('Вызов реальной функции регистрации с данными:', registrationData);
      const result = await onRegister(registrationData);
      console.log('Регистрация успешна:', result);
      
      // Проверяем, что результат содержит pending_registration_id
      if (result && result.pending_registration_id) {
        // Сохраняем результат регистрации и исходные данные
        // Преобразуем pending_registration_id в verification_id для совместимости с остальным кодом
        const resultWithVerificationId = {
          ...result,
          verification_id: result.pending_registration_id
        };
        setRegistrationResult(resultWithVerificationId);
        setOriginalRegistrationData(registrationData);
        // Сразу переходим к QR-коду
        setMode('qr-verify');
      } else {
        console.error('Не получен pending_registration_id от сервера');
        // Можно показать ошибку пользователю
      }
      
      return result;
    } catch (error) {
      console.error('Ошибка при регистрации в AdvancedAuth:', error);
      throw error; // Пробрасываем ошибку в AdvancedRegistration для обработки
    }
  };

  const handleTelegramVerificationComplete = async (result) => {
    console.log('Telegram-верификация завершена:', result);
    
    // Проверяем, требуется ли завершить регистрацию
    if (result && result.requiresRegistration) {
      console.log('Требуется завершить регистрацию');
      // Переходим к форме регистрации для завершения процесса
      setMode('register');
      return;
    }
    
    // Если это обычный пользователь (успешная авторизация)
    if (onLogin && result) {
      await onLogin(result);
      // НЕ закрываем модальное окно, так как мы уже на странице аккаунта
      // и компонент автоматически перерендерится при изменении isLoggedIn
    }
  };

  const handleBackToRegistration = () => {
    setMode('register');
    setRegistrationResult(null);
  };

  // const handleChooseTelegramVerification = () => {
  //   setMode('telegram-verify');
  // };

  const handleGoogleLogin = async () => {
    try {
      console.log('🔵 Начинаем Google OAuth процесс (redirect flow)');
      console.log('🔵 Текущий URL:', window.location.href);
      console.log('🔵 Origin:', window.location.origin);
      setIsLoading(true);
      setError('');

      // Проверяем client_id
      const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
      console.log('🔵 Google Client ID:', clientId);
      if (!clientId || clientId === 'your-google-client-id') {
        const errorMsg = 'Google Client ID не настроен в .env файле';
        console.error('❌', errorMsg);
        throw new Error(errorMsg);
      }

      // Определяем redirect URI (для nginx на порту 80)
      const redirectUri = 'http://localhost/auth/google/callback';
      console.log('🔵 Redirect URI:', redirectUri);
      console.log('🔵 ВАЖНО: Убедитесь, что этот URI добавлен в Google Console!');

      // Параметры для Google OAuth
      const params = new URLSearchParams({
        client_id: clientId,
        redirect_uri: redirectUri,
        response_type: 'code',
        scope: 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
        access_type: 'offline',
        prompt: 'select_account'
      });

      // Сохраняем текущий URL для возврата после авторизации
      localStorage.setItem('oauth_return_url', window.location.pathname);
      
      // Перенаправляем на Google OAuth
      const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
      console.log('🔵 Перенаправляем на Google OAuth:', googleAuthUrl);
      console.log('🔵 Параметры запроса:');
      console.log('   - client_id:', clientId);
      console.log('   - redirect_uri:', redirectUri);
      console.log('   - response_type: code');
      console.log('   - scope: email + profile');
      
      console.log('🔵 ДИАГНОСТИКА: Если получите redirect_uri_mismatch:');
      console.log('   1. Откройте https://console.cloud.google.com/');
      console.log('   2. APIs & Services → Credentials');
      console.log('   3. Найдите Client ID:', clientId);
      console.log('   4. Добавьте redirect_uri:', redirectUri);
      console.log('   5. Подождите 10 минут и очистите кэш браузера');
      
      window.location.href = googleAuthUrl;
      
    } catch (error) {
      console.error('❌ Ошибка Google OAuth:', error);
      console.error('❌ Стек ошибки:', error.stack);
      setError(`Ошибка Google OAuth: ${error.message}`);
      setIsLoading(false);
    }
  };

  const handleTelegramLogin = async () => {
    try {
      console.log('🔵 Открываем модальное окно Telegram входа');
      setError('');
      setShowTelegramModal(true);
    } catch (error) {
      console.error('❌ Ошибка открытия Telegram модального окна:', error);
      setError(`Ошибка: ${error.message}`);
    }
  };

  const handleTelegramPhoneSubmit = async (phoneNumber) => {
    try {
      console.log('🔵 Отправляем номер телефона для Telegram входа:', phoneNumber);
      setTelegramLoginLoading(true);
      
      // Получаем CSRF токен
      const csrfToken = getCSRFToken();
      
      // Отправляем запрос на бэкенд для инициации входа через Telegram
      const response = await fetch('/api/accounts/telegram/login/initiate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          verification_type: 'login'
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Ошибка отправки запроса');
      }
      
      // Закрываем модальное окно
      setShowTelegramModal(false);
      
      // Запускаем проверку статуса входа
      startTelegramLoginStatusCheck(phoneNumber);
      
      // Открываем Telegram клиент в новом окне
      if (data.telegram_link) {
        window.open(data.telegram_link, '_blank');
      }

    } catch (error) {
      console.error('❌ Ошибка отправки номера телефона:', error);
      throw error; // Пробрасываем ошибку в модальное окно
    } finally {
      setTelegramLoginLoading(false);
    }
  };

  const handleCloseTelegramModal = () => {
    setShowTelegramModal(false);
    setTelegramLoginLoading(false);
    // Очищаем интервал проверки статуса при закрытии модального окна
    if (telegramStatusInterval) {
      clearInterval(telegramStatusInterval);
      setTelegramStatusInterval(null);
    }
  };

  // Функция для проверки статуса входа через Telegram
  const checkTelegramLoginStatus = async (phoneNumber) => {
    try {
      // Получаем CSRF токен
      const csrfToken = getCSRFToken();
      
      const response = await fetch('/api/accounts/telegram/login/status/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          phone_number: phoneNumber
        })
      });
      
      const data = await response.json();
      
      if (response.ok && data.success && data.authenticated) {
        // Пользователь успешно авторизован через Telegram
        console.log('✅ Успешный вход через Telegram:', data);
        
        // Сохраняем токены
        if (data.access_token) {
          localStorage.setItem('token', data.access_token);
        }
        if (data.refresh_token) {
          localStorage.setItem('refreshToken', data.refresh_token);
        }
        
        // Очищаем интервал
        if (telegramStatusInterval) {
          clearInterval(telegramStatusInterval);
          setTelegramStatusInterval(null);
        }
        
        // Закрываем модальное окно и очищаем состояние
         setShowTelegramModal(false);
         setTelegramLoginLoading(false);
         
         // Вызываем callback для обновления состояния пользователя
         if (onLogin && typeof onLogin === 'function') {
           onLogin(data.user);
         }
        
        return true; // Авторизация завершена
      }
      
      return false; // Еще ожидаем подтверждения
    } catch (error) {
      console.error('❌ Ошибка проверки статуса входа через Telegram:', error);
      return false;
    }
  };

  // Функция для запуска периодической проверки статуса
  const startTelegramLoginStatusCheck = (phoneNumber) => {
    // Очищаем предыдущий интервал, если он есть
    if (telegramStatusInterval) {
      clearInterval(telegramStatusInterval);
    }
    
    let attempts = 0;
    const maxAttempts = 60; // Максимум 5 минут (60 * 5 секунд)
    
    const interval = setInterval(async () => {
      attempts++;
      
      const isAuthenticated = await checkTelegramLoginStatus(phoneNumber);
      
      if (isAuthenticated || attempts >= maxAttempts) {
        clearInterval(interval);
        setTelegramStatusInterval(null);
        
        if (attempts >= maxAttempts && !isAuthenticated) {
          console.log('⏰ Время ожидания входа через Telegram истекло');
          alert('Время ожидания истекло. Попробуйте войти снова.');
        }
      }
    }, 5000); // Проверяем каждые 5 секунд
    
    setTelegramStatusInterval(interval);
  };

  // Очистка интервала при размонтировании компонента
  useEffect(() => {
    return () => {
      if (telegramStatusInterval) {
        clearInterval(telegramStatusInterval);
      }
    };
  }, [telegramStatusInterval]);

  // Обработчик callback от Google OAuth
  const handleGoogleCallback = async () => {
    try {
      console.log('🔵 Обрабатываем Google OAuth callback');
      setIsLoading(true);
      setError('');

      // Получаем код авторизации из URL
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const error = urlParams.get('error');
      
      if (error) {
        throw new Error(`Google OAuth ошибка: ${error}`);
      }
      
      if (!code) {
        throw new Error('Код авторизации не получен от Google');
      }

      console.log(`🔵 Получен код авторизации: ${code.substring(0, 20)}...`);

      // Определяем base URL для API
      const getBaseURL = () => {
        // Проверяем переменную окружения
        if (process.env.REACT_APP_API_URL) {
          return process.env.REACT_APP_API_URL;
        }
        
        // Для контейнеризованного развертывания с nginx используем текущий origin
        return window.location.origin;
      };

      const baseURL = getBaseURL();
      console.log('🔵 Base URL:', baseURL);

      // Отправляем код авторизации на сервер для обмена на токен
      console.log('🔵 Отправляем код на Django сервер...');
      const endpoint = `${baseURL}/api/accounts/users/google_login/`;
      console.log('🔵 Endpoint:', endpoint);
      
      const requestBody = {
        code,
        redirect_uri: `${window.location.origin}/auth/google/callback`
      };
      console.log('🔵 Тело запроса:', {
        code: `${code.substring(0, 20)}...`,
        redirect_uri: requestBody.redirect_uri
      });
      
      const apiResponse = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('🔵 Ответ Django сервера:', {
        status: apiResponse.status,
        statusText: apiResponse.statusText,
        ok: apiResponse.ok,
        headers: Object.fromEntries(apiResponse.headers.entries())
      });
      
      if (!apiResponse.ok) {
        const errorText = await apiResponse.text();
        console.error('🔴 Ошибка Django сервера:', errorText);
        
        let errorData;
        try {
          errorData = JSON.parse(errorText);
          console.error('🔴 Ошибка сервера (JSON):', errorData);
        } catch (parseError) {
          console.error('🔴 Не удалось распарсить ошибку как JSON:', parseError);
          errorData = { error: errorText };
        }
        
        throw new Error(errorData.error || `Ошибка сервера: ${apiResponse.status}`);
      }

      const responseText = await apiResponse.text();
      console.log('🔵 Ответ Django сервера (текст):', responseText);
      
      let data;
      try {
        data = JSON.parse(responseText);
        console.log('🟢 Успешный ответ Django сервера:', data);
      } catch (parseError) {
        console.error('🔴 Не удалось распарсить ответ как JSON:', parseError);
        throw new Error('Неверный формат ответа сервера');
      }
      
      // Сохраняем токен в localStorage
      if (data.token) {
        localStorage.setItem('token', data.token);
        console.log('🟢 Токен сохранен в localStorage');
      } else {
        console.error('🔴 Токен не найден в ответе сервера');
      }
      
      // Вызываем onGoogleLogin callback
      if (onGoogleLogin) {
        console.log('🔵 Вызываем onGoogleLogin callback');
        await onGoogleLogin(data);
        console.log('🟢 Google OAuth завершен успешно!');
      }

      // Очищаем URL и возвращаемся на исходную страницу
      const returnUrl = localStorage.getItem('oauth_return_url') || '/account';
      localStorage.removeItem('oauth_return_url');
      window.history.replaceState({}, document.title, returnUrl);

    } catch (error) {
      console.error('🔴 Google OAuth callback ошибка:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      setError(error.message || 'Ошибка обработки Google OAuth');
    } finally {
      setIsLoading(false);
    }
  };

  // const handleOpenTelegramBot = () => {
  //   // Открываем Telegram-бота в новой вкладке
  //   window.open('https://t.me/GuschaBot', '_blank');
  // };

  const handleInputChange = (field, value) => {
    setLoginData(prev => ({ ...prev, [field]: value }));
    if (error) setError(''); // Очищаем ошибку при изменении полей
  };



  if (mode === 'telegram-verify' && registrationResult) {
    return (
      <TelegramVerification
        verificationId={registrationResult.verification_id}
        phoneNumber={originalRegistrationData?.phone}
        onVerificationComplete={handleTelegramVerificationComplete}
        onBack={handleBackToRegistration}
      />
    );
  }

  if (mode === 'qr-verify' && registrationResult) {
    return (
      <QRCodeVerification
        userData={{
          ...originalRegistrationData,
          verification_id: registrationResult.verification_id
        }}
        onVerificationComplete={handleTelegramVerificationComplete}
        onBack={handleBackToRegistration}
      />
    );
  }

  if (mode === 'register') {
    return (
      <AdvancedRegistration
        onRegister={handleRegistrationSuccess}
        onSwitchToLogin={() => setMode('login')}
      />
    );
  }

  return (
    <div className="advanced-auth">
      <div className="auth-container">
        <div className="auth-header">
          <h1>Вход в аккаунт</h1>
          <p>Введите ваши данные для входа</p>
        </div>

        <form className="auth-form" onSubmit={handleLoginSubmit}>
          {error && (
            <div className="error-banner">
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <div className="input-with-icon">
              <FiMail className="input-icon" />
              <input
                type="text"
                className="form-input"
                value={loginData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                placeholder="Email или номер телефона"
                disabled={isLoading}
                autoComplete="username"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <div className="input-with-icon">
              <FiLock className="input-icon" />
              <input
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                value={loginData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                placeholder="Пароль"
                disabled={isLoading}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
                aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="auth-btn primary"
            disabled={isLoading || !loginData.email || !loginData.password}
          >
            {isLoading ? (
              <>
                <div className="btn-spinner" />
                Вход...
              </>
            ) : (
              'Войти'
            )}
          </button>
        </form>

        <div className="divider">
          <span>или</span>
        </div>

        <div className="auth-buttons-container">
          <button
            className="auth-btn google"
            onClick={() => handleGoogleLogin()}
            disabled={isLoading}
          >
            <FcGoogle size={20} />
            Войти через Google
          </button>
          
          <button
            className="auth-btn telegram"
            onClick={() => handleTelegramLogin()}
            disabled={isLoading}
          >
            <SiTelegram size={20} />
            Войти через TG
          </button>
        </div>

        <div className="auth-footer">
          <p>
            Нет аккаунта?{' '}
            <button
              type="button"
              className="link-btn"
              onClick={() => setMode('register')}
              disabled={isLoading}
            >
              Зарегистрироваться
            </button>
          </p>
        </div>
      </div>
      
      {/* Модальное окно для входа через Telegram */}
      <TelegramLoginModal
        isOpen={showTelegramModal}
        onClose={handleCloseTelegramModal}
        onSubmit={handleTelegramPhoneSubmit}
        isLoading={telegramLoginLoading}
      />
    </div>
  );
};

export default AdvancedAuth;