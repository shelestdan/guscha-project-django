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
  
  // Если работаем через nginx (порт 80 или без порта), используем текущий хост
  if (currentHost === 'localhost' || currentHost.includes(':80') || !currentHost.includes(':')) {
    return `${currentProtocol}//${currentHost}`;
  }
  
  // По умолчанию используем localhost:8000
  return 'http://localhost:8000';
};

// Создаем глобальную конфигурацию для axios
window.axiosConfig = {
  baseURL: getBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true
};

// Функция для получения CSRF токена из cookies
function getCSRFToken() {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

window.getCSRFToken = getCSRFToken;
window.getBaseURL = getBaseURL;











