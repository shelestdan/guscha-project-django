import axios from './axiosInstance';

// Получение списка доступных предзаказов
export async function fetchPreorders(params = {}) {
  const { data } = await axios.get('/api/products/preorders/', { params });
  return data;
}

// Получение деталей конкретного предзаказа
export async function fetchPreorderDetails(preorderId) {
  const { data } = await axios.get(`/api/products/preorders/${preorderId}/`);
  return data;
}

// Получение доступных размеров для предзаказа
export async function fetchPreorderSizes(preorderId) {
  const { data } = await axios.get(`/api/products/preorders/${preorderId}/sizes/`);
  return data;
}

// Создание заявки на предзаказ
export async function createPreorderRequest(preorderId, requestData) {
  const { data } = await axios.post(`/api/products/preorders/${preorderId}/request/`, requestData);
  return data;
}

// Получение статуса заявки на предзаказ
export async function checkPreorderRequestStatus(requestId) {
  const { data } = await axios.get(`/api/products/preorders/requests/${requestId}/status/`);
  return data;
}

// Отмена заявки на предзаказ
export async function cancelPreorderRequest(requestId) {
  const { data } = await axios.post(`/api/products/preorders/requests/${requestId}/cancel/`);
  return data;
}

// Получение списка заявок пользователя на предзаказы
export async function fetchUserPreorderRequests() {
  const { data } = await axios.get('/api/accounts/users/me/preorder-requests/');
  return data;
}