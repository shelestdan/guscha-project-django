import axios from './axiosInstance';

export async function login(email, password) {
  const { data } = await axios.post('/api/accounts/users/login/', { email, password });
  // Токен сохраняется в httpOnly cookie автоматически
  return data;
}

export async function register(userData) {
  try {
    const response = await axios.post('/api/accounts/users/', userData);
    // Токен сохраняется в httpOnly cookie автоматически
    // Ожидаем, что сервер вернет verification_id для Telegram-верификации
    return response.data;
  } catch (error) {
    // Обрабатываем специфичные ошибки от сервера
    if (error.response?.data) {
      const serverError = error.response.data;

      // Проверяем различные возможные форматы ошибок от Django
      let errorMessage = 'Ошибка регистрации';

      if (typeof serverError === 'string') {
        errorMessage = serverError;
      } else if (serverError.detail) {
        errorMessage = serverError.detail;
      } else if (serverError.message) {
        errorMessage = serverError.message;
      } else if (serverError.error) {
        errorMessage = serverError.error;
      } else if (serverError.non_field_errors) {
        errorMessage = Array.isArray(serverError.non_field_errors)
          ? serverError.non_field_errors.join(', ')
          : serverError.non_field_errors;
      } else {
        // Проверяем ошибки по конкретным полям
        const fieldErrors = [];
        Object.keys(serverError).forEach(field => {
          if (Array.isArray(serverError[field])) {
            fieldErrors.push(`${field}: ${serverError[field].join(', ')}`);
          } else {
            fieldErrors.push(`${field}: ${serverError[field]}`);
          }
        });
        if (fieldErrors.length > 0) {
          errorMessage = fieldErrors.join('; ');
        }
      }

      const detailedError = new Error(errorMessage);
      detailedError.response = error.response;
      detailedError.serverData = serverError;
      throw detailedError;
    }

    // Если нет данных от сервера, используем общую ошибку
    const fallbackError = new Error('Ошибка регистрации');
    fallbackError.response = error.response;
    throw fallbackError;
  }
}

export async function fetchProfile() {
  const { data } = await axios.get('/api/accounts/users/me/');
  return data;
}

export async function logout() {
  try {
    await axios.post('/api/accounts/users/logout/', {});
  } finally {
    // Токен удаляется из cookie сервером (через Set-Cookie с истекшим сроком)
  }
}

export async function changePassword(oldPassword, newPassword) {
  const { data } = await axios.put('/api/accounts/users/change_password/', {
    old_password: oldPassword,
    new_password: newPassword,
    new_password_confirm: newPassword
  });

  // Токен обновляется в cookie автоматически
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