import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import axios from '../api/axiosInstance';

const GoogleOAuthCallback = () => {
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState('');
  const [processingStep, setProcessingStep] = useState('Получение кода авторизации...');
  const [retryCount, setRetryCount] = useState(0);
  const navigate = useNavigate();
  const authHook = useAuth();
  const toastHook = useToast();
  const hasProcessed = useRef(false);
  const abortController = useRef(null);

  useEffect(() => {
    const handleCallback = async (attempt = 1) => {
      // Предотвращаем повторные вызовы
      if (hasProcessed.current) {
        return;
      }

      try {
        setProcessingStep(`Обработка авторизации (попытка ${attempt})...`);

        // Получаем параметры из URL
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const errorParam = urlParams.get('error');

        if (errorParam) {
          throw new Error(`Google OAuth ошибка: ${errorParam}`);
        }

        if (!code) {
          throw new Error('Код авторизации не получен от Google');
        }

        // Проверяем, не был ли этот код уже обработан
        const processedCode = sessionStorage.getItem('oauth_processed_code');
        if (processedCode === code) {
          setProcessingStep('Завершение авторизации...');
          // Перенаправляем на страницу аккаунта
          const returnUrl = localStorage.getItem('oauth_return_url') || '/account';
          localStorage.removeItem('oauth_return_url');
          navigate(returnUrl, { replace: true });
          return;
        }

        hasProcessed.current = true;

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

        // Отправляем код авторизации на сервер для обмена на токен
        setProcessingStep('Обмен кода на токен доступа...');

        const requestBody = {
          code,
          redirect_uri: `${window.location.origin}/auth/google/callback`
        };

        // Создаем новый AbortController для этого запроса
        const currentAbortController = new AbortController();
        abortController.current = currentAbortController;

        // Используем axios instance с автоматическим добавлением CSRF токена
        const apiResponse = await axios.post('/api/accounts/users/google_login/', requestBody, {
          signal: currentAbortController.signal,
          timeout: 10000
        });

        const data = apiResponse.data;

        // Помечаем код как обработанный
        sessionStorage.setItem('oauth_processed_code', code);

        // Токен теперь возвращается в ответе сервера
        // Сохраняем токены в localStorage для фронтенда (используем правильные ключи)
        if (data.access_token || data.token || data.access) {
          const accessToken = data.access_token || data.token || data.access;
          localStorage.setItem('access_token', accessToken);
        }
        if (data.refresh_token || data.refresh) {
          const refreshToken = data.refresh_token || data.refresh;
          localStorage.setItem('refresh_token', refreshToken);
        }

        // Обновляем состояние пользователя
        if (data.user) {
          authHook.setUserWithLogin(data.user);  // setUserWithLogin автоматически установит isLoggedIn
          setProcessingStep('Завершение авторизации...');
        }

        // Возвращаемся на исходную страницу
        const returnUrl = localStorage.getItem('oauth_return_url') || '/account';
        localStorage.removeItem('oauth_return_url');

        // Очищаем обработанный код из sessionStorage после успешного завершения
        setTimeout(() => {
          sessionStorage.removeItem('oauth_processed_code');
        }, 5000);

        // Небольшая задержка для показа успешного состояния
        setTimeout(() => {
          navigate(returnUrl, { replace: true });
        }, 1000);

      } catch (error) {
        // Проверяем, не была ли операция отменена
        if (error.name === 'AbortError') {
          return;
        }

        // Retry логика для определенных ошибок
        const isRetryableError =
          error.message.includes('Failed to exchange authorization code for token') ||
          error.message.includes('Network Error') ||
          error.message.includes('timeout') ||
          error.message.includes('fetch');

        if (isRetryableError && attempt < 3) {
          setRetryCount(attempt);
          setProcessingStep(`Повторная попытка через ${attempt * 2} сек...`);

          // Сбрасываем флаг обработки для retry
          hasProcessed.current = false;

          setTimeout(() => {
            handleCallback(attempt + 1);
          }, attempt * 2000); // Экспоненциальная задержка
          return;
        }

        // Если все попытки исчерпаны или ошибка не подлежит повтору
        hasProcessed.current = false;
        setError(error.message || 'Ошибка обработки Google OAuth');
        toastHook.showError(error.message || 'Ошибка входа через Google');
        setProcessingStep('Ошибка авторизации');

        // Возвращаемся на страницу входа при ошибке
        setTimeout(() => {
          navigate('/account', { replace: true });
        }, 3000);
      } finally {
        if (attempt >= 3 || !error || !error.message.includes('Failed to exchange')) {
          setIsProcessing(false);
        }
      }
    };

    // Cleanup function для отмены запросов при размонтировании
    const cleanup = () => {
      if (abortController.current) {
        abortController.current.abort();
      }
    };

    handleCallback();

    return cleanup;
  }, []); // Пустой массив зависимостей - выполняется только при монтировании

  if (isProcessing) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '2rem',
        textAlign: 'center'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          border: '3px solid #f3f3f3',
          borderTop: '3px solid #667eea',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: '1rem'
        }}></div>
        <h2 style={{ color: '#333', marginBottom: '0.5rem' }}>Обрабатываем вход через Google...</h2>
        <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '0.5rem' }}>{processingStep}</p>
        {retryCount > 0 && (
          <p style={{ color: '#f59e0b', fontSize: '0.8rem' }}>Попытка {retryCount + 1} из 3</p>
        )}
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '2rem',
        textAlign: 'center'
      }}>
        <div style={{
          color: '#e74c3c',
          fontSize: '3rem',
          marginBottom: '1rem'
        }}>⚠️</div>
        <h2 style={{ color: '#e74c3c', marginBottom: '1rem' }}>Ошибка входа</h2>
        <p style={{ color: '#666', marginBottom: '2rem', maxWidth: '400px' }}>{error}</p>
        <p style={{ color: '#999', fontSize: '0.9rem' }}>Перенаправление на страницу входа...</p>
      </div>
    );
  }

  return null;
};

export default GoogleOAuthCallback;