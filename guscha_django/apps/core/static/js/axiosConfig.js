// Автоматическое определение baseURL в зависимости от того, откуда загружен фронтенд
const getBaseURL = () => {
  const currentHost = window.location.host;
  const currentProtocol = window.location.protocol;
  
  // Если фронтенд загружен с Django-сервера (порт 8000), используем его же для API
  if (currentHost.includes(':8000')) {
    return `${currentProtocol}//${currentHost}`;
  }
  
  // Если фронтенд на development сервере (порт 3000), используем Django на 8000
  if (currentHost.includes(':3000')) {
    return 'http://localhost:8000';
  }
  
  // По умолчанию используем localhost:8000
  return 'http://localhost:8000';
};

// Настройка axios
axios.defaults.baseURL = getBaseURL();
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.withCredentials = true;

// Функция для получения CSRF токена из cookies (Django использует имя 'csrftoken')
function getCSRFToken() {
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken') {
      return value;
    }
  }
  return null;
}

// Функция для получения ID сессии корзины
function getCartSessionId() {
  let cartSessionId = localStorage.getItem('cartSessionId');
  if (!cartSessionId) {
    cartSessionId = 'cart_' + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('cartSessionId', cartSessionId);
  }
  return cartSessionId;
}

// Добавляем токены ко всем запросам
axios.interceptors.request.use((config) => {
  // Добавляем токен аутентификации из localStorage
  const token = localStorage.getItem('token');
  if (token) {
    config.headers['Authorization'] = `Token ${token}`;
  }
  
  // CSRF защита: добавляем CSRF токен для всех небезопасных запросов
  if (['post', 'put', 'delete', 'patch'].includes(config.method?.toLowerCase())) {
    const csrfToken = getCSRFToken();
    
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    } else {
      console.warn('⚠️ CSRF токен не найден');
    }
  }
  
  // Добавляем cart session ID для всех запросов к корзине
  if (config.url && config.url.includes('/api/cart/')) {
    config.headers['X-Cart-Session-ID'] = getCartSessionId();
  }
  
  return config;
});

// Глобальная обработка ошибок
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('🔥 Axios error:', error);
    
    const message = error.response?.data?.detail || 
                    error.response?.data?.message || 
                    error.message || 
                    'Ошибка запроса';
    
    console.error(message);
    
    return Promise.reject(error);
  }
);