import axios from './axiosInstance';

// Получение списка избранных товаров
export async function fetchWishlist() {
  const { data } = await axios.get('/api/wishlist/');
  return data;
}

// Добавление товара в избранное
export async function addToWishlist(productId) {
  const { data } = await axios.post('/api/wishlist/add/', { product: productId });
  return data;
}

// Удаление товара из избранного
export async function removeFromWishlist(productId) {
  const { data } = await axios.delete(`/api/wishlist/remove/${productId}/`);
  return data;
}

// Проверка, находится ли товар в избранном
export async function checkInWishlist(productId) {
  try {
    const { data } = await axios.get(`/api/wishlist/check/${productId}/`);
    return data.in_wishlist;
  } catch (error) {
    console.error('Error checking wishlist status:', error);
    return false;
  }
}

// Очистка всего списка избранного
export async function clearWishlist() {
  const { data } = await axios.post('/api/wishlist/clear/');
  return data;
}