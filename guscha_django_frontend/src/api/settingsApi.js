import axios from './axiosInstance';

// Получение общих настроек приложения
export async function fetchAppSettings() {
  const { data } = await axios.get('/api/settings/app/');
  return data;
}

// Получение настроек магазина
export async function fetchStoreSettings() {
  const { data } = await axios.get('/api/settings/store/');
  return data;
}

// Получение информации о доставке
export async function fetchDeliveryInfo() {
  const { data } = await axios.get('/api/settings/delivery/');
  return data;
}

// Получение информации об оплате
export async function fetchPaymentInfo() {
  const { data } = await axios.get('/api/settings/payment/');
  return data;
}

// Получение текстов страниц (О нас, Условия использования и т.д.)
export async function fetchPageContent(pageSlug) {
  const { data } = await axios.get(`/api/settings/pages/${pageSlug}/`);
  return data;
}

// Получение списка всех страниц
export async function fetchAllPages() {
  const { data } = await axios.get('/api/settings/pages/');
  return data;
}

// Получение информации о социальных сетях
export async function fetchSocialLinks() {
  const { data } = await axios.get('/api/settings/social/');
  return data;
}

// Получение информации о контактах
export async function fetchContactInfo() {
  const { data } = await axios.get('/api/settings/contacts/');
  return data;
}

// Получение информации о баннерах для главной страницы
export async function fetchBanners() {
  const { data } = await axios.get('/api/settings/banners/');
  return data;
}

// Получение информации о промо-акциях
export async function fetchPromotions() {
  const { data } = await axios.get('/api/settings/promotions/');
  return data;
}