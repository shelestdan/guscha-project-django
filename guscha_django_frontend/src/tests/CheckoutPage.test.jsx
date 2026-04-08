import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import CheckoutPage from '../pages/CheckoutPage';
import { useCartStore } from '../store/cartStore';
import { useToast } from '../hooks/useToast';
import { createOrder } from '../api/ordersApi';
import { fetchUserProfile } from '../api/profileApi';
import { createCartReservations } from '../api/cartApi';
import addressesApi from '../api/addresses';

// Мокируем зависимости
jest.mock('../store/cartStore');
jest.mock('../hooks/useToast');
jest.mock('../api/ordersApi');
jest.mock('../api/profileApi');
jest.mock('../api/cartApi');
jest.mock('../api/addresses');
jest.mock('../utils/imageUtils', () => ({
  getProductImageUrl: (item) => item.product_image || '/default-product.jpg',
  getProductName: (item) => item.product_name || 'Test Product'
}));
jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
  BrowserRouter: ({ children }) => <div>{children}</div>
}));

// Компонент-обертка для роутера
const CheckoutPageWrapper = ({ children }) => (
  <div>{children}</div>
);

describe('CheckoutPage', () => {
  const mockNavigate = jest.fn();
  const mockShowSuccess = jest.fn();
  const mockShowError = jest.fn();
  const mockClearCart = jest.fn();

  const mockCartItems = [
    {
      id: 1,
      product_id: 1,
      product_name: 'Test Product 1',
      price: '1500.00',
      quantity: 2,
      size_name: 'M',
      product_image: '/test-image1.jpg'
    },
    {
      id: 2,
      product_id: 2,
      product_name: 'Test Product 2',
      price: '2000.00',
      quantity: 1,
      size_name: 'L',
      product_image: '/test-image2.jpg'
    }
  ];

  const mockUserProfile = {
    first_name: 'Иван',
    last_name: 'Иванов',
    email: 'ivan@example.com',
    phone: '+7 900 123-45-67'
  };

  const mockSavedAddresses = [
    {
      id: 1,
      full_name: 'Иван Иванов',
      full_address: 'ул. Тестовая 1, кв. 10, Москва, 123456, Россия',
      phone: '+7 900 123-45-67'
    },
    {
      id: 2,
      full_name: 'Петр Петров',
      full_address: 'ул. Примерная 2, офис 5, Санкт-Петербург, 654321, Россия',
      phone: '+7 911 987-65-43'
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Мокируем react-router-dom
    jest.spyOn(require('react-router-dom'), 'useNavigate').mockReturnValue(mockNavigate);
    
    // Мокируем localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'mock-token'),
        setItem: jest.fn(),
        removeItem: jest.fn()
      },
      writable: true
    });

    // Мокируем хуки и стор
    useCartStore.mockImplementation((selector) => {
      const state = {
        items: mockCartItems,
        total: 5000,
        clearCart: mockClearCart
      };
      return selector(state);
    });
    
    useToast.mockReturnValue({
      showSuccess: mockShowSuccess,
      showError: mockShowError
    });

    // Мокируем API
    fetchUserProfile.mockResolvedValue(mockUserProfile);
    addressesApi.getAddresses.mockResolvedValue({ data: mockSavedAddresses });
    createCartReservations.mockResolvedValue({
      reservations_created: [
        { status: 'created', product_id: 1 },
        { status: 'created', product_id: 2 }
      ],
      errors: []
    });
    createOrder.mockResolvedValue({ id: 123 });
  });

  it('отображает форму оформления заказа корректно', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    expect(screen.getByText('Оформление заказа')).toBeInTheDocument();
    expect(screen.getByText('Информация о плательщике')).toBeInTheDocument();
    expect(screen.getByText('Способ доставки')).toBeInTheDocument();
    expect(screen.getByText('Способ оплаты')).toBeInTheDocument();
    expect(screen.getByText('Ваш заказ')).toBeInTheDocument();
  });

  it('перенаправляет на главную если корзина пуста', async () => {
    useCartStore.mockImplementation((selector) => {
      const state = {
        items: [],
        total: 0,
        clearCart: mockClearCart
      };
      return selector ? selector(state) : state;
    });

    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    expect(mockNavigate).toHaveBeenCalledWith('/');
    expect(mockShowError).toHaveBeenCalledWith('Корзина пуста. Добавьте товары перед оформлением заказа.');
  });

  it('загружает данные пользователя при инициализации', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    await waitFor(() => {
      expect(fetchUserProfile).toHaveBeenCalled();
      expect(addressesApi.getAddresses).toHaveBeenCalled();
      expect(createCartReservations).toHaveBeenCalled();
    });
  });

  it('заполняет форму данными пользователя', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    await waitFor(() => {
      expect(screen.getByDisplayValue('Иван')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Иванов')).toBeInTheDocument();
      expect(screen.getByDisplayValue('ivan@example.com')).toBeInTheDocument();
      expect(screen.getByDisplayValue('+7 900 123-45-67')).toBeInTheDocument();
    });
  });

  it('отображает сохраненные адреса в селекте', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/Иван Иванов.*ул\. Тестовая 1, кв\. 10, Москва, 123456, Россия/)).toBeInTheDocument();
      expect(screen.getByText(/Петр Петров.*ул\. Примерная 2, офис 5, Санкт-Петербург, 654321, Россия/)).toBeInTheDocument();
    });
  });

  it('заполняет форму при выборе сохраненного адреса', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    await waitFor(() => {
      const addressSelect = screen.getByLabelText('Сохранённые адреса');
      fireEvent.change(addressSelect, { target: { value: '1' } });
    });

    await waitFor(() => {
      expect(screen.getByDisplayValue('ул. Тестовая 1')).toBeInTheDocument();
      expect(screen.getByDisplayValue('кв. 10')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Москва')).toBeInTheDocument();
      expect(screen.getByDisplayValue('123456')).toBeInTheDocument();
    });
  });

  it('обновляет поля формы при вводе', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    const addressInput = screen.getByLabelText('Адрес*');
    fireEvent.change(addressInput, { target: { value: 'ул. Новая 123' } });

    expect(addressInput.value).toBe('ул. Новая 123');
  });

  it('отображает товары в корзине', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    expect(screen.getByText('Test Product 1')).toBeInTheDocument();
    expect(screen.getByText('Test Product 2')).toBeInTheDocument();
    expect(screen.getByText('Размер: M')).toBeInTheDocument();
    expect(screen.getByText('Размер: L')).toBeInTheDocument();
    expect(screen.getByText('Количество: 2')).toBeInTheDocument();
    expect(screen.getByText('Количество: 1')).toBeInTheDocument();
  });

  it('рассчитывает итоговую сумму корректно', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    expect(screen.getByText('5000.00 ₽')).toBeInTheDocument(); // Подытог
    expect(screen.getByText('150.00 ₽')).toBeInTheDocument(); // Стандартная доставка
    expect(screen.getByText('5150.00 ₽')).toBeInTheDocument(); // Итого
  });

  it('изменяет стоимость доставки при выборе экспресс-доставки', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    const expressShipping = screen.getByLabelText(/Экспресс-доставка/);
    fireEvent.click(expressShipping);

    await waitFor(() => {
      expect(screen.getByText('300.00 ₽')).toBeInTheDocument(); // Экспресс доставка
      expect(screen.getByText('5300.00 ₽')).toBeInTheDocument(); // Новый итог
    });
  });

  it('позволяет выбрать способ оплаты', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    const sbpPayment = screen.getByLabelText(/СБП/);
    fireEvent.click(sbpPayment);

    expect(sbpPayment).toBeChecked();
  });

  it('успешно оформляет заказ', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    // Заполняем обязательные поля
    await waitFor(() => {
      const cityInput = screen.getByLabelText('Город*');
      fireEvent.change(cityInput, { target: { value: 'Москва' } });
      
      const postalCodeInput = screen.getByLabelText('Почтовый индекс*');
      fireEvent.change(postalCodeInput, { target: { value: '123456' } });
      
      const addressInput = screen.getByLabelText('Адрес*');
      fireEvent.change(addressInput, { target: { value: 'ул. Тестовая 1' } });
    });

    const submitButton = screen.getByRole('button', { name: /оформить заказ/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(createOrder).toHaveBeenCalledWith(expect.objectContaining({
        email: 'ivan@example.com',
        total: 5000,
        shipping_method: 'standard',
        payment_method: 'card'
      }));
    });

    await waitFor(() => {
      expect(mockClearCart).toHaveBeenCalled();
      expect(mockShowSuccess).toHaveBeenCalledWith('Заказ успешно оформлен!');
      expect(mockNavigate).toHaveBeenCalledWith('/order-confirmation/123');
    });
  });

  it('показывает ошибку при неудачном оформлении заказа', async () => {
    createOrder.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Ошибка создания заказа'
        }
      }
    });

    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    // Заполняем обязательные поля
    await waitFor(() => {
      const cityInput = screen.getByLabelText('Город*');
      fireEvent.change(cityInput, { target: { value: 'Москва' } });
      
      const postalCodeInput = screen.getByLabelText('Почтовый индекс*');
      fireEvent.change(postalCodeInput, { target: { value: '123456' } });
      
      const addressInput = screen.getByLabelText('Адрес*');
      fireEvent.change(addressInput, { target: { value: 'ул. Тестовая 1' } });
    });

    const submitButton = screen.getByRole('button', { name: /оформить заказ/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockShowError).toHaveBeenCalledWith('Ошибка создания заказа');
    });
  });

  it('показывает состояние загрузки при отправке формы', async () => {
    // Создаем промис, который не резолвится сразу
    let resolvePromise;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    createOrder.mockReturnValue(pendingPromise);

    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    // Заполняем обязательные поля
    await waitFor(() => {
      const cityInput = screen.getByLabelText('Город*');
      fireEvent.change(cityInput, { target: { value: 'Москва' } });
      
      const postalCodeInput = screen.getByLabelText('Почтовый индекс*');
      fireEvent.change(postalCodeInput, { target: { value: '123456' } });
      
      const addressInput = screen.getByLabelText('Адрес*');
      fireEvent.change(addressInput, { target: { value: 'ул. Тестовая 1' } });
    });

    const submitButton = screen.getByRole('button', { name: /оформить заказ/i });
    fireEvent.click(submitButton);

    // Проверяем состояние загрузки
    expect(screen.getByText('Оформление...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();

    // Резолвим промис
    resolvePromise({ id: 123 });
    
    await waitFor(() => {
      expect(screen.queryByText('Оформление...')).not.toBeInTheDocument();
    });
  });

  it('создает резервирования товаров при загрузке', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    await waitFor(() => {
      expect(createCartReservations).toHaveBeenCalled();
      expect(mockShowSuccess).toHaveBeenCalledWith('Товары зарезервированы на 30 минут (2 новых)');
    });
  });

  it('показывает ошибку при проблемах с резервированием', async () => {
    createCartReservations.mockResolvedValueOnce({
      reservations_created: [],
      errors: ['Товар недоступен']
    });

    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    await waitFor(() => {
      expect(mockShowError).toHaveBeenCalledWith('Некоторые товары могут быть недоступны. Проверьте корзину.');
    });
  });

  it('обрабатывает ошибки загрузки адресов без показа пользователю', async () => {
    addressesApi.getAddresses.mockRejectedValueOnce(new Error('Network error'));

    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    // Ошибка не должна показываться пользователю
    expect(mockShowError).not.toHaveBeenCalledWith(expect.stringContaining('адрес'));
  });

  it('добавляет примечания к заказу', async () => {
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    const notesTextarea = screen.getByLabelText('Примечания к заказу');
    fireEvent.change(notesTextarea, { target: { value: 'Оставить у двери' } });

    expect(notesTextarea.value).toBe('Оставить у двери');
  });

  it('валидирует обязательные поля формы', async () => {
    // Мокаем пустой профиль пользователя
    fetchUserProfile.mockResolvedValue({ data: {} });
    
    await act(async () => {
      render(
        <CheckoutPageWrapper>
          <CheckoutPage />
        </CheckoutPageWrapper>
      );
    });

    // Ждем загрузки и проверяем, что поля пустые
    await waitFor(() => {
      const firstNameInput = screen.getByLabelText('Имя*');
      expect(firstNameInput.value).toBe('');
    });

    const submitButton = screen.getByRole('button', { name: /оформить заказ/i });
    
    // Проверяем, что поле имеет атрибут required
    const firstNameInput = screen.getByLabelText('Имя*');
    expect(firstNameInput).toHaveAttribute('required');
    
    // В Jest HTML5 валидация не работает, поэтому просто проверим наличие required атрибута
    // В реальном браузере это предотвратило бы отправку формы
  });
});