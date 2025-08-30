import { useState, useEffect, useCallback } from 'react';

/**
 * Хук для управления аутентификацией пользователя
 * Обрабатывает вход, регистрацию, выход и обновление токенов
 */
export const useAuth = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [csrfToken, setCsrfToken] = useState(null);

  // Обновление токена доступа
  const refreshAccessToken = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return null;

      // Определяем тип токена и соответствующий заголовок
      const authHeader = token.includes('.') ? `Bearer ${token}` : `Token ${token}`;

      const response = await fetch(
        'http://localhost/api/accounts/users/me/',
        {
          method: 'GET',
          headers: {
            Authorization: authHeader
          },
          credentials: 'include'
        }
      );

      if (response.ok) {
        return token;
      } else {
        localStorage.removeItem('token');
        setIsLoggedIn(false);
        setUser(null);
        return null;
      }
    } catch (error) {
      console.error('Ошибка обновления токена:', error);
      return null;
    }
  };

  // Выполнение запросов с аутентификацией
  const fetchWithAuth = async (url, options = {}) => {
    let token = localStorage.getItem('token');

    const makeRequest = async (authToken) => {
      if (!authToken) {
        throw new Error('No auth token available');
      }
      // Определяем тип токена и соответствующий заголовок
      const authHeader = authToken.includes('.') ? `Bearer ${authToken}` : `Token ${authToken}`;
      
      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: authHeader,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });
    };

    try {
      let response = await makeRequest(token);

      if (response && response.status === 401) {
        token = await refreshAccessToken();
        if (token) {
          response = await makeRequest(token);
        }
      }

      return response;
    } catch (error) {
      throw error;
    }
  };

  // Получение профиля пользователя
  const fetchUserProfile = useCallback(async () => {
    try {
      const response = await fetchWithAuth(
        'http://localhost/api/accounts/users/me/'
      );

      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setIsLoggedIn(true);
      } else {
        localStorage.removeItem('token');
        setIsLoggedIn(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Ошибка получения профиля:', error);
      localStorage.removeItem('token');
      setIsLoggedIn(false);
      setUser(null);
    }
  }, []);

  // Инициализация аутентификации
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Получаем CSRF токен из cookie
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
          const [name, value] = cookie.trim().split('=');
          if (name === 'csrftoken') {
            setCsrfToken(value);
            break;
          }
        }

        // Проверяем токен доступа
        const token = localStorage.getItem('token');
        if (token) {
          await fetchUserProfile();
        }
      } catch (error) {
        console.error('Ошибка инициализации:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, [fetchUserProfile]);

  // Обработка входа
  const handleLogin = async (loginData) => {
    try {
      const response = await fetch(
        'http://localhost/api/accounts/users/login/',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
          },
          credentials: 'include',
          body: JSON.stringify(loginData)
        }
      );

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.token);
        setUser(data.user);
        setIsLoggedIn(true);
      } else {
        throw new Error(data.detail || data.message || 'Ошибка входа');
      }
    } catch (error) {
      throw error;
    }
  };

  // Обработка регистрации
  const handleRegister = async (registrationData) => {
    try {
      const response = await fetch(
        'http://localhost/api/accounts/users/',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
          },
          credentials: 'include',
          body: JSON.stringify(registrationData)
        }
      );

      const data = await response.json();

      if (response.ok) {
        // Обработка случаев с Telegram-верификацией или повторной регистрацией
        const pendingRegistrationId = 
          data.pending_registration_id || response.existing_pending_id;
        if (pendingRegistrationId) {
          return {
            success: true,
            needsTelegramVerification: true,
            pending_registration_id: pendingRegistrationId,
            // Для обратной совместимости с компонентами
            verification_id: pendingRegistrationId,
            user: data.user
          };
        }
        
        // Обычная регистрация без Telegram-верификации
        localStorage.setItem('token', data.token);
        setUser(data.user);
        setIsLoggedIn(true);
        return {
          success: true,
          needsTelegramVerification: false
        };
      } else {
        const error = new Error(
          data.detail || data.message || 'Ошибка регистрации'
        );
        error.response = { data };
        throw error;
      }
    } catch (error) {
      throw error;
    }
  };

  // Обработка выхода
  const handleLogout = async () => {
    try {
      await fetch('http://localhost/api/accounts/users/logout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
          Authorization: `Token ${localStorage.getItem('token')}`
        },
        credentials: 'include'
      });
    } catch (error) {
      console.error('Ошибка при выходе из системы:', error);
    } finally {
      localStorage.removeItem('token');
      setIsLoggedIn(false);
      setUser(null);
    }
  };

  // Активация Telegram-бота
  const activateTelegramBot = async (verificationId, telegramChatId) => {
    try {
      const response = await fetch(
        'http://localhost/api/accounts/telegram/activate/',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
          },
          credentials: 'include',
          body: JSON.stringify({
            verification_id: verificationId,
            telegram_chat_id: telegramChatId
          })
        }
      );

      const data = await response.json();

      if (response.ok) {
        return { success: true, data };
      } else {
        throw new Error(data.detail || data.message || 'Ошибка активации бота');
      }
    } catch (error) {
      throw error;
    }
  };

  // Верификация Telegram-кода
  const verifyTelegramCode = async (phoneNumber, code) => {
    try {
      const response = await fetch(
        'http://localhost/api/accounts/telegram/verify/',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
          },
          credentials: 'include',
          body: JSON.stringify({
            phone_number: phoneNumber,
            verification_code: code
          })
        }
      );

      const data = await response.json();

      if (response.ok) {
        // После успешной верификации устанавливаем пользователя как авторизованного
        console.log('Ответ сервера при верификации Telegram:', data);
        
        // Если требуется регистрация, не устанавливаем токен и не логиним пользователя
        if (data.requires_registration) {
          return { success: true, ...data };
        }
        
        // Проверяем различные возможные поля для токена
        const token = data.access_token || data.token || data.access;
        if (token) {
          localStorage.setItem('token', token);
          console.log('Telegram-верификация завершена:', data.user || data);
          // Если есть refresh_token, сохраняем и его
          if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token);
          }
          setUser(data.user || data);
          setIsLoggedIn(true);
        }
        
        return { success: true, ...data };
      } else {
        throw new Error(data.detail || data.message || 'Ошибка верификации кода');
      }
    } catch (error) {
      throw error;
    }
  };

  // Кастомная функция для установки пользователя с обновлением состояния входа
  const setUserWithLogin = (userData) => {
    setUser(userData);
    setIsLoggedIn(!!userData); // true если userData не null/undefined
  };

  return {
    user,
    setUser: setUserWithLogin,
    setUserWithLogin,
    loading,
    isLoggedIn,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    fetchUserProfile,
    apiRequest: fetchWithAuth,
    activateTelegramBot,
    verifyTelegramCode
  };
};