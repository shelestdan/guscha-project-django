import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import * as cartApi from '../api/cartApi';
import { logger } from '../utils/logger';

const MODULE_NAME = 'CartStore';

/**
 * @typedef {Object} CartItem
 * @property {number} id
 * @property {number} [product_id]
 * @property {number} [preorder_id]
 * @property {Object} [product]
 * @property {Object} [preorder]
 * @property {Object} [size]
 * @property {number} quantity
 * @property {string} price
 */

/**
 * Zustand store для управления корзиной
 */
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
          logger.debug(MODULE_NAME, 'fetchCart called');
          set((state) => {
            state.loading = true;
            state.error = null;
          });

          try {
            const data = await cartApi.getCartItems();
            logger.debug(MODULE_NAME, 'fetchCart data received', data);
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
            logger.error(MODULE_NAME, 'Error in fetchCart', error);
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
          logger.debug(MODULE_NAME, 'addToCart called', { productId, sizeId, quantity });
          set((state) => { state.loading = true; state.error = null; });

          try {
            await cartApi.addCartItem(productId, quantity, sizeId);
            await get().fetchCart();
            return true;
          } catch (error) {
            logger.error(MODULE_NAME, 'Error in addToCart', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка добавления в корзину';
            });
            throw error;
          }
        },

        // API: добавить предзаказ
        addPreorderToCart: async (preorderId, sizeId = null, quantity = 1) => {
          logger.debug(MODULE_NAME, 'addPreorderToCart called', { preorderId, sizeId, quantity });
          set((state) => { state.loading = true; state.error = null; });

          try {
            await cartApi.addPreorderItem(preorderId, quantity, sizeId);
            await get().fetchCart();
            return true;
          } catch (error) {
            logger.error(MODULE_NAME, 'Error in addPreorderToCart', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка добавления предзаказа';
            });
            throw error;
          }
        },

        // API: обновить количество
        updateQuantity: async (itemId, quantity) => {
          logger.debug(MODULE_NAME, `updateQuantity called for item ${itemId}`, { itemId, quantity });
          set((state) => { state.loading = true; state.error = null; });

          try {
            await cartApi.updateCartItem(itemId, quantity);
            await get().fetchCart();
          } catch (error) {
            logger.error(MODULE_NAME, 'Error in updateQuantity', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка обновления количества';
            });

            if (error.response?.status === 404) {
              logger.info(MODULE_NAME, 'Item not found, refreshing cart');
              await get().fetchCart();
            }
          }
        },

        // API: удалить товар
        removeFromCart: async (itemId) => {
          logger.debug(MODULE_NAME, `removeFromCart called for item ${itemId}`, { itemId });
          set((state) => { state.loading = true; state.error = null; });

          try {
            await cartApi.removeCartItem(itemId);
            await get().fetchCart();
          } catch (error) {
            logger.error(MODULE_NAME, 'Error in removeFromCart', error);
            set((state) => {
              state.loading = false;
              state.error = error.message || 'Ошибка удаления из корзины';
            });

            if (error.response?.status === 404) {
              logger.info(MODULE_NAME, 'Item not found, refreshing cart');
              await get().fetchCart();
            }
          }
        },

        // API: очистить корзину
        clearCart: async () => {
          logger.debug(MODULE_NAME, 'clearCart called');
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
            logger.error(MODULE_NAME, 'Error in clearCart', error);
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