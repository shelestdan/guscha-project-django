// Экспорт всех API функций из одного места для удобства импорта

// Аутентификация и пользователи
export * from './authApi';
export * from './profileApi';

// Товары и каталог
export * from './productsApi';
export * from './searchApi';
export * from './reviewsApi';

// Корзина и заказы
export * from './cartApi';
export * from './ordersApi';

// Избранное
export * from './wishlistApi';

// Предзаказы
export * from './preordersApi';

// Уведомления
export * from './notificationsApi';

// Контакты и обратная связь
export * from './contactApi';

// Настройки приложения
export * from './settingsApi';

// Экспорт настроенного экземпляра axios
export { default as axiosInstance } from './axiosInstance';

// Примечание: файлы orderApi.js и userApi.js устарели и не рекомендуются к использованию.
// Вместо них используйте ordersApi.js, authApi.js и profileApi.js