import React, { useEffect, useState, useRef } from 'react';
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
        console.log('🔵 OAuth callback уже обрабатывается, пропускаем');
        return;
      }

      try {
        console.log(`🔵 Обрабатываем Google OAuth callback (попытка ${attempt})`);
        setProcessingStep(`Обработка авторизации (попытка ${attempt})...`);
        
        // Получаем параметры из URL
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');
        const state = urlParams.get('state');
        
        if (error) {
          throw new Error(`Google OAuth ошибка: ${error}`);
        }
        
        if (!code) {
          throw new Error('Код авторизации не получен от Google');
        }

        // Проверяем, не был ли этот код уже обработан
        const processedCode = sessionStorage.getItem('oauth_processed_code');
        if (processedCode === code) {
          console.log('🔵 Этот код авторизации уже был обработан');
          setProcessingStep('Завершение авторизации...');
          // Перенаправляем на страницу аккаунта
          const returnUrl = localStorage.getItem('oauth_return_url') || '/account';
          localStorage.removeItem('oauth_return_url');
          navigate(returnUrl, { replace: true });
          return;
        }

        console.log('🔵 Получен код авторизации:', code.substring(0, 20) + '...');
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
        console.log('🔵 Base URL:', baseURL);

        // Отправляем код авторизации на сервер для обмена на токен
        console.log('🔵 Отправляем код на Django сервер...');
        setProcessingStep('Обмен кода на токен доступа...');
        
        const requestBody = {
          code: code,
          redirect_uri: `${window.location.origin}/auth/google/callback`
        };
        console.log('🔵 Тело запроса:', {
          code: code.substring(0, 20) + '...',
          redirect_uri: requestBody.redirect_uri
        });
        
        // Создаем новый AbortController для этого запроса
        const currentAbortController = new AbortController();
        abortController.current = currentAbortController;
        
        // Используем axios instance с автоматическим добавлением CSRF токена
        const apiResponse = await axios.post('/api/accounts/users/google_login/', requestBody, {
          signal: currentAbortController.signal,
          timeout: 10000
        });

        console.log('🔵 Ответ Django сервера:', {
          status: apiResponse.status,
          statusText: apiResponse.statusText,
          data: apiResponse.data
        });
        
        const data = apiResponse.data;
        console.log('🟢 Успешный ответ Django сервера:', data);
        
        // Помечаем код как обработанный
        sessionStorage.setItem('oauth_processed_code', code);
        
        // Сохраняем токен в localStorage
        if (data.token) {
          localStorage.setItem('token', data.token);
          console.log('🟢 Токен сохранен в localStorage');
          setProcessingStep('Сохранение данных пользователя...');
        } else {
          console.error('🔴 Токен не найден в ответе сервера');
        }
        
        // Обновляем состояние пользователя
        if (data.user) {
          authHook.setUser(data.user);
          toastHook.showSuccess('Вход через Google выполнен успешно!');
          console.log('🟢 Google OAuth завершен успешно!');
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
        console.error(`🔴 Google OAuth callback ошибка (попытка ${attempt}):`, {
          message: error.message,
          stack: error.stack,
          name: error.name
        });
        
        // Проверяем, не была ли операция отменена
        if (error.name === 'AbortError') {
          console.log('🔵 Запрос был отменен');
          return;
        }
        
        // Retry логика для определенных ошибок
        const isRetryableError = 
          error.message.includes('Failed to exchange authorization code for token') ||
          error.message.includes('Network Error') ||
          error.message.includes('timeout') ||
          error.message.includes('fetch');
        
        if (isRetryableError && attempt < 3) {
          console.log(`🔄 Повторная попытка через ${attempt * 2} секунд...`);
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