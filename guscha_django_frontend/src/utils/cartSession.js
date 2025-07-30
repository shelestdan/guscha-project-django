// Утилита для управления cart session ID
export const getCartSessionId = () => {
  let sessionId = localStorage.getItem('cart_session_id');
  if (!sessionId) {
    sessionId = generateUUID();
    localStorage.setItem('cart_session_id', sessionId);
  }
  return sessionId;
};

export const clearCartSessionId = () => {
  localStorage.removeItem('cart_session_id');
};

// Простая функция для генерации UUID
const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : ((r & 0x3) | 0x8);
    return v.toString(16);
  });
};