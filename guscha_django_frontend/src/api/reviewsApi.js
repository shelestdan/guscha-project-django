import axios from './axiosInstance';

// Получение отзывов для конкретного товара
export async function fetchProductReviews(productId, params = {}) {
  const { data } = await axios.get(`/api/products/products/${productId}/reviews/`, { params });
  return data;
}

// Добавление нового отзыва
export async function addProductReview(productId, reviewData) {
  const { data } = await axios.post(`/api/products/products/${productId}/reviews/`, reviewData);
  return data;
}

// Обновление существующего отзыва
export async function updateProductReview(productId, reviewId, reviewData) {
  const { data } = await axios.put(`/api/products/products/${productId}/reviews/${reviewId}/`, reviewData);
  return data;
}

// Удаление отзыва
export async function deleteProductReview(productId, reviewId) {
  await axios.delete(`/api/products/products/${productId}/reviews/${reviewId}/`);
  return true;
}

// Получение всех отзывов пользователя
export async function fetchUserReviews(params = {}) {
  const { data } = await axios.get('/api/accounts/users/me/reviews/', { params });
  return data;
}

// Голосование за отзыв (полезный/неполезный)
export async function voteReview(productId, reviewId, isHelpful) {
  const { data } = await axios.post(`/api/products/products/${productId}/reviews/${reviewId}/vote/`, {
    is_helpful: isHelpful
  });
  return data;
}