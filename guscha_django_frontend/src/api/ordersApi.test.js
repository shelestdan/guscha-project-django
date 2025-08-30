import axios from 'axios';
import {
  fetchUserOrders,
  fetchOrderDetails,
  createOrder,
  cancelOrder,
  fetchDeliveryMethods,
  fetchPaymentMethods,
  checkPaymentStatus,
  initiatePayment
} from './ordersApi';

// Мокируем axiosInstance
jest.mock('./axiosInstance', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
}));

import axiosInstance from './axiosInstance';
const mockedAxios = axiosInstance;

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

describe('ordersApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('test-session-id');
  });

  describe('fetchUserOrders', () => {
    it('должен успешно получить заказы пользователя', async () => {
      const mockOrders = [
        { id: 1, status: 'pending', total: 100 },
        { id: 2, status: 'completed', total: 200 }
      ];
      mockedAxios.get.mockResolvedValue({ data: mockOrders });

      const result = await fetchUserOrders();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/orders/');
      expect(result).toEqual(mockOrders);
    });

    it('должен обработать ошибку при получении заказов', async () => {
      const errorMessage = 'Network Error';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchUserOrders()).rejects.toThrow(errorMessage);
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/orders/');
    });
  });

  describe('fetchOrderDetails', () => {
    it('должен успешно получить детали заказа', async () => {
      const orderId = 123;
      const mockOrderDetails = {
        id: orderId,
        status: 'pending',
        items: [{ id: 1, name: 'Product 1', quantity: 2 }],
        total: 100
      };
      mockedAxios.get.mockResolvedValue({ data: mockOrderDetails });

      const result = await fetchOrderDetails(orderId);

      expect(mockedAxios.get).toHaveBeenCalledWith(`/api/orders/${orderId}/`);
      expect(result).toEqual(mockOrderDetails);
    });

    it('должен обработать ошибку при получении деталей заказа', async () => {
      const orderId = 123;
      const errorMessage = 'Order not found';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchOrderDetails(orderId)).rejects.toThrow(errorMessage);
      expect(mockedAxios.get).toHaveBeenCalledWith(`/api/orders/${orderId}/`);
    });
  });

  describe('createOrder', () => {
    it('должен успешно создать заказ', async () => {
      const orderData = {
        delivery_method: 1,
        payment_method: 1,
        address: 'Test Address',
        phone: '+1234567890'
      };
      const mockCreatedOrder = {
        id: 123,
        status: 'pending',
        ...orderData
      };
      mockedAxios.post.mockResolvedValue({ data: mockCreatedOrder });

      const result = await createOrder(orderData);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/orders/', orderData);
      expect(result).toEqual(mockCreatedOrder);
    });

    it('должен создать заказ без session_id если его нет в localStorage', async () => {
      localStorageMock.getItem.mockReturnValue(null);
      const orderData = {
        delivery_method: 1,
        payment_method: 1,
        address: 'Test Address'
      };
      const mockCreatedOrder = { id: 123, status: 'pending' };
      mockedAxios.post.mockResolvedValue({ data: mockCreatedOrder });

      const result = await createOrder(orderData);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/orders/', orderData);
      expect(result).toEqual(mockCreatedOrder);
    });

    it('должен обработать ошибку при создании заказа', async () => {
      const orderData = { delivery_method: 1 };
      const errorMessage = 'Validation error';
      mockedAxios.post.mockRejectedValue(new Error(errorMessage));

      await expect(createOrder(orderData)).rejects.toThrow(errorMessage);
    });
  });

  describe('cancelOrder', () => {
    it('должен успешно отменить заказ', async () => {
      const orderId = 123;
      const mockResponse = { message: 'Order cancelled successfully' };
      mockedAxios.post.mockResolvedValue({ data: mockResponse });

      const result = await cancelOrder(orderId);

      expect(mockedAxios.post).toHaveBeenCalledWith(`/api/orders/${orderId}/cancel/`, { reason: '' });
      expect(result).toEqual(mockResponse);
    });

    it('должен обработать ошибку при отмене заказа', async () => {
      const orderId = 123;
      const errorMessage = 'Cannot cancel order';
      mockedAxios.post.mockRejectedValue(new Error(errorMessage));

      await expect(cancelOrder(orderId)).rejects.toThrow(errorMessage);
      expect(mockedAxios.post).toHaveBeenCalledWith(`/api/orders/${orderId}/cancel/`, { reason: '' });
    });
  });

  describe('fetchDeliveryMethods', () => {
    it('должен успешно получить методы доставки', async () => {
      const mockDeliveryMethods = [
        { id: 1, name: 'Courier', price: 10 },
        { id: 2, name: 'Pickup', price: 0 }
      ];
      mockedAxios.get.mockResolvedValue({ data: mockDeliveryMethods });

      const result = await fetchDeliveryMethods();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/orders/delivery-methods/');
      expect(result).toEqual(mockDeliveryMethods);
    });

    it('должен обработать ошибку при получении методов доставки', async () => {
      const errorMessage = 'Network Error';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchDeliveryMethods()).rejects.toThrow(errorMessage);
    });
  });

  describe('fetchPaymentMethods', () => {
    it('должен успешно получить методы оплаты', async () => {
      const mockPaymentMethods = [
        { id: 1, name: 'Credit Card', enabled: true },
        { id: 2, name: 'Cash', enabled: true }
      ];
      mockedAxios.get.mockResolvedValue({ data: mockPaymentMethods });

      const result = await fetchPaymentMethods();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/orders/payment-methods/');
      expect(result).toEqual(mockPaymentMethods);
    });

    it('должен обработать ошибку при получении методов оплаты', async () => {
      const errorMessage = 'Network Error';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchPaymentMethods()).rejects.toThrow(errorMessage);
    });
  });

  describe('checkPaymentStatus', () => {
    it('должен успешно проверить статус платежа', async () => {
      const orderId = 123;
      const mockPaymentStatus = {
        status: 'completed',
        payment_id: 'pay_123',
        amount: 100
      };
      mockedAxios.get.mockResolvedValue({ data: mockPaymentStatus });

      const result = await checkPaymentStatus(orderId);

      expect(mockedAxios.get).toHaveBeenCalledWith(`/api/orders/${orderId}/payment-status/`);
      expect(result).toEqual(mockPaymentStatus);
    });

    it('должен обработать ошибку при проверке статуса платежа', async () => {
      const orderId = 123;
      const errorMessage = 'Payment not found';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(checkPaymentStatus(orderId)).rejects.toThrow(errorMessage);
    });
  });

  describe('initiatePayment', () => {
    it('должен успешно инициировать платеж', async () => {
      const orderId = 123;
      const paymentData = {
        payment_method: 'card',
        return_url: 'https://example.com/return'
      };
      const mockPaymentResponse = {
        payment_url: 'https://payment.example.com/pay/123',
        payment_id: 'pay_123'
      };
      mockedAxios.post.mockResolvedValue({ data: mockPaymentResponse });

      const result = await initiatePayment(orderId, paymentData);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `/api/orders/${orderId}/pay/`,
        { payment_method: paymentData }
      );
      expect(result).toEqual(mockPaymentResponse);
    });

    it('должен обработать ошибку при инициации платежа', async () => {
      const orderId = 123;
      const paymentData = { payment_method: 'card' };
      const errorMessage = 'Payment initiation failed';
      mockedAxios.post.mockRejectedValue(new Error(errorMessage));

      await expect(initiatePayment(orderId, paymentData)).rejects.toThrow(errorMessage);
    });
  });
});