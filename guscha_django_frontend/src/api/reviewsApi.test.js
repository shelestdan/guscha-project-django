import axios from './axiosInstance';
import {
  fetchProductReviews,
  addProductReview,
  updateProductReview,
  deleteProductReview,
  fetchUserReviews,
  voteReview
} from './reviewsApi';

// Мокируем axios instance
jest.mock('./axiosInstance');
const mockedAxios = axios;

describe('reviewsApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchProductReviews', () => {
    it('должен успешно получить отзывы для товара без параметров', async () => {
      const productId = 101;
      const mockReviews = {
        results: [
          {
            id: 1,
            user: { username: 'user1', avatar: 'avatar1.jpg' },
            rating: 5,
            comment: 'Great product!',
            created_at: '2024-01-15T10:00:00Z',
            helpful_votes: 3
          },
          {
            id: 2,
            user: { username: 'user2', avatar: 'avatar2.jpg' },
            rating: 4,
            comment: 'Good quality',
            created_at: '2024-01-16T11:00:00Z',
            helpful_votes: 1
          }
        ],
        count: 2,
        average_rating: 4.5
      };
      mockedAxios.get.mockResolvedValue({ data: mockReviews });

      const result = await fetchProductReviews(productId);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `/api/products/products/${productId}/reviews/`,
        { params: {} }
      );
      expect(result).toEqual(mockReviews);
    });

    it('должен успешно получить отзывы с параметрами фильтрации', async () => {
      const productId = 101;
      const params = {
        rating: 5,
        ordering: '-created_at',
        page: 1
      };
      const mockReviews = {
        results: [{
          id: 1,
          rating: 5,
          comment: 'Excellent!'
        }],
        count: 1
      };
      mockedAxios.get.mockResolvedValue({ data: mockReviews });

      const result = await fetchProductReviews(productId, params);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `/api/products/products/${productId}/reviews/`,
        { params }
      );
      expect(result).toEqual(mockReviews);
    });

    it('должен обработать ошибку при получении отзывов', async () => {
      const productId = 999;
      const error = {
        response: {
          status: 404,
          data: { detail: 'Product not found.' }
        }
      };
      mockedAxios.get.mockRejectedValue(error);

      await expect(fetchProductReviews(productId)).rejects.toEqual(error);
    });
  });

  describe('addProductReview', () => {
    it('должен успешно добавить новый отзыв', async () => {
      const productId = 101;
      const reviewData = {
        rating: 5,
        comment: 'Amazing product, highly recommend!'
      };
      const mockNewReview = {
        id: 3,
        product: productId,
        user: { username: 'testuser' },
        ...reviewData,
        created_at: '2024-01-17T12:00:00Z',
        helpful_votes: 0
      };
      mockedAxios.post.mockResolvedValue({ data: mockNewReview });

      const result = await addProductReview(productId, reviewData);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `/api/products/products/${productId}/reviews/`,
        reviewData
      );
      expect(result).toEqual(mockNewReview);
    });

    it('должен обработать ошибку валидации при добавлении отзыва', async () => {
      const productId = 101;
      const reviewData = {
        rating: 6, // Невалидный рейтинг
        comment: ''
      };
      const error = {
        response: {
          status: 400,
          data: {
            rating: ['Ensure this value is less than or equal to 5.'],
            comment: ['This field may not be blank.']
          }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(addProductReview(productId, reviewData)).rejects.toEqual(error);
    });

    it('должен обработать ошибку при попытке добавить повторный отзыв', async () => {
      const productId = 101;
      const reviewData = { rating: 5, comment: 'Great!' };
      const error = {
        response: {
          status: 400,
          data: { error: 'You have already reviewed this product.' }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(addProductReview(productId, reviewData)).rejects.toEqual(error);
    });
  });

  describe('updateProductReview', () => {
    it('должен успешно обновить существующий отзыв', async () => {
      const productId = 101;
      const reviewId = 1;
      const reviewData = {
        rating: 4,
        comment: 'Updated review - still good!'
      };
      const mockUpdatedReview = {
        id: reviewId,
        product: productId,
        ...reviewData,
        updated_at: '2024-01-17T13:00:00Z'
      };
      mockedAxios.put.mockResolvedValue({ data: mockUpdatedReview });

      const result = await updateProductReview(productId, reviewId, reviewData);

      expect(mockedAxios.put).toHaveBeenCalledWith(
        `/api/products/products/${productId}/reviews/${reviewId}/`,
        reviewData
      );
      expect(result).toEqual(mockUpdatedReview);
    });

    it('должен обработать ошибку 404 при обновлении несуществующего отзыва', async () => {
      const productId = 101;
      const reviewId = 999;
      const reviewData = { rating: 4, comment: 'Updated' };
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found.' }
        }
      };
      mockedAxios.put.mockRejectedValue(error);

      await expect(updateProductReview(productId, reviewId, reviewData)).rejects.toEqual(error);
    });

    it('должен обработать ошибку доступа при попытке обновить чужой отзыв', async () => {
      const productId = 101;
      const reviewId = 1;
      const reviewData = { rating: 4, comment: 'Updated' };
      const error = {
        response: {
          status: 403,
          data: { detail: 'You do not have permission to perform this action.' }
        }
      };
      mockedAxios.put.mockRejectedValue(error);

      await expect(updateProductReview(productId, reviewId, reviewData)).rejects.toEqual(error);
    });
  });

  describe('deleteProductReview', () => {
    it('должен успешно удалить отзыв', async () => {
      const productId = 101;
      const reviewId = 1;
      mockedAxios.delete.mockResolvedValue({});

      const result = await deleteProductReview(productId, reviewId);

      expect(mockedAxios.delete).toHaveBeenCalledWith(
        `/api/products/products/${productId}/reviews/${reviewId}/`
      );
      expect(result).toBe(true);
    });

    it('должен обработать ошибку 404 при удалении несуществующего отзыва', async () => {
      const productId = 101;
      const reviewId = 999;
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found.' }
        }
      };
      mockedAxios.delete.mockRejectedValue(error);

      await expect(deleteProductReview(productId, reviewId)).rejects.toEqual(error);
    });

    it('должен обработать ошибку доступа при попытке удалить чужой отзыв', async () => {
      const productId = 101;
      const reviewId = 1;
      const error = {
        response: {
          status: 403,
          data: { detail: 'You do not have permission to perform this action.' }
        }
      };
      mockedAxios.delete.mockRejectedValue(error);

      await expect(deleteProductReview(productId, reviewId)).rejects.toEqual(error);
    });
  });

  describe('fetchUserReviews', () => {
    it('должен успешно получить отзывы пользователя без параметров', async () => {
      const mockUserReviews = {
        results: [
          {
            id: 1,
            product: { id: 101, name: 'Product 1' },
            rating: 5,
            comment: 'Great product!',
            created_at: '2024-01-15T10:00:00Z'
          },
          {
            id: 2,
            product: { id: 102, name: 'Product 2' },
            rating: 4,
            comment: 'Good quality',
            created_at: '2024-01-16T11:00:00Z'
          }
        ],
        count: 2
      };
      mockedAxios.get.mockResolvedValue({ data: mockUserReviews });

      const result = await fetchUserReviews();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/accounts/users/me/reviews/', { params: {} });
      expect(result).toEqual(mockUserReviews);
    });

    it('должен успешно получить отзывы пользователя с параметрами', async () => {
      const params = {
        ordering: '-created_at',
        page: 1
      };
      const mockUserReviews = { results: [], count: 0 };
      mockedAxios.get.mockResolvedValue({ data: mockUserReviews });

      const result = await fetchUserReviews(params);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/accounts/users/me/reviews/', { params });
      expect(result).toEqual(mockUserReviews);
    });

    it('должен обработать ошибку при получении отзывов пользователя', async () => {
      const errorMessage = 'Unauthorized';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchUserReviews()).rejects.toThrow(errorMessage);
    });
  });

  describe('voteReview', () => {
    it('должен успешно проголосовать за отзыв как полезный', async () => {
      const productId = 101;
      const reviewId = 1;
      const isHelpful = true;
      const mockVoteResponse = {
        message: 'Vote recorded successfully',
        helpful_votes: 4,
        unhelpful_votes: 1
      };
      mockedAxios.post.mockResolvedValue({ data: mockVoteResponse });

      const result = await voteReview(productId, reviewId, isHelpful);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `/api/products/products/${productId}/reviews/${reviewId}/vote/`,
        { is_helpful: isHelpful }
      );
      expect(result).toEqual(mockVoteResponse);
    });

    it('должен успешно проголосовать за отзыв как неполезный', async () => {
      const productId = 101;
      const reviewId = 1;
      const isHelpful = false;
      const mockVoteResponse = {
        message: 'Vote recorded successfully',
        helpful_votes: 3,
        unhelpful_votes: 2
      };
      mockedAxios.post.mockResolvedValue({ data: mockVoteResponse });

      const result = await voteReview(productId, reviewId, isHelpful);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `/api/products/products/${productId}/reviews/${reviewId}/vote/`,
        { is_helpful: isHelpful }
      );
      expect(result).toEqual(mockVoteResponse);
    });

    it('должен обработать ошибку при повторном голосовании', async () => {
      const productId = 101;
      const reviewId = 1;
      const isHelpful = true;
      const error = {
        response: {
          status: 400,
          data: { error: 'You have already voted for this review.' }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(voteReview(productId, reviewId, isHelpful)).rejects.toEqual(error);
    });

    it('должен обработать ошибку при голосовании за несуществующий отзыв', async () => {
      const productId = 101;
      const reviewId = 999;
      const isHelpful = true;
      const error = {
        response: {
          status: 404,
          data: { detail: 'Review not found.' }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(voteReview(productId, reviewId, isHelpful)).rejects.toEqual(error);
    });
  });
});