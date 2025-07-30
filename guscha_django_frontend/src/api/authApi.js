import axios from './axiosInstance';

export async function login(email, password) {
  const { data } = await axios.post('/api/accounts/users/login/', { email, password }, { withCredentials: true });
  // Сохраняем токен в localStorage
  localStorage.setItem('token', data.token);
  return data;
}

export async function register(userData) {
  const { data } = await axios.post('/api/accounts/users/', userData, { withCredentials: true });
  // Сохраняем токен в localStorage
  localStorage.setItem('token', data.token);
  // Ожидаем, что сервер вернет verification_id для Telegram-верификации
  return data;
}

export async function fetchProfile() {
  const { data } = await axios.get('/api/accounts/users/me/', { withCredentials: true });
  return data;
}

export async function logout() {
  await axios.post('/api/accounts/users/logout/', {}, { withCredentials: true });
  // Удаляем токен из localStorage
  localStorage.removeItem('token');
}

export async function changePassword(oldPassword, newPassword) {
  const { data } = await axios.put('/api/accounts/users/change_password/', {
    old_password: oldPassword,
    new_password: newPassword,
    new_password_confirm: newPassword
  }, { withCredentials: true });
  
  // Обновляем токен в localStorage
  if (data.token) {
    localStorage.setItem('token', data.token);
  }
  
  return data;
}

// Запрос на сброс пароля
export async function requestPasswordReset(email) {
  const { data } = await axios.post('/api/accounts/password-reset/', { email });
  return data;
}

// Подтверждение сброса пароля
export async function confirmPasswordReset(uid, token, newPassword) {
  const { data } = await axios.post('/api/accounts/password-reset-confirm/', {
    uid,
    token,
    new_password: newPassword
  });
  return data;
}

export async function getCsrfToken() {
  // В Django CSRF токен автоматически добавляется в cookies как 'csrftoken'
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken') {
      return value;
    }
  }
  return null;
}

// Telegram-интеграция
export async function checkTelegramBotStatus(verificationId) {
  const { data } = await axios.get('/api/accounts/telegram/status/', {
    params: { verification_id: verificationId }
  });
  return data;
}

export async function activateTelegramBot(verificationId, telegramChatId, telegramUsername) {
  const { data } = await axios.post('/api/accounts/telegram/activate/', {
    verification_id: verificationId,
    telegram_chat_id: telegramChatId,
    telegram_username: telegramUsername
  });
  return data;
}

export async function verifyTelegramCode(phoneNumber, code) {
  const { data } = await axios.post('/api/accounts/telegram/verify/', {
    phone_number: phoneNumber,
    verification_code: code
  });
  return data;
}

export async function requestTelegramPasswordReset(email) {
  const { data } = await axios.post('/api/accounts/telegram/password-reset/', {
    email
  });
  return data;
}

export async function confirmTelegramPasswordReset(verificationId, code, newPassword) {
  const { data } = await axios.post('/api/accounts/telegram/password-reset-confirm/', {
    verification_id: verificationId,
    code,
    new_password: newPassword
  });
  return data;
}