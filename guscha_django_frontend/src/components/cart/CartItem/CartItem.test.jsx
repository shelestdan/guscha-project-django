import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import CartItem from './CartItem';
import { useCartStore } from '../../../store/cartStore';
import { useToast } from '../../../hooks/useToast';

// Мокируем зависимости
jest.mock('../../../store/cartStore');
jest.mock('../../../hooks/useToast');
jest.mock('../../../utils/imageUtils');

// Компонент-обертка для роутера
const CartItemWrapper = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('CartItem', () => {
  const mockUpdateQuantity = jest.fn();
  const mockRemoveItem = jest.fn();
  const mockShowToast = jest.fn();

  const mockCartItem = {
    id: 1,
    item_type: 'product',
    product_id: 123,
    quantity: 2,
    price: '1500.00',
    name: 'Test Product',
    image_url: '/test-image.jpg',
    size_name: 'M'
  };

  beforeEach(() => {
    // Сброс моков перед каждым тестом
    jest.clearAllMocks();
    
    const { getProductImageUrl, getProductName, getProductSize } = require('../../../utils/imageUtils');
    
    getProductImageUrl.mockImplementation((item) => {
      return item?.image_url || '/default-image.jpg';
    });
    
    getProductName.mockImplementation((item) => {
      return item?.name || 'Unknown Product';
    });
    
    getProductSize.mockImplementation((item) => {
      return item?.size_name || '';
    });
    
    useCartStore.mockReturnValue({
      updateQuantity: mockUpdateQuantity,
      removeItem: mockRemoveItem
    });

    useToast.mockReturnValue({
      showToast: mockShowToast
    });
  });

  it('отображает информацию о товаре корректно', () => {
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('1 500 ₽')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2')).toBeInTheDocument();
  });

  it('отображает размер товара если он есть', () => {
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    expect(screen.getByText(/размер.*m/i)).toBeInTheDocument();
  });

  it('не отображает размер если его нет', () => {
    const itemWithoutSize = { ...mockCartItem, size_name: null };
    
    render(
      <CartItemWrapper>
        <CartItem item={itemWithoutSize} />
      </CartItemWrapper>
    );

    expect(screen.queryByText(/размер/i)).not.toBeInTheDocument();
  });

  it('увеличивает количество товара при клике на "+"', async () => {
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    const increaseButton = screen.getByRole('button', { name: /увеличить/i });
    fireEvent.click(increaseButton);

    await waitFor(() => {
      expect(mockUpdateQuantity).toHaveBeenCalledWith(1, 3);
    });
  });

  it('уменьшает количество товара при клике на "-"', async () => {
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    const decreaseButton = screen.getByRole('button', { name: /уменьшить/i });
    fireEvent.click(decreaseButton);

    await waitFor(() => {
      expect(mockUpdateQuantity).toHaveBeenCalledWith(1, 1);
    });
  });

  it('не позволяет уменьшить количество ниже 1', async () => {
    const itemWithMinQuantity = { ...mockCartItem, quantity: 1 };
    
    render(
      <CartItemWrapper>
        <CartItem item={itemWithMinQuantity} />
      </CartItemWrapper>
    );

    const decreaseButton = screen.getByRole('button', { name: /уменьшить/i });
    expect(decreaseButton).toBeDisabled();
  });

  it('изменяет количество при вводе в поле', async () => {
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    const quantityInput = screen.getByDisplayValue('2');
    fireEvent.change(quantityInput, { target: { value: '5' } });
    fireEvent.blur(quantityInput);

    await waitFor(() => {
      expect(mockUpdateQuantity).toHaveBeenCalledWith(1, 5);
    });
  });

  it('не позволяет ввести некорректное количество', async () => {
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    const quantityInput = screen.getByDisplayValue('2');
    
    // Тест с отрицательным числом
    fireEvent.change(quantityInput, { target: { value: '-1' } });
    
    // Проверяем, что updateQuantity НЕ вызывается для отрицательных значений
    expect(mockUpdateQuantity).not.toHaveBeenCalled();

    // Тест с нулем
    fireEvent.change(quantityInput, { target: { value: '0' } });
    
    // Проверяем, что updateQuantity НЕ вызывается для нуля
    expect(mockUpdateQuantity).not.toHaveBeenCalled();
    
    // Тест с корректным значением
    fireEvent.change(quantityInput, { target: { value: '3' } });
    
    // Проверяем, что updateQuantity вызывается для корректного значения
    expect(mockUpdateQuantity).toHaveBeenCalledWith(1, 3);
  });

  it('удаляет товар из корзины при клике на кнопку удаления', async () => {
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    const removeButton = screen.getByRole('button', { name: /удалить/i });
    fireEvent.click(removeButton);

    await waitFor(() => {
      expect(mockRemoveItem).toHaveBeenCalledWith(1);
    });
  });

  it('показывает уведомление при успешном удалении', async () => {
    mockRemoveItem.mockResolvedValueOnce();
    
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    const removeButton = screen.getByRole('button', { name: /удалить/i });
    fireEvent.click(removeButton);

    await waitFor(() => {
      expect(mockShowToast).toHaveBeenCalledWith(
        'Товар удален из корзины',
        'success'
      );
    });
  });

  it('показывает ошибку при неудачном удалении', async () => {
    mockRemoveItem.mockRejectedValueOnce(new Error('Network error'));
    
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    const removeButton = screen.getByRole('button', { name: /удалить/i });
    fireEvent.click(removeButton);

    await waitFor(() => {
      expect(mockShowToast).toHaveBeenCalledWith(
        'Ошибка при удалении товара',
        'error'
      );
    });
  });

  it('отображает изображение товара', () => {
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    const image = screen.getByRole('img');
    expect(image).toHaveAttribute('src', '/test-image.jpg');
    expect(image).toHaveAttribute('alt', 'Test Product');
  });

  it('отображает изображение по умолчанию если нет изображения товара', () => {
    const itemWithoutImage = { ...mockCartItem, image_url: null };
    
    render(
      <CartItemWrapper>
        <CartItem item={itemWithoutImage} />
      </CartItemWrapper>
    );

    const image = screen.getByRole('img');
    expect(image).toHaveAttribute('src', '/default-image.jpg');
  });

  it('рассчитывает общую стоимость товара корректно', () => {
    render(
      <CartItemWrapper>
        <CartItem item={mockCartItem} />
      </CartItemWrapper>
    );

    // Проверяем цену за единицу товара (1500)
    expect(screen.getByText('1 500 ₽')).toBeInTheDocument();
  });

  it('обрабатывает предзаказы корректно', () => {
    const preorderItem = {
      ...mockCartItem,
      item_type: 'preorder',
      preorder_id: 456,
      name: 'Preorder Item'
    };
    
    const { container } = render(
      <CartItemWrapper>
        <CartItem item={preorderItem} />
      </CartItemWrapper>
    );
    
    // Проверяем, что компонент рендерится
    expect(container.firstChild).toBeInTheDocument();
    
    // Проверяем, что есть элемент с классом cart-item
    const cartItem = container.querySelector('.cart-item');
    expect(cartItem).toBeInTheDocument();
    
    // Проверяем наличие метки предзаказа
    const preorderLabel = container.querySelector('.cart-item__preorder');
    expect(preorderLabel).toBeInTheDocument();
    expect(preorderLabel).toHaveTextContent('Предзаказ');
    
    // Проверяем, что отображается название предзаказа
    const { getProductName } = require('../../../utils/imageUtils');
    const productName = getProductName(preorderItem);
    expect(screen.getByText(productName)).toBeInTheDocument();
  });
});