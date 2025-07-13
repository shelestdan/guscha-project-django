import React from 'react';
import Toast from './Toast';
import { useToasts, useToast } from '../../hooks/useToast';

const ToastContainer = ({ position = 'top-right' }) => {
  const toasts = useToasts();
  const { removeToast } = useToast();

  return (
    <>
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          position={position}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </>
  );
};

export default ToastContainer;
