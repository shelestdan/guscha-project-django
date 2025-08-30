import axios from './axiosInstance';
import {
  fetchProducts,
  fetchProductDetails,
  fetchCategories,
  fetchSizes
} from './productsApi';

// Мокируем axios instance
jest.mock('./axiosInstance');
const mockedAxios = axios;

describe('productsApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchProducts', () => {
    it('должен успешно получить список продуктов без параметров', async () => {
      const mockProducts = {
        results: [
          { id: 1, name: 'Product 1', price: 100 },
          { id: 2, name: 'Product 2', price: 200 }
        ],
        count: 2,
        next: null,
        previous: null
      };
      mockedAxios.get.mockResolvedValue({ data: mockProducts });

      const result = await fetchProducts();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/products/products/', { params: {} });
      expect(result).toEqual(mockProducts);
    });

    it('должен успешно получить список продуктов с параметрами', async () => {
      const params = {
        category: 1,
        search: 'test',
        page: 2,
        ordering: 'price'
      };
      const mockProducts = {
        results: [{ id: 3, name: 'Product 3', price: 150 }],
        count: 1
      };
      mockedAxios.get.mockResolvedValue({ data: mockProducts });

      const result = await fetchProducts(params);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/products/products/', { params });
      expect(result).toEqual(mockProducts);
    });

    it('должен обработать ошибку при получении продуктов', async () => {
      const errorMessage = 'Network Error';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchProducts()).rejects.toThrow(errorMessage);
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/products/products/', { params: {} });
    });
  });

  describe('fetchProductDetails', () => {
    it('должен успешно получить детали продукта', async () => {
      const productId = 123;
      const mockProductDetails = {
        id: productId,
        name: 'Detailed Product',
        description: 'Product description',
        price: 299,
        images: [{ id: 1, image: 'image1.jpg' }],
        sizes: [{ id: 1, name: 'M' }],
        category: { id: 1, name: 'Category 1' }
      };
      mockedAxios.get.mockResolvedValue({ data: mockProductDetails });

      const result = await fetchProductDetails(productId);

      expect(mockedAxios.get).toHaveBeenCalledWith(`/api/products/products/${productId}/`);
      expect(result).toEqual(mockProductDetails);
    });

    it('должен обработать ошибку при получении деталей продукта', async () => {
      const productId = 123;
      const errorMessage = 'Product not found';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchProductDetails(productId)).rejects.toThrow(errorMessage);
      expect(mockedAxios.get).toHaveBeenCalledWith(`/api/products/products/${productId}/`);
    });

    it('должен обработать ошибку 404 при получении несуществующего продукта', async () => {
      const productId = 999;
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found.' }
        }
      };
      mockedAxios.get.mockRejectedValue(error);

      await expect(fetchProductDetails(productId)).rejects.toEqual(error);
    });
  });

  describe('fetchCategories', () => {
    it('должен успешно получить список категорий', async () => {
      const mockCategories = [
        { id: 1, name: 'Category 1', slug: 'category-1' },
        { id: 2, name: 'Category 2', slug: 'category-2' },
        { id: 3, name: 'Category 3', slug: 'category-3' }
      ];
      mockedAxios.get.mockResolvedValue({ data: mockCategories });

      const result = await fetchCategories();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/products/categories/');
      expect(result).toEqual(mockCategories);
    });

    it('должен обработать ошибку при получении категорий', async () => {
      const errorMessage = 'Server Error';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchCategories()).rejects.toThrow(errorMessage);
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/products/categories/');
    });

    it('должен вернуть пустой массив если категории не найдены', async () => {
      const mockEmptyCategories = [];
      mockedAxios.get.mockResolvedValue({ data: mockEmptyCategories });

      const result = await fetchCategories();

      expect(result).toEqual([]);
    });
  });

  describe('fetchSizes', () => {
    it('должен успешно получить список размеров', async () => {
      const mockSizes = [
        { id: 1, name: 'XS', order: 1 },
        { id: 2, name: 'S', order: 2 },
        { id: 3, name: 'M', order: 3 },
        { id: 4, name: 'L', order: 4 },
        { id: 5, name: 'XL', order: 5 }
      ];
      mockedAxios.get.mockResolvedValue({ data: mockSizes });

      const result = await fetchSizes();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/products/sizes/');
      expect(result).toEqual(mockSizes);
    });

    it('должен обработать ошибку при получении размеров', async () => {
      const errorMessage = 'Network Error';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchSizes()).rejects.toThrow(errorMessage);
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/products/sizes/');
    });

    it('должен вернуть пустой массив если размеры не найдены', async () => {
      const mockEmptySizes = [];
      mockedAxios.get.mockResolvedValue({ data: mockEmptySizes });

      const result = await fetchSizes();

      expect(result).toEqual([]);
    });
  });
});