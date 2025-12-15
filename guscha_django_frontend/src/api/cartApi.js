import axios from './axiosInstance';

export async function getCartItems() {
  const sessionId = localStorage.getItem('cart_session_id');

  const headers = {};
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  try {
    // 1. Получаем основную информацию о корзине
    const { data: cartData } = await axios.get('/api/cart/items/', { headers });
    return cartData;
  } catch (error) {
    throw error;
  }
}

export async function addCartItem(productId, quantity = 1, sizeId = null) {
  const requestData = { product: productId, quantity };
  if (sizeId) {
    requestData.size = sizeId;
  }
  const sessionId = localStorage.getItem('cart_session_id');

  const headers = {};
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  try {
    const { data } = await axios.post('/api/cart/add/', requestData, { headers });
    return data;
  } catch (error) {
    throw error;
  }
}

export async function addPreorderItem(preorderId, quantity = 1, sizeId = null) {
  const requestData = { preorder: preorderId, quantity };
  if (sizeId) {
    requestData.size = sizeId;
  }
  const sessionId = localStorage.getItem('cart_session_id');

  const headers = {};
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  try {
    const { data } = await axios.post('/api/cart/add_preorder/', requestData, { headers });
    return data;
  } catch (error) {
    throw error;
  }
}

export async function updateCartItem(itemId, quantity) {
  const sessionId = localStorage.getItem('cart_session_id');

  const headers = {};
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  try {
    const { data } = await axios.put(`/api/cart/update/${itemId}/`, { quantity }, { headers });
    return data;
  } catch (error) {
    if (error.response?.status === 404) {
      throw new Error(`Товар в корзине с ID ${itemId} не найден`);
    }
    throw error;
  }
}

export async function removeCartItem(itemId) {
  const sessionId = localStorage.getItem('cart_session_id');

  const headers = {};
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  try {
    const { data } = await axios.delete(`/api/cart/remove/${itemId}/`, { headers });
    return data;
  } catch (error) {
    if (error.response?.status === 404) {
      // Не выбрасываем ошибку, так как элемент уже удален
      return { message: 'Item already removed' };
    }
    throw error;
  }
}

export async function clearCart() {
  const sessionId = localStorage.getItem('cart_session_id');

  const headers = {};
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  try {
    const { data } = await axios.delete('/api/cart/clear/', { headers });
    return data;
  } catch (error) {
    throw error;
  }
}

export async function createCartReservations() {
  const sessionId = localStorage.getItem('cart_session_id');

  const headers = {};
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  try {
    const { data } = await axios.post('/api/cart/create-reservations/', {}, { headers });
    return data;
  } catch (error) {
    throw error;
  }
}

// Заглушки для промокодов - временно отключены, так как backend не реализует эти endpoints
export async function applyPromoCode(code) {
  throw new Error('Промокоды временно недоступны');
}

export async function removePromoCode() {
  throw new Error('Промокоды временно недоступны');
}

export async function getAvailablePromoCodes() {
  return [];
}

export async function validatePromoCode(code) {
  throw new Error('Промокоды временно недоступны');
}
