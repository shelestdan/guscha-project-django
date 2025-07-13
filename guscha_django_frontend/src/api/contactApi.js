import axios from './axiosInstance';

// Отправка сообщения через контактную форму
export async function sendContactMessage(messageData) {
  const { data } = await axios.post('/api/contact/message/', messageData);
  return data;
}

// Отправка запроса на обратный звонок
export async function requestCallback(callbackData) {
  const { data } = await axios.post('/api/contact/callback/', callbackData);
  return data;
}

// Подписка на рассылку новостей
export async function subscribeToNewsletter(email) {
  const { data } = await axios.post('/api/contact/newsletter/subscribe/', { email });
  return data;
}

// Отписка от рассылки новостей
export async function unsubscribeFromNewsletter(token) {
  const { data } = await axios.post('/api/contact/newsletter/unsubscribe/', { token });
  return data;
}

// Отправка отзыва о работе магазина
export async function sendFeedback(feedbackData) {
  const { data } = await axios.post('/api/contact/feedback/', feedbackData);
  return data;
}

// Получение часто задаваемых вопросов (FAQ)
export async function fetchFAQ() {
  const { data } = await axios.get('/api/contact/faq/');
  return data;
}