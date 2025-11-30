import axios from 'axios';
import { toast } from 'react-toastify';
import { getCartSessionId } from '../utils/cartSession';

// Автоматическое определение baseURL для работы с nginx в контейнере
const getBaseURL = () => {
  // Проверяем переменную окружения
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }

  // Для контейнеризованного развертывания с nginx используем текущий origin
  // Это работает как для разработки, так и для продакшена
  return window.location.origin;
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
  // Добавляем JWT токен если он есть в localStorage
  const accessToken = localStorage.getItem('access_token');
  if (accessToken) {
    config.headers['Authorization'] = `Bearer ${accessToken}`;
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

    // Не показываем toast для ошибок корзины и регистрации (обрабатываются отдельно)
    if (!error.config?.url?.includes('/api/cart/') &&
      !error.config?.url?.includes('/api/accounts/users/')) {
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