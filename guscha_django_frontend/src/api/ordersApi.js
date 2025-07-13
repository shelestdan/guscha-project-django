import axios from './axiosInstance';

// Получение списка заказов пользователя
export async function fetchUserOrders() {
  const { data } = await axios.get('/api/orders/');
  return data;
}

// Получение деталей конкретного заказа
export async function fetchOrderDetails(orderId) {
  const { data } = await axios.get(`/api/orders/${orderId}/`);
  return data;
}

// Создание нового заказа
export async function createOrder(orderData) {
  const { data } = await axios.post('/api/orders/', orderData);
  return data;
}

// Отмена заказа
export async function cancelOrder(orderId, reason = '') {
  const { data } = await axios.post(`/api/orders/${orderId}/cancel/`, { reason });
  return data;
}

// Получение доступных способов доставки
export async function fetchDeliveryMethods() {
  const { data } = await axios.get('/api/orders/delivery-methods/');
  return data;
}

// Получение доступных способов оплаты
export async function fetchPaymentMethods() {
  const { data } = await axios.get('/api/orders/payment-methods/');
  return data;
}

// Проверка статуса оплаты заказа
export async function checkPaymentStatus(orderId) {
  const { data } = await axios.get(`/api/orders/${orderId}/payment-status/`);
  return data;
}

// Инициирование оплаты заказа
export async function initiatePayment(orderId, paymentMethod) {
  const { data } = await axios.post(`/api/orders/${orderId}/pay/`, { payment_method: paymentMethod });
  return data;
}