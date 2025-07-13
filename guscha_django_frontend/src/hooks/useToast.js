import { create } from 'zustand';

const useToastStore = create((set, get) => ({
  toasts: [],
  addToast: (message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random();
    const toast = { id, message, type, duration };
    
    set((state) => ({
      toasts: [...state.toasts, toast]
    }));

    // Автоматически удаляем toast через duration
    setTimeout(() => {
      get().removeToast(id);
    }, duration + 300); // Добавляем время для анимации
  },
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter(toast => toast.id !== id)
    }));
  },
  clearToasts: () => {
    set({ toasts: [] });
  }
}));

export const useToast = () => {
  const { addToast, removeToast, clearToasts } = useToastStore();
  
  return {
    showSuccess: (message, duration) => addToast(message, 'success', duration),
    showError: (message, duration) => addToast(message, 'error', duration),
    showWarning: (message, duration) => addToast(message, 'warning', duration),
    showInfo: (message, duration) => addToast(message, 'info', duration),
    removeToast,
    clearToasts
  };
};

export const useToasts = () => useToastStore((state) => state.toasts);
