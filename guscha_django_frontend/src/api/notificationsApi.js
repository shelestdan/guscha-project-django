import axios from './axiosInstance';

// Получение всех уведомлений пользователя
export async function fetchNotifications(params = {}) {
  const { data } = await axios.get('/api/notifications/', { params });
  return data;
}

// Получение количества непрочитанных уведомлений
export async function fetchUnreadCount() {
  const { data } = await axios.get('/api/notifications/unread-count/');
  return data;
}

// Отметка уведомления как прочитанного
export async function markAsRead(notificationId) {
  const { data } = await axios.post(`/api/notifications/${notificationId}/read/`);
  return data;
}

// Отметка всех уведомлений как прочитанных
export async function markAllAsRead() {
  const { data } = await axios.post('/api/notifications/read-all/');
  return data;
}

// Удаление уведомления
export async function deleteNotification(notificationId) {
  await axios.delete(`/api/notifications/${notificationId}/`);
  return true;
}

// Удаление всех уведомлений
export async function deleteAllNotifications() {
  await axios.delete('/api/notifications/delete-all/');
  return true;
}

// Настройка предпочтений уведомлений
export async function updateNotificationPreferences(preferences) {
  const { data } = await axios.put('/api/notifications/preferences/', preferences);
  return data;
}

// Получение текущих настроек уведомлений
export async function fetchNotificationPreferences() {
  const { data } = await axios.get('/api/notifications/preferences/');
  return data;
}