import axios from 'axios';
import { toast } from 'react-toastify';
import { getCartSessionId } from '../utils/cartSession';

// Автоматическое определение baseURL в зависимости от того, откуда загружен фронтенд
const getBaseURL = () => {
  const currentHost = window.location.host;
  const currentProtocol = window.location.protocol;
  
  // Если фронтенд загружен с Django-сервера (порт 8000), используем его же для API
  if (currentHost.includes(':8000')) {
    return `${currentProtocol}//${currentHost}`;
  }
  
  // Если фронтенд на development сервере (порт 3000), используем Nginx на 80
  if (currentHost.includes(':3000')) {
    return 'http://localhost';
  }
  
  // По умолчанию используем localhost (Nginx на порту 80)
  return 'http://localhost';
};

const instance = axios.create({
  baseURL: getBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Важно для передачи cookies с CSRF токенами
});

// 🔒 Функция для получения CSRF токена из cookies (Django использует имя 'csrftoken')
function getCSRFToken() {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken') {
      return value;
    }
  }
  return null;
}

// Добавляем токены ко всем запросам
instance.interceptors.request.use((config) => {
  // Добавляем токен аутентификации из localStorage
  const token = localStorage.getItem('token');
  if (token) {
    // Проверяем, является ли токен JWT (содержит точки) или обычным Django Token
    if (token.includes('.')) {
      // JWT токен - используем Bearer
      config.headers['Authorization'] = `Bearer ${token}`;
    } else {
      // Обычный Django Token
      config.headers['Authorization'] = `Token ${token}`;
    }
  }
  
  // 🔒 CSRF защита: добавляем CSRF токен для всех небезопасных запросов
  if (['post', 'put', 'delete', 'patch'].includes(config.method?.toLowerCase())) {
    const csrfToken = getCSRFToken();
    
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
      if (process.env.NODE_ENV === 'development') {
        console.log('🔒 CSRF токен добавлен к запросу');
      }
    } else {
      console.warn('⚠️ CSRF токен не найден');
    }
  }
  
  // Добавляем cart session ID для всех запросов к корзине
  if (config.url && config.url.includes('/api/cart/')) {
    config.headers['X-Session-ID'] = getCartSessionId();
  }
  
  return config;
});

// Глобальная обработка ошибок
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('🔥 Axios error:', error);
    
    // Не показываем toast для ошибок корзины
    if (!error.config?.url?.includes('/api/cart/')) {
      const message = error.response?.data?.detail || 
                      error.response?.data?.message || 
                      error.message || 
                      'Ошибка запроса';
      
      toast.error(message);
    }
    
    return Promise.reject(error);
  }
);

export default instance;