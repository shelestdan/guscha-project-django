import { create } from 'zustand'
import { persist, devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import * as cartApi from '../api/cartApi'

export const useCartStore = create(
  devtools(
    persist(
      immer((set, get) => ({
        items: [],
        count: 0,
        total: 0,
        isOpen: false,
        loading: false,
        error: null,

        // API: загрузка корзины
        fetchCart: async () => {
          console.log('🛒 fetchCart called');
          set((state) => {
            state.loading = true;
            state.error = null;
          });

          try {
            const data = await cartApi.getCartItems();
            console.log('🛒 fetchCart data received:', data);
            set((state) => {
              const itemsArray = (data && Array.isArray(data.items)) ? data.items : [];
              state.items = itemsArray;
              state.count = (data && data.count !== undefined)
                ? data.count
                : itemsArray.reduce((sum, item) => sum + (item.quantity || 0), 0);
              state.total = (data && data.total !== undefined)
                ? parseFloat(data.total)
                : itemsArray.reduce((sum, item) => sum + ((item.quantity || 0) * parseFloat(item.price || 0)), 0);
              state.loading = false;
            });
          } catch (error) {
            console.error('🛒 Error in fetchCart:', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка загрузки корзины';
            });

            if (error.response?.status === 401) {
              set((state) => {
                state.items = [];
                state.count = 0;
                state.total = 0;
              });
            }
          }
        },

        // API: добавить товар
        addToCart: async (productId, sizeId = null, quantity = 1) => {
          console.log('🛒 cartStore.addToCart called:', { productId, sizeId, quantity });
          set((state) => { state.loading = true; state.error = null; });

          try {
            await cartApi.addCartItem(productId, quantity, sizeId);
            await get().fetchCart();
            return true;
          } catch (error) {
            console.error('🛒 Error in cartStore.addToCart:', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка добавления в корзину';
            });
            throw error;
          }
        },

        // API: добавить предзаказ
        addPreorderToCart: async (preorderId, sizeId = null, quantity = 1) => {
          console.log('🛒 cartStore.addPreorderToCart called:', { preorderId, sizeId, quantity });
          set((state) => { state.loading = true; state.error = null; });

          try {
            await cartApi.addPreorderItem(preorderId, quantity, sizeId);
            await get().fetchCart();
            return true;
          } catch (error) {
            console.error('🛒 Error in cartStore.addPreorderToCart:', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка добавления предзаказа';
            });
            throw error;
          }
        },

        // API: обновить количество
        updateQuantity: async (itemId, quantity) => {
          console.log(`🛒 cartStore.updateQuantity called for item ${itemId} with quantity ${quantity}`);
          set((state) => { state.loading = true; state.error = null; });

          try {
            await cartApi.updateCartItem(itemId, quantity);
            await get().fetchCart();
          } catch (error) {
            console.error('🛒 Error in cartStore.updateQuantity:', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка обновления количества';
            });

            if (error.response?.status === 404) {
              console.log('🛒 Item not found, refreshing cart...');
              await get().fetchCart();
            }
          }
        },

        // API: удалить товар
        removeFromCart: async (itemId) => {
          console.log(`🛒 cartStore.removeFromCart called for item ${itemId}`);
          set((state) => { state.loading = true; state.error = null; });

          try {
            await cartApi.removeCartItem(itemId);
            await get().fetchCart();
          } catch (error) {
            console.error('🛒 Error in cartStore.removeFromCart:', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка удаления из корзины';
            });

            if (error.response?.status === 404) {
              console.log('🛒 Item not found, refreshing cart...');
              await get().fetchCart();
            }
          }
        },

        // API: очистить корзину
        clearCart: async () => {
          console.log('🛒 cartStore.clearCart called');
          set((state) => { state.loading = true; state.error = null; });

          try {
            await cartApi.clearCart();
            set((state) => {
              state.items = [];
              state.count = 0;
              state.total = 0;
              state.loading = false;
            });
          } catch (error) {
            console.error('🛒 Error in cartStore.clearCart:', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка очистки корзины';
            });
          }
        },

        // UI: открыть/закрыть корзину
        toggleCart: () => set((state) => { state.isOpen = !state.isOpen }),

        // UI: очистить ошибку
        clearError: () => set((state) => { state.error = null }),
      })),
      { name: 'cart-storage' }
    )
  )
)