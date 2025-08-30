import axios from './axiosInstance';
import {
  getCartItems,
  addCartItem,
  addPreorderItem,
  updateCartItem,
  removeCartItem,
  clearCart,
  createCartReservations,
  applyPromoCode,
  removePromoCode,
  getAvailablePromoCodes,
  validatePromoCode
} from './cartApi';

// Мокируем axios
jest.mock('./axiosInstance');
const mockedAxios = axios;

// Мокируем localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Мокируем console методы
const consoleSpy = {
  log: jest.spyOn(console, 'log').mockImplementation(() => {}),
  error: jest.spyOn(console, 'error').mockImplementation(() => {})
};

describe('cartApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockClear();
    consoleSpy.log.mockClear();
    consoleSpy.error.mockClear();
  });

  afterAll(() => {
    consoleSpy.log.mockRestore();
    consoleSpy.error.mockRestore();
  });

  describe('getCartItems', () => {
    it('should get cart items successfully', async () => {
      const mockCartData = {
        items: [
          { id: 1, product: { name: 'Test Product' }, quantity: 2, price: 100 }
        ],
        count: 1,
        total: 200
      };
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.get.mockResolvedValue({ data: mockCartData });

      const result = await getCartItems();

      expect(localStorageMock.getItem).toHaveBeenCalledWith('cart_session_id');
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/cart/items/');
      expect(result).toEqual(mockCartData);
      expect(consoleSpy.log).toHaveBeenCalledWith('🛒 cartApi.getCartItems called');
      expect(consoleSpy.log).toHaveBeenCalledWith('🛒 Frontend session ID:', 'session-123');
    });

    it('should handle get cart items error', async () => {
      const mockError = new Error('Network error');
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.get.mockRejectedValue(mockError);

      await expect(getCartItems()).rejects.toThrow('Network error');
      expect(consoleSpy.error).toHaveBeenCalledWith('🛒 Error in getCartItems:', mockError);
    });

    it('should work without session ID', async () => {
      const mockCartData = { items: [], count: 0, total: 0 };
      localStorageMock.getItem.mockReturnValue(null);
      mockedAxios.get.mockResolvedValue({ data: mockCartData });

      const result = await getCartItems();

      expect(result).toEqual(mockCartData);
      expect(consoleSpy.log).toHaveBeenCalledWith('🛒 Frontend session ID:', null);
    });
  });

  describe('addCartItem', () => {
    it('should add cart item successfully with default quantity', async () => {
      const mockResponse = { data: { message: 'Item added' } };
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await addCartItem(1);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/cart/add/', {
        product: 1,
        quantity: 1
      });
      expect(result).toEqual(mockResponse.data);
      expect(consoleSpy.log).toHaveBeenCalledWith('🛒 cartApi.addCartItem request:', {
        product: 1,
        quantity: 1
      });
    });

    it('should add cart item with custom quantity and size', async () => {
      const mockResponse = { data: { message: 'Item added' } };
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await addCartItem(1, 3, 2);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/cart/add/', {
        product: 1,
        quantity: 3,
        size: 2
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle add cart item error', async () => {
      const mockError = new Error('Product not found');
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(addCartItem(999)).rejects.toThrow('Product not found');
      expect(consoleSpy.error).toHaveBeenCalledWith('🛒 Error in addCartItem:', mockError);
    });
  });

  describe('addPreorderItem', () => {
    it('should add preorder item successfully with default quantity', async () => {
      const mockResponse = { data: { message: 'Preorder item added' } };
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await addPreorderItem(1);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/cart/add_preorder/', {
        preorder: 1,
        quantity: 1
      });
      expect(result).toEqual(mockResponse.data);
      expect(consoleSpy.log).toHaveBeenCalledWith('🛒 cartApi.addPreorderItem request:', {
        preorder: 1,
        quantity: 1
      });
    });

    it('should add preorder item with custom quantity and size', async () => {
      const mockResponse = { data: { message: 'Preorder item added' } };
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await addPreorderItem(1, 2, 3);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/cart/add_preorder/', {
        preorder: 1,
        quantity: 2,
        size: 3
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle add preorder item error', async () => {
      const mockError = new Error('Preorder not found');
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(addPreorderItem(999)).rejects.toThrow('Preorder not found');
      expect(consoleSpy.error).toHaveBeenCalledWith('🛒 Error in addPreorderItem:', mockError);
    });
  });

  describe('updateCartItem', () => {
    it('should update cart item successfully', async () => {
      const mockResponse = { data: { message: 'Item updated' } };
      mockedAxios.put.mockResolvedValue(mockResponse);

      const result = await updateCartItem(1, 5);

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/cart/update/1/', { quantity: 5 });
      expect(result).toEqual(mockResponse.data);
      expect(consoleSpy.log).toHaveBeenCalledWith(
        '🛒 cartApi.updateCartItem called for item 1 with quantity 5'
      );
    });

    it('should handle update cart item error with 404', async () => {
      const mockError = {
        response: { status: 404 },
        message: 'Not found'
      };
      mockedAxios.put.mockRejectedValue(mockError);

      await expect(updateCartItem(999, 2))
        .rejects.toThrow('Товар в корзине с ID 999 не найден');
      expect(consoleSpy.error).toHaveBeenCalledWith(
        '🛒 Cart item with ID 999 not found'
      );
    });

    it('should handle update cart item general error', async () => {
      const mockError = new Error('Server error');
      mockedAxios.put.mockRejectedValue(mockError);

      await expect(updateCartItem(1, 2)).rejects.toThrow('Server error');
      expect(consoleSpy.error).toHaveBeenCalledWith('🛒 Error in updateCartItem:', mockError);
    });
  });

  describe('removeCartItem', () => {
    it('should remove cart item successfully', async () => {
      const mockResponse = { data: { message: 'Item removed' } };
      mockedAxios.delete.mockResolvedValue(mockResponse);

      const result = await removeCartItem(1);

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/cart/remove/1/');
      expect(result).toEqual(mockResponse.data);
      expect(consoleSpy.log).toHaveBeenCalledWith('🛒 cartApi.removeCartItem called for item 1');
    });

    it('should handle remove cart item with 404 (already removed)', async () => {
      const mockError = {
        response: { status: 404 },
        message: 'Not found'
      };
      mockedAxios.delete.mockRejectedValue(mockError);

      const result = await removeCartItem(999);

      expect(result).toEqual({ message: 'Item already removed' });
      expect(consoleSpy.error).toHaveBeenCalledWith(
        '🛒 Cart item with ID 999 not found - may already be removed'
      );
    });

    it('should handle remove cart item general error', async () => {
      const mockError = new Error('Server error');
      mockedAxios.delete.mockRejectedValue(mockError);

      await expect(removeCartItem(1)).rejects.toThrow('Server error');
      expect(consoleSpy.error).toHaveBeenCalledWith('🛒 Error in removeCartItem:', mockError);
    });
  });

  describe('clearCart', () => {
    it('should clear cart successfully', async () => {
      const mockResponse = { data: { message: 'Cart cleared' } };
      mockedAxios.delete.mockResolvedValue(mockResponse);

      const result = await clearCart();

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/cart/clear/');
      expect(result).toEqual(mockResponse.data);
      expect(consoleSpy.log).toHaveBeenCalledWith('🛒 cartApi.clearCart called');
    });

    it('should handle clear cart error', async () => {
      const mockError = new Error('Server error');
      mockedAxios.delete.mockRejectedValue(mockError);

      await expect(clearCart()).rejects.toThrow('Server error');
      expect(consoleSpy.error).toHaveBeenCalledWith('🛒 Error in clearCart:', mockError);
    });
  });

  describe('createCartReservations', () => {
    it('should create cart reservations successfully', async () => {
      const mockResponse = { data: { reservations: ['res1', 'res2'] } };
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await createCartReservations();

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/cart/create-reservations/');
      expect(result).toEqual(mockResponse.data);
      expect(consoleSpy.log).toHaveBeenCalledWith('🛒 cartApi.createCartReservations called');
      expect(consoleSpy.log).toHaveBeenCalledWith('🛒 Frontend session ID for reservations:', 'session-123');
    });

    it('should handle create cart reservations error', async () => {
      const mockError = new Error('Reservation failed');
      localStorageMock.getItem.mockReturnValue('session-123');
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(createCartReservations()).rejects.toThrow('Reservation failed');
      expect(consoleSpy.error).toHaveBeenCalledWith('🛒 Error in createCartReservations:', mockError);
    });
  });

  describe('Promo code functions (disabled)', () => {
    describe('applyPromoCode', () => {
      it('should throw error for disabled promo codes', async () => {
        await expect(applyPromoCode('TEST123'))
          .rejects.toThrow('Промокоды временно недоступны');
        expect(consoleSpy.log).toHaveBeenCalledWith(
          '🛒 cartApi.applyPromoCode called with code:', 'TEST123'
        );
      });
    });

    describe('removePromoCode', () => {
      it('should throw error for disabled promo codes', async () => {
        await expect(removePromoCode())
          .rejects.toThrow('Промокоды временно недоступны');
        expect(consoleSpy.log).toHaveBeenCalledWith('🛒 cartApi.removePromoCode called');
      });
    });

    describe('getAvailablePromoCodes', () => {
      it('should return empty array for disabled promo codes', async () => {
        const result = await getAvailablePromoCodes();

        expect(result).toEqual([]);
        expect(consoleSpy.log).toHaveBeenCalledWith('🛒 cartApi.getAvailablePromoCodes called');
      });
    });

    describe('validatePromoCode', () => {
      it('should throw error for disabled promo codes', async () => {
        await expect(validatePromoCode('TEST123'))
          .rejects.toThrow('Промокоды временно недоступны');
        expect(consoleSpy.log).toHaveBeenCalledWith(
          '🛒 cartApi.validatePromoCode called with code:', 'TEST123'
        );
      });
    });
  });
});