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

export async function getCsrfToken() {
  // В Django CSRF токен автоматически добавляется в cookies как 'csrftoken'
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken') {
      return value;
    }
  }
  return null;
}