import { useState } from 'react';

export const useNotification = () => {
  const [notification, setNotification] = useState(null);

  const showNotification = (type, title, message) => {
    setNotification({ type, title, message });
  };

  const hideNotification = () => {
    setNotification(null);
  };

  return { notification, showNotification, hideNotification };
};