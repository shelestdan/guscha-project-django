import axios from './axiosInstance';

/**
 * API функции для работы с адресами доставки
 */

/**
 * Получение списка адресов пользователя
 * @returns {Promise<Array>} Список адресов
 */
export const fetchUserAddresses = async () => {
  try {
    const { data } = await axios.get('/api/addresses/');
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Добавление нового адреса
 * @param {Object} addressData - Данные адреса
 * @returns {Promise<Object>} Созданный адрес
 */
export const addUserAddress = async (addressData) => {
  try {
    const { data } = await axios.post('/api/addresses/', addressData);
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Обновление существующего адреса
 * @param {number} addressId - ID адреса
 * @param {Object} addressData - Обновленные данные адреса
 * @returns {Promise<Object>} Обновленный адрес
 */
export const updateUserAddress = async (addressId, addressData) => {
  try {
    const { data } = await axios.put(`/api/addresses/${addressId}/`, addressData);
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Удаление адреса
 * @param {number} addressId - ID адреса
 * @returns {Promise<boolean>} Результат операции
 */
export const deleteUserAddress = async (addressId) => {
  try {
    await axios.delete(`/api/addresses/${addressId}/`);
    return true;
  } catch (error) {
    throw error;
  }
};

/**
 * Установка адреса по умолчанию
 * @param {number} addressId - ID адреса
 * @returns {Promise<Object>} Обновленный адрес
 */
export const setDefaultAddress = async (addressId) => {
  try {
    const { data } = await axios.post(`/api/addresses/${addressId}/set_default/`);
    return data;
  } catch (error) {
    throw error;
  }
};
