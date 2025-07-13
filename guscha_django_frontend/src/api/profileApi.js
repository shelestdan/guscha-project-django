import axios from './axiosInstance';

// Получение профиля пользователя
export async function fetchUserProfile() {
  const { data } = await axios.get('/api/accounts/users/me/');
  return data;
}

// Обновление профиля пользователя
export async function updateUserProfile(profileData) {
  const { data } = await axios.put('/api/accounts/users/me/', profileData);
  return data;
}

// Обновление аватара пользователя
export async function updateUserAvatar(formData) {
  const { data } = await axios.post('/api/accounts/users/me/avatar/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
}

// Получение адресов пользователя
export async function fetchUserAddresses() {
  const { data } = await axios.get('/api/accounts/addresses/');
  return data;
}

// Добавление нового адреса
export async function addUserAddress(addressData) {
  const { data } = await axios.post('/api/accounts/addresses/', addressData);
  return data;
}

// Обновление существующего адреса
export async function updateUserAddress(addressId, addressData) {
  const { data } = await axios.put(`/api/accounts/addresses/${addressId}/`, addressData);
  return data;
}

// Удаление адреса
export async function deleteUserAddress(addressId) {
  await axios.delete(`/api/accounts/addresses/${addressId}/`);
  return true;
}

// Установка адреса по умолчанию
export async function setDefaultAddress(addressId) {
  const { data } = await axios.post(`/api/accounts/addresses/${addressId}/set_default/`);
  return data;
}