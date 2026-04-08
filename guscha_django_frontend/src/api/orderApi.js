import axios from './axiosInstance';

/**
 * API функции для работы с заказами
 */

/**
 * Получение списка заказов пользователя
 * @returns {Promise<Array>} Список заказов
 */
export const fetchUserOrders = async () => {
  try {
    const { data } = await axios.get('/api/orders/');
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Получение детальной информации о заказе
 * @param {number} orderId - ID заказа
 * @returns {Promise<Object>} Детали заказа
 */
export const fetchOrderDetails = async (orderId) => {
  try {
    const { data } = await axios.get(`/api/orders/${orderId}/`);
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Создание нового заказа
 * @param {Object} orderData - Данные заказа
 * @returns {Promise<Object>} Созданный заказ
 */
export const createOrder = async (orderData) => {
  try {
    const { data } = await axios.post('/api/orders/', orderData);
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Отмена заказа
 * @param {number} orderId - ID заказа
 * @returns {Promise<Object>} Обновленный заказ
 */
export const cancelOrder = async (orderId) => {
  try {
    const { data } = await axios.post(`/api/orders/${orderId}/cancel/`);
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Получение истории статусов заказа
 * @param {number} orderId - ID заказа
 * @returns {Promise<Array>} История статусов
 */
export const fetchOrderStatusHistory = async (orderId) => {
  try {
    const { data } = await axios.get(`/api/orders/${orderId}/status-history/`);
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Повторный заказ (создание нового заказа на основе существующего)
 * @param {number} orderId - ID исходного заказа
 * @returns {Promise<Object>} Новый заказ
 */
export const reorderOrder = async (orderId) => {
  try {
    const { data } = await axios.post(`/api/orders/${orderId}/reorder/`);
    return data;
  } catch (error) {
    throw error;
  }
};