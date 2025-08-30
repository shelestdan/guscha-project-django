import axios from './axiosInstance';
import {
  fetchWishlist,
  addToWishlist,
  removeFromWishlist,
  checkInWishlist,
  clearWishlist
} from './wishlistApi';

// Мокируем axios instance
jest.mock('./axiosInstance');
const mockedAxios = axios;

// Мокируем console.error для тестов
const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

describe('wishlistApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    consoleSpy.mockClear();
  });

  afterAll(() => {
    consoleSpy.mockRestore();
  });

  describe('fetchWishlist', () => {
    it('должен успешно получить список избранных товаров', async () => {
      const mockWishlist = {
        results: [
          {
            id: 1,
            product: {
              id: 101,
              name: 'Product 1',
              price: 100,
              image: 'product1.jpg'
            },
            added_at: '2024-01-15T10:00:00Z'
          },
          {
            id: 2,
            product: {
              id: 102,
              name: 'Product 2',
              price: 200,
              image: 'product2.jpg'
            },
            added_at: '2024-01-16T11:00:00Z'
          }
        ],
        count: 2
      };
      mockedAxios.get.mockResolvedValue({ data: mockWishlist });

      const result = await fetchWishlist();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/wishlist/');
      expect(result).toEqual(mockWishlist);
    });

    it('должен вернуть пустой список если избранное пусто', async () => {
      const mockEmptyWishlist = {
        results: [],
        count: 0
      };
      mockedAxios.get.mockResolvedValue({ data: mockEmptyWishlist });

      const result = await fetchWishlist();

      expect(result).toEqual(mockEmptyWishlist);
    });

    it('должен обработать ошибку при получении списка избранного', async () => {
      const errorMessage = 'Unauthorized';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchWishlist()).rejects.toThrow(errorMessage);
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/wishlist/');
    });
  });

  describe('addToWishlist', () => {
    it('должен успешно добавить товар в избранное', async () => {
      const productId = 101;
      const mockResponse = {
        id: 3,
        product: productId,
        message: 'Product added to wishlist successfully'
      };
      mockedAxios.post.mockResolvedValue({ data: mockResponse });

      const result = await addToWishlist(productId);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/wishlist/add/', { product: productId });
      expect(result).toEqual(mockResponse);
    });

    it('должен обработать ошибку при добавлении уже существующего товара', async () => {
      const productId = 101;
      const error = {
        response: {
          status: 400,
          data: { error: 'Product already in wishlist' }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(addToWishlist(productId)).rejects.toEqual(error);
    });

    it('должен обработать ошибку при добавлении несуществующего товара', async () => {
      const productId = 999;
      const error = {
        response: {
          status: 404,
          data: { error: 'Product not found' }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(addToWishlist(productId)).rejects.toEqual(error);
    });
  });

  describe('removeFromWishlist', () => {
    it('должен успешно удалить товар из избранного', async () => {
      const productId = 101;
      const mockResponse = {
        message: 'Product removed from wishlist successfully'
      };
      mockedAxios.delete.mockResolvedValue({ data: mockResponse });

      const result = await removeFromWishlist(productId);

      expect(mockedAxios.delete).toHaveBeenCalledWith(`/api/wishlist/remove/${productId}/`);
      expect(result).toEqual(mockResponse);
    });

    it('должен обработать ошибку при удалении несуществующего товара', async () => {
      const productId = 999;
      const error = {
        response: {
          status: 404,
          data: { error: 'Product not found in wishlist' }
        }
      };
      mockedAxios.delete.mockRejectedValue(error);

      await expect(removeFromWishlist(productId)).rejects.toEqual(error);
    });

    it('должен обработать общую ошибку при удалении', async () => {
      const productId = 101;
      const errorMessage = 'Network Error';
      mockedAxios.delete.mockRejectedValue(new Error(errorMessage));

      await expect(removeFromWishlist(productId)).rejects.toThrow(errorMessage);
    });
  });

  describe('checkInWishlist', () => {
    it('должен вернуть true если товар в избранном', async () => {
      const productId = 101;
      const mockResponse = { in_wishlist: true };
      mockedAxios.get.mockResolvedValue({ data: mockResponse });

      const result = await checkInWishlist(productId);

      expect(mockedAxios.get).toHaveBeenCalledWith(`/api/wishlist/check/${productId}/`);
      expect(result).toBe(true);
    });

    it('должен вернуть false если товар не в избранном', async () => {
      const productId = 102;
      const mockResponse = { in_wishlist: false };
      mockedAxios.get.mockResolvedValue({ data: mockResponse });

      const result = await checkInWishlist(productId);

      expect(result).toBe(false);
    });

    it('должен вернуть false и залогировать ошибку при сетевой ошибке', async () => {
      const productId = 101;
      const errorMessage = 'Network Error';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      const result = await checkInWishlist(productId);

      expect(result).toBe(false);
      expect(consoleSpy).toHaveBeenCalledWith('Error checking wishlist status:', expect.any(Error));
    });

    it('должен вернуть false и залогировать ошибку при ошибке 404', async () => {
      const productId = 999;
      const error = {
        response: {
          status: 404,
          data: { error: 'Product not found' }
        }
      };
      mockedAxios.get.mockRejectedValue(error);

      const result = await checkInWishlist(productId);

      expect(result).toBe(false);
      expect(consoleSpy).toHaveBeenCalledWith('Error checking wishlist status:', error);
    });
  });

  describe('clearWishlist', () => {
    it('должен успешно очистить весь список избранного', async () => {
      const mockResponse = {
        message: 'Wishlist cleared successfully',
        cleared_count: 5
      };
      mockedAxios.post.mockResolvedValue({ data: mockResponse });

      const result = await clearWishlist();

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/wishlist/clear/');
      expect(result).toEqual(mockResponse);
    });

    it('должен обработать ошибку при очистке избранного', async () => {
      const errorMessage = 'Server Error';
      mockedAxios.post.mockRejectedValue(new Error(errorMessage));

      await expect(clearWishlist()).rejects.toThrow(errorMessage);
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/wishlist/clear/');
    });

    it('должен обработать ошибку доступа при очистке избранного', async () => {
      const error = {
        response: {
          status: 401,
          data: { detail: 'Authentication credentials were not provided.' }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(clearWishlist()).rejects.toEqual(error);
    });
  });
});