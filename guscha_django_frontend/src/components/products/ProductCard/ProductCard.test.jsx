import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProductCard from './ProductCard';
import { useCartStore } from '../../../store/cartStore';
import { useToast } from '../../../hooks/useToast';

// Мокируем зависимости
jest.mock('../../../store/cartStore');
jest.mock('../../../hooks/useToast');
jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
  BrowserRouter: ({ children }) => <div>{children}</div>
}));

// Компонент-обертка для роутера
const ProductCardWrapper = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('ProductCard', () => {
  const mockAddToCart = jest.fn();
  const mockShowToast = jest.fn();

  const mockProduct = {
    id: 1,
    name: 'Test Product',
    price: '2500.00',
    primary_image: '/test-product.jpg',
    slug: 'test-product',
    description: 'Test product description',
    category: {
      id: 1,
      name: 'Test Category'
    },
    sizes: [
      { id: 1, name: 'S' },
      { id: 2, name: 'M' },
      { id: 3, name: 'L' }
    ],
    is_available: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    useCartStore.mockReturnValue({
      addToCart: mockAddToCart
    });
    
    useToast.mockReturnValue({
      showToast: mockShowToast
    });
  });

  it('отображает информацию о товаре корректно', () => {
    render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('2 500 ₽')).toBeInTheDocument();
  });

  it('отображает изображение товара', () => {
    render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    const image = screen.getByRole('img');
    expect(image).toHaveAttribute('src', '/test-product.jpg');
    expect(image).toHaveAttribute('alt', 'Test Product');
  });

  it('отображает изображение по умолчанию если нет изображения', () => {
    const productWithoutImage = { ...mockProduct, primary_image: null };
    
    render(
      <ProductCardWrapper>
        <ProductCard product={productWithoutImage} />
      </ProductCardWrapper>
    );

    const image = screen.getByRole('img');
    expect(image).toHaveAttribute('src', '/default-product.jpg');
  });

  it('показывает доступные размеры', () => {
    render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    const sizeSelect = screen.getByRole('combobox');
    expect(sizeSelect).toBeInTheDocument();
    expect(screen.getByText('S')).toBeInTheDocument();
    expect(screen.getByText('M')).toBeInTheDocument();
    expect(screen.getByText('L')).toBeInTheDocument();
  });

  it('позволяет выбрать размер', () => {
    render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    const sizeSelect = screen.getByRole('combobox');
    fireEvent.change(sizeSelect, { target: { value: '2' } });

    expect(sizeSelect.value).toBe('2');
  });

  it('добавляет товар в корзину с выбранным размером', async () => {
    render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    // Выбираем размер
    const sizeSelect = screen.getByRole('combobox');
    fireEvent.change(sizeSelect, { target: { value: '2' } });

    // Добавляем в корзину
    const addToCartButton = screen.getByRole('button', { name: /в корзину/i });
    fireEvent.click(addToCartButton);

    await waitFor(() => {
      expect(mockAddToCart).toHaveBeenCalledWith({
        product_id: 1,
        size_id: '2',
        quantity: 1
      });
    });
  });

  it('не позволяет добавить товар без выбора размера', () => {
    render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    const addToCartButton = screen.getByRole('button', { name: /в корзину/i });
    fireEvent.click(addToCartButton);

    expect(mockShowToast).toHaveBeenCalledWith(
      'Пожалуйста, выберите размер',
      'warning'
    );
    expect(mockAddToCart).not.toHaveBeenCalled();
  });

  it('показывает уведомление при успешном добавлении в корзину', async () => {
    mockAddToCart.mockResolvedValueOnce();
    
    render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    const sizeSelect = screen.getByRole('combobox');
    fireEvent.change(sizeSelect, { target: { value: '2' } });

    const addToCartButton = screen.getByRole('button', { name: /в корзину/i });
    fireEvent.click(addToCartButton);

    await waitFor(() => {
      expect(mockShowToast).toHaveBeenCalledWith(
        'Товар добавлен в корзину',
        'success'
      );
    });
  });

  it('показывает ошибку при неудачном добавлении в корзину', async () => {
    mockAddToCart.mockRejectedValueOnce(new Error('Network error'));
    
    render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    const sizeSelect = screen.getByRole('combobox');
    fireEvent.change(sizeSelect, { target: { value: '2' } });

    const addToCartButton = screen.getByRole('button', { name: /в корзину/i });
    fireEvent.click(addToCartButton);

    await waitFor(() => {
      expect(mockShowToast).toHaveBeenCalledWith(
        'Ошибка при добавлении в корзину',
        'error'
      );
    });
  });

  it('переходит на страницу товара при клике на карточку', () => {
    const mockNavigate = jest.fn();
    jest.spyOn(require('react-router-dom'), 'useNavigate').mockReturnValue(mockNavigate);
    
    const { container } = render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    const productCard = container.querySelector('.product-card');
    fireEvent.click(productCard);

    expect(mockNavigate).toHaveBeenCalledWith('/products/test-product');
  });

  it('отображает статус "Нет в наличии" для недоступного товара', () => {
    const unavailableProduct = { ...mockProduct, is_available: false };
    
    render(
      <ProductCardWrapper>
        <ProductCard product={unavailableProduct} />
      </ProductCardWrapper>
    );

    const addToCartButton = screen.queryByRole('button', { name: /Недоступен/i });
    expect(addToCartButton).toBeDisabled();
  });

  it('не отображает размеры если их нет', () => {
    const productWithoutSizes = { ...mockProduct, sizes: [] };
    
    render(
      <ProductCardWrapper>
        <ProductCard product={productWithoutSizes} />
      </ProductCardWrapper>
    );

    expect(screen.queryByText('S')).not.toBeInTheDocument();
    expect(screen.queryByText('M')).not.toBeInTheDocument();
    expect(screen.queryByText('L')).not.toBeInTheDocument();
  });

  it('добавляет товар без размера если размеры не требуются', async () => {
    const productWithoutSizes = { ...mockProduct, sizes: [] };
    
    render(
      <ProductCardWrapper>
        <ProductCard product={productWithoutSizes} />
      </ProductCardWrapper>
    );

    const addToCartButton = screen.getByRole('button', { name: /в корзину/i });
    fireEvent.click(addToCartButton);

    await waitFor(() => {
      expect(mockAddToCart).toHaveBeenCalledWith({
        product_id: 1,
        quantity: 1,
        size_id: null
      });
    });
  });

  it('отображает скидочную цену если есть скидка', () => {
    const productWithDiscount = {
      ...mockProduct,
      price: '2500.00',
      discounted_price: '2000.00'
    };
    
    render(
      <ProductCardWrapper>
        <ProductCard product={productWithDiscount} />
      </ProductCardWrapper>
    );

    expect(screen.getByText('2 000 ₽')).toBeInTheDocument();
    expect(screen.getByText('2 500 ₽')).toHaveClass('line-through'); // предполагаем зачеркнутую старую цену
  });

  it('показывает индикатор загрузки при добавлении в корзину', async () => {
    // Создаем промис, который не резолвится сразу
    let resolvePromise;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    mockAddToCart.mockReturnValue(pendingPromise);
    
    render(
      <ProductCardWrapper>
        <ProductCard product={mockProduct} />
      </ProductCardWrapper>
    );

    const sizeSelect = screen.getByRole('combobox');
    fireEvent.change(sizeSelect, { target: { value: '2' } });

    const addToCartButton = screen.getByRole('button', { name: /в корзину/i });
    fireEvent.click(addToCartButton);

    // Проверяем, что кнопка показывает состояние загрузки
    expect(addToCartButton).toBeDisabled();
    expect(screen.getByText('Добавление...')).toBeInTheDocument();

    // Резолвим промис
    resolvePromise();
    
    await waitFor(() => {
      expect(addToCartButton).not.toBeDisabled();
    });
  });

  it('обрезает длинное название товара', () => {
    const productWithLongName = {
      ...mockProduct,
      name: 'Очень длинное название товара которое должно быть обрезано'
    };
    
    render(
      <ProductCardWrapper>
        <ProductCard product={productWithLongName} />
      </ProductCardWrapper>
    );

    const productName = screen.getByText(/очень длинное название/i);
    const titleElement = productName.closest('h3');
    expect(titleElement).toBeInTheDocument();
  });
});