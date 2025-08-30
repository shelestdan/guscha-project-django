import { renderHook, act } from '@testing-library/react';
import { useCartStore } from './cartStore';
import * as cartApi from '../api/cartApi';
import { logger } from '../utils/logger';

// Мокаем зависимости
jest.mock('../api/cartApi');
jest.mock('../utils/logger');

// Мокаем Zustand persist middleware
jest.mock('zustand/middleware', () => ({
  persist: (fn) => fn,
  devtools: (fn) => fn,
  immer: (fn) => fn,
}));

describe('cartStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Очищаем store перед каждым тестом
    const { result } = renderHook(() => useCartStore());
    act(() => {
      result.current.items = [];
      result.current.count = 0;
      result.current.total = 0;
      result.current.isOpen = false;
      result.current.loading = false;
      result.current.error = null;
    });
  });

  describe('Initial state', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useCartStore());
      
      expect(result.current.items).toEqual([]);
      expect(result.current.count).toBe(0);
      expect(result.current.total).toBe(0);
      expect(result.current.isOpen).toBe(false);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('fetchCart', () => {
    it('should fetch cart successfully', async () => {
      const mockCartData = {
        items: [
          { id: 1, product_id: 1, quantity: 2, price: '100.00' },
          { id: 2, product_id: 2, quantity: 1, price: '50.00' }
        ],
        count: 3,
        total: 250.00
      };
      
      cartApi.getCartItems.mockResolvedValue(mockCartData);
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.fetchCart();
      });
      
      expect(result.current.items).toEqual(mockCartData.items);
      expect(result.current.count).toBe(3);
      expect(result.current.total).toBe(250.00);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(logger.debug).toHaveBeenCalledWith('CartStore', 'fetchCart called');
    });

    it('should handle empty cart data', async () => {
      cartApi.getCartItems.mockResolvedValue({ items: [], count: 0, total: 0 });
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.fetchCart();
      });
      
      expect(result.current.items).toEqual([]);
      expect(result.current.count).toBe(0);
      expect(result.current.total).toBe(0);
    });

    it('should calculate count and total from items when not provided', async () => {
      const mockItems = [
        { id: 1, quantity: 2, price: '100.00' },
        { id: 2, quantity: 1, price: '50.00' }
      ];
      
      cartApi.getCartItems.mockResolvedValue({ items: mockItems });
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.fetchCart();
      });
      
      expect(result.current.count).toBe(3); // 2 + 1
      expect(result.current.total).toBe(250); // 2*100 + 1*50
    });

    it('should handle fetch error', async () => {
      const mockError = new Error('Network error');
      cartApi.getCartItems.mockRejectedValue(mockError);
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.fetchCart();
      });
      
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe('Network error');
      expect(logger.error).toHaveBeenCalledWith('CartStore', 'Error in fetchCart', mockError);
    });

    it('should clear cart on 401 error', async () => {
      const mockError = {
        message: 'Unauthorized',
        response: { status: 401 }
      };
      cartApi.getCartItems.mockRejectedValue(mockError);
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.fetchCart();
      });
      
      expect(result.current.items).toEqual([]);
      expect(result.current.count).toBe(0);
      expect(result.current.total).toBe(0);
    });
  });

  describe('addToCart', () => {
    it('should add item to cart successfully', async () => {
      cartApi.addCartItem.mockResolvedValue();
      cartApi.getCartItems.mockResolvedValue({
        items: [{ id: 1, product_id: 1, quantity: 1, price: '100.00' }],
        count: 1,
        total: 100.00
      });
      
      const { result } = renderHook(() => useCartStore());
      
      let returnValue;
      await act(async () => {
        returnValue = await result.current.addToCart(1, 1, 1);
      });
      
      expect(returnValue).toBe(true);
      expect(cartApi.addCartItem).toHaveBeenCalledWith(1, 1, 1);
      expect(result.current.items).toHaveLength(1);
      expect(logger.debug).toHaveBeenCalledWith('CartStore', 'addToCart called', {
        productId: 1,
        sizeId: 1,
        quantity: 1
      });
    });

    it('should handle add to cart error', async () => {
      const mockError = new Error('Add failed');
      cartApi.addCartItem.mockRejectedValue(mockError);
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        try {
          await result.current.addToCart(1, 1, 1);
        } catch (error) {
          expect(error).toBe(mockError);
        }
      });
      
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe('Add failed');
      expect(logger.error).toHaveBeenCalledWith('CartStore', 'Error in addToCart', mockError);
    });
  });

  describe('addPreorderToCart', () => {
    it('should add preorder to cart successfully', async () => {
      cartApi.addPreorderItem.mockResolvedValue();
      cartApi.getCartItems.mockResolvedValue({
        items: [{ id: 1, preorder_id: 1, quantity: 1, price: '150.00' }],
        count: 1,
        total: 150.00
      });
      
      const { result } = renderHook(() => useCartStore());
      
      let returnValue;
      await act(async () => {
        returnValue = await result.current.addPreorderToCart(1, 1, 1);
      });
      
      expect(returnValue).toBe(true);
      expect(cartApi.addPreorderItem).toHaveBeenCalledWith(1, 1, 1);
      expect(result.current.items).toHaveLength(1);
      expect(logger.debug).toHaveBeenCalledWith('CartStore', 'addPreorderToCart called', {
        preorderId: 1,
        sizeId: 1,
        quantity: 1
      });
    });

    it('should handle add preorder error', async () => {
      const mockError = new Error('Preorder add failed');
      cartApi.addPreorderItem.mockRejectedValue(mockError);
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        try {
          await result.current.addPreorderToCart(1, 1, 1);
        } catch (error) {
          expect(error).toBe(mockError);
        }
      });
      
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe('Preorder add failed');
    });
  });

  describe('updateQuantity', () => {
    it('should update quantity successfully', async () => {
      cartApi.updateCartItem.mockResolvedValue();
      cartApi.getCartItems.mockResolvedValue({
        items: [{ id: 1, product_id: 1, quantity: 3, price: '100.00' }],
        count: 3,
        total: 300.00
      });
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.updateQuantity(1, 3);
      });
      
      expect(cartApi.updateCartItem).toHaveBeenCalledWith(1, 3);
      expect(result.current.items[0].quantity).toBe(3);
      expect(logger.debug).toHaveBeenCalledWith('CartStore', 'updateQuantity called for item 1', {
        itemId: 1,
        quantity: 3
      });
    });

    it('should handle update quantity error', async () => {
      const mockError = new Error('Update failed');
      cartApi.updateCartItem.mockRejectedValue(mockError);
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.updateQuantity(1, 3);
      });
      
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe('Update failed');
    });

    it('should refresh cart on 404 error', async () => {
      const mockError = {
        message: 'Not found',
        response: { status: 404 }
      };
      cartApi.updateCartItem.mockRejectedValue(mockError);
      cartApi.getCartItems.mockResolvedValue({ items: [], count: 0, total: 0 });
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.updateQuantity(1, 3);
      });
      
      expect(logger.info).toHaveBeenCalledWith('CartStore', 'Item not found, refreshing cart');
    });
  });

  describe('removeFromCart', () => {
    it('should remove item from cart successfully', async () => {
      cartApi.removeCartItem.mockResolvedValue();
      cartApi.getCartItems.mockResolvedValue({ items: [], count: 0, total: 0 });
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.removeFromCart(1);
      });
      
      expect(cartApi.removeCartItem).toHaveBeenCalledWith(1);
      expect(result.current.items).toEqual([]);
      expect(logger.debug).toHaveBeenCalledWith('CartStore', 'removeFromCart called for item 1', {
        itemId: 1
      });
    });

    it('should handle remove error', async () => {
      const mockError = new Error('Remove failed');
      cartApi.removeCartItem.mockRejectedValue(mockError);
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.removeFromCart(1);
      });
      
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe('Remove failed');
    });

    it('should refresh cart on 404 error', async () => {
      const mockError = {
        message: 'Not found',
        response: { status: 404 }
      };
      cartApi.removeCartItem.mockRejectedValue(mockError);
      cartApi.getCartItems.mockResolvedValue({ items: [], count: 0, total: 0 });
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.removeFromCart(1);
      });
      
      expect(logger.info).toHaveBeenCalledWith('CartStore', 'Item not found, refreshing cart');
    });
  });

  describe('clearCart', () => {
    it('should clear cart successfully', async () => {
      cartApi.clearCart.mockResolvedValue();
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.clearCart();
      });
      
      expect(cartApi.clearCart).toHaveBeenCalled();
      expect(result.current.items).toEqual([]);
      expect(result.current.count).toBe(0);
      expect(result.current.total).toBe(0);
      expect(result.current.loading).toBe(false);
      expect(logger.debug).toHaveBeenCalledWith('CartStore', 'clearCart called');
    });

    it('should handle clear cart error', async () => {
      const mockError = new Error('Clear failed');
      cartApi.clearCart.mockRejectedValue(mockError);
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        await result.current.clearCart();
      });
      
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe('Clear failed');
      expect(logger.error).toHaveBeenCalledWith('CartStore', 'Error in clearCart', mockError);
    });
  });

  describe('UI actions', () => {
    it('should toggle cart open/close', () => {
      const { result } = renderHook(() => useCartStore());
      
      expect(result.current.isOpen).toBe(false);
      
      act(() => {
        result.current.toggleCart();
      });
      
      expect(result.current.isOpen).toBe(true);
      
      act(() => {
        result.current.toggleCart();
      });
      
      expect(result.current.isOpen).toBe(false);
    });

    it('should clear error', () => {
      const { result } = renderHook(() => useCartStore());
      
      // Устанавливаем ошибку
      act(() => {
        result.current.error = 'Test error';
      });
      
      expect(result.current.error).toBe('Test error');
      
      act(() => {
        result.current.clearError();
      });
      
      expect(result.current.error).toBeNull();
    });
  });

  describe('Loading states', () => {
    it('should set loading to true during API calls', async () => {
      let resolvePromise;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      
      cartApi.addCartItem.mockReturnValue(promise);
      
      const { result } = renderHook(() => useCartStore());
      
      act(() => {
        result.current.addToCart(1, 1, 1);
      });
      
      expect(result.current.loading).toBe(true);
      
      await act(async () => {
        resolvePromise();
        await promise;
      });
    });
  });

  describe('Error handling', () => {
    it('should handle API errors with default messages', async () => {
      const mockError = { message: undefined };
      cartApi.addCartItem.mockRejectedValue(mockError);
      
      const { result } = renderHook(() => useCartStore());
      
      await act(async () => {
        try {
          await result.current.addToCart(1, 1, 1);
        } catch (error) {
          // Ожидаем, что ошибка будет выброшена
        }
      });
      
      expect(result.current.error).toBe('Ошибка добавления в корзину');
    });
  });
});