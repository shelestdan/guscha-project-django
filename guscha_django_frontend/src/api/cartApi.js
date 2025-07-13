import axios from './axiosInstance';

export async function getCartItems() {
  console.log('🛒 cartApi.getCartItems called');
  const sessionId = localStorage.getItem('cart_session_id');
  console.log('🛒 Frontend session ID:', sessionId);

  try {
    // 1. Получаем основную информацию о корзине
    const { data: cartData } = await axios.get('/api/cart/items/');
    console.log('🛒 cartApi.getCartItems response:', cartData);
    return cartData;
  } catch (error) {
    console.error('🛒 Error in getCartItems:', error);
    throw error;
  }
}

export async function addCartItem(productId, quantity = 1, sizeId = null) {
  const requestData = { product: productId, quantity };
  if (sizeId) {
    requestData.size = sizeId;
  }
  const sessionId = localStorage.getItem('cart_session_id');
  console.log('🛒 cartApi.addCartItem request:', requestData);
  console.log('🛒 Frontend session ID for POST:', sessionId);

  try {
    const { data } = await axios.post('/api/cart/add/', requestData);
    console.log('🛒 cartApi.addCartItem response:', data);
    return data;
  } catch (error) {
    console.error('🛒 Error in addCartItem:', error);
    throw error;
  }
}

export async function addPreorderItem(preorderId, quantity = 1, sizeId = null) {
  const requestData = { preorder: preorderId, quantity };
  if (sizeId) {
    requestData.size = sizeId;
  }
  const sessionId = localStorage.getItem('cart_session_id');
  console.log('🛒 cartApi.addPreorderItem request:', requestData);
  console.log('🛒 Frontend session ID for POST:', sessionId);

  try {
    const { data } = await axios.post('/api/cart/add_preorder/', requestData);
    console.log('🛒 cartApi.addPreorderItem response:', data);
    return data;
  } catch (error) {
    console.error('🛒 Error in addPreorderItem:', error);
    throw error;
  }
}

export async function updateCartItem(itemId, quantity) {
  console.log(`🛒 cartApi.updateCartItem called for item ${itemId} with quantity ${quantity}`);

  try {
    const { data } = await axios.put(`/api/cart/update/${itemId}/`, { quantity });
    console.log('🛒 cartApi.updateCartItem response:', data);
    return data;
  } catch (error) {
    console.error('🛒 Error in updateCartItem:', error);
    if (error.response?.status === 404) {
      console.error(`🛒 Cart item with ID ${itemId} not found`);
      throw new Error(`Товар в корзине с ID ${itemId} не найден`);
    }
    throw error;
  }
}

export async function removeCartItem(itemId) {
  console.log(`🛒 cartApi.removeCartItem called for item ${itemId}`);

  try {
    const { data } = await axios.delete(`/api/cart/remove/${itemId}/`);
    console.log('🛒 cartApi.removeCartItem response:', data);
    return data;
  } catch (error) {
    console.error('🛒 Error in removeCartItem:', error);
    if (error.response?.status === 404) {
      console.error(`🛒 Cart item with ID ${itemId} not found - may already be removed`);
      // Не выбрасываем ошибку, так как элемент уже удален
      return { message: 'Item already removed' };
    }
    throw error;
  }
}

export async function clearCart() {
  console.log('🛒 cartApi.clearCart called');

  try {
    const { data } = await axios.post('/api/cart/clear/');
    console.log('🛒 cartApi.clearCart response:', data);
    return data;
  } catch (error) {
    console.error('🛒 Error in clearCart:', error);
    throw error;
  }
}

// Заглушки для промокодов - временно отключены, так как backend не реализует эти endpoints
export async function applyPromoCode(code) {
  console.log('🛒 cartApi.applyPromoCode called with code:', code);
  throw new Error('Промокоды временно недоступны');
}

export async function removePromoCode() {
  console.log('🛒 cartApi.removePromoCode called');
  throw new Error('Промокоды временно недоступны');
}

export async function getAvailablePromoCodes() {
  console.log('🛒 cartApi.getAvailablePromoCodes called');
  return [];
}

export async function validatePromoCode(code) {
  console.log('🛒 cartApi.validatePromoCode called with code:', code);
  throw new Error('Промокоды временно недоступны');
}