import { create } from 'zustand';

const useToastStore = create((set, get) => ({
  toasts: [],
  nextId: 0, // Счетчик для гарантированно уникальных ID
  addToast: (message, type = 'info', duration = 4000) => {
    const state = get();
    const id = state.nextId + Date.now() + Math.random(); // Комбинированный уникальный ID
    const toast = { id, message, type, duration };
    
    set((prevState) => ({
      toasts: [...prevState.toasts, toast],
      nextId: prevState.nextId + 1 // Увеличиваем счетчик
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
