import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCartStore } from '../store/cartStore';
import { useToast } from '../hooks/useToast';
import { createOrder } from '../api/ordersApi';
import { fetchUserProfile } from '../api/profileApi';
import { createCartReservations } from '../api/cartApi';
import addressesApi from '../api/addresses';
import '../styles/CheckoutPage.css';
import { getProductImageUrl, getProductName } from '../utils/imageUtils';

const CheckoutPage = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();
  const items = useCartStore((state) => state.items);
  const total = useCartStore((state) => state.total);
  const clearCart = useCartStore((state) => state.clearCart);

  const [loading, setLoading] = useState(false);
  const [savedAddresses, setSavedAddresses] = useState([]);
  const [selectedBillingAddress, setSelectedBillingAddress] = useState('');

  const [formData, setFormData] = useState({
    billing_address: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      address_line1: '',
      address_line2: '',
      city: '',
      postal_code: '',
      country: 'Россия'
    },

    shipping_method: 'standard',
    payment_method: 'card',
    notes: ''
  });

  // Функция для загрузки сохраненных адресов
  const fetchSavedAddresses = async () => {
    console.log('🔥 НАЧАЛО fetchSavedAddresses - функция вызвана!');
    try {
      // Токен теперь в httpOnly cookie, поэтому просто пробуем загрузить адреса

      console.log('🏠 Загружаем сохраненные адреса...');
      const response = await addressesApi.getAddresses();
      console.log('🔥 Ответ от API:', response);

      if (response.data) {
        // API возвращает массив адресов напрямую
        const addresses = Array.isArray(response.data) ? response.data : response.data.results || [];
        console.log('🏠 Загружено адресов:', addresses.length, addresses);
        setSavedAddresses(addresses);
      } else {
        console.log('🔥 response.data пустой:', response.data);
      }
    } catch (error) {
      console.error('🔥 ОШИБКА в fetchSavedAddresses:', error);
      console.error('🔥 Детали ошибки:', error.response?.data);
      console.error('🔥 Статус ошибки:', error.response?.status);
      // Не показываем ошибку пользователю, так как это не критично
    }
    console.log('🔥 КОНЕЦ fetchSavedAddresses');
  };

  // Загрузка данных пользователя, если он авторизован
  const fetchUserData = async () => {
    try {
      const userData = await fetchUserProfile();
      if (userData) {
        setFormData(prev => ({
          ...prev,
          billing_address: {
            ...prev.billing_address,
            first_name: userData.first_name || '',
            last_name: userData.last_name || '',
            email: userData.email || '',
            phone: userData.phone || ''
          }
        }));
      }
    } catch (error) {
      console.error('Ошибка загрузки данных пользователя:', error);
    }
  };

  // Создание резервирований для товаров в корзине
  const createReservations = async () => {
    try {
      console.log('🛒 Создаем резервирования для товаров в корзине...');
      const result = await createCartReservations();
      console.log('🛒 Резервирования созданы:', result);

      if (result.errors && result.errors.length > 0) {
        console.warn('🛒 Некоторые товары не удалось зарезервировать:', result.errors);
        showError('Некоторые товары могут быть недоступны. Проверьте корзину.');
        return;
      }

      // Подсчитываем новые и существующие резервирования
      const newReservations = result.reservations_created?.filter(r => r.status === 'created') || [];
      const existingReservations = result.reservations_created?.filter(r => r.status === 'already_exists') || [];

      if (newReservations.length > 0) {
        console.log(`🛒 Создано новых резервирований: ${newReservations.length}`);
        showSuccess(`Товары зарезервированы на 30 минут (${newReservations.length} новых)`);
      } else if (existingReservations.length > 0) {
        console.log(`🛒 Все товары уже зарезервированы: ${existingReservations.length}`);
        // Не показываем уведомление, если все резервирования уже существуют
      } else {
        console.log('🛒 Нет товаров для резервирования');
      }
    } catch (error) {
      console.error('🛒 Ошибка создания резервирований:', error);
      showError('Не удалось зарезервировать товары. Некоторые позиции могут быть недоступны.');
    }
  };

  // Проверяем, есть ли товары в корзине и загружаем адреса и данные пользователя
  useEffect(() => {
    console.log('🔥 useEffect ЗАПУЩЕН! items.length:', items.length);
    if (items.length === 0) {
      console.log('🔥 Корзина пуста, перенаправляем на главную');
      navigate('/');
      showError('Корзина пуста. Добавьте товары перед оформлением заказа.');
    } else {
      console.log('🔥 Корзина НЕ пуста, загружаем данные...');
      // Создаем резервирования для товаров в корзине
      createReservations();
      console.log('🔥 Вызываем fetchSavedAddresses...');
      fetchSavedAddresses();
      console.log('🔥 Вызываем fetchUserData...');
      fetchUserData();
    }
  }, [items.length]); // eslint-disable-line react-hooks/exhaustive-deps

  // Проверка валидности формы
  const isFormValid = 
    formData.billing_address.first_name.trim() !== '' &&
    formData.billing_address.last_name.trim() !== '' &&
    formData.billing_address.email.trim() !== '' &&
    formData.billing_address.phone.trim() !== '' &&
    formData.billing_address.address_line1.trim() !== '' &&
    formData.billing_address.city.trim() !== '' &&
    formData.billing_address.postal_code.trim() !== '';

  const handleChange = (e) => {
    const { name, value } = e.target;

    if (name.includes('.')) {
      const [section, field] = name.split('.');
      setFormData({
        ...formData,
        [section]: {
          ...formData[section],
          [field]: value
        }
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };

  // Функция для выбора сохраненного адреса
  const handleAddressSelect = (addressId) => {
    const address = savedAddresses.find(addr => addr.id === parseInt(addressId));
    if (!address) return;

    console.log('🏠 Выбран адрес:', address);
    console.log('🏠 full_address:', address.full_address);
    console.log('🏠 Отдельные поля:', {
      address_line1: address.address_line1,
      address_line2: address.address_line2,
      city: address.city,
      postal_code: address.postal_code
    });

    // Парсим full_name в first_name и last_name
    const fullName = address.full_name || `${address.first_name || ''} ${address.last_name || ''}`.trim();
    const nameParts = fullName.split(' ');
    const firstName = nameParts[0] || '';
    const lastName = nameParts.slice(1).join(' ') || '';

    // Парсим full_address или используем отдельные поля
    let addressData = {
      first_name: firstName,
      last_name: lastName,
      address_line1: address.address_line1 || '',
      address_line2: address.address_line2 || '', // Используем квартиру из сохраненного адреса
      city: address.city || '',
      postal_code: address.postal_code || '',
      country: address.country || 'Россия'
    };

    // Если есть full_address, попробуем извлечь из него данные
    if (address.full_address) {
      console.log('🏠 Парсим full_address:', address.full_address);

      // Разделяем по запятым и анализируем структуру
      const addressParts = address.full_address.split(',').map(part => part.trim());
      console.log('🏠 Части адреса:', addressParts);

      // Реальный формат: "Улица дом", "Квартира", "Город", "Индекс", "Страна" (5 частей)
      // Исправляем логику парсинга согласно фактическому формату
      if (addressParts.length >= 1) {
        // Первая часть - улица и номер дома
        addressData.address_line1 = addressParts[0];
      }
      if (addressParts.length >= 2) {
        // Вторая часть - квартира
        addressData.address_line2 = addressParts[1];
      }
      if (addressParts.length >= 3) {
        // Третья часть - город
        addressData.city = addressParts[2];
      }
      if (addressParts.length >= 4) {
        // Четвертая часть - почтовый индекс
        addressData.postal_code = addressParts[3];
      }
      if (addressParts.length >= 5) {
        // Пятая часть - страна
        addressData.country = addressParts[4];
      }

      console.log('🏠 Результат парсинга:', addressData);
    }

    setSelectedBillingAddress(addressId);
    setFormData({
      ...formData,
      billing_address: {
        ...formData.billing_address,
        ...addressData,
        // Email и phone берем из адреса, если есть, иначе оставляем из профиля
        email: formData.billing_address.email, // Email остается из профиля пользователя
        phone: address.phone || formData.billing_address.phone // Phone из адреса или профиля
      }
    });

    console.log('🏠 Финальные данные формы:', {
      ...formData,
      billing_address: {
        ...formData.billing_address,
        ...addressData,
        email: formData.billing_address.email,
        phone: address.phone || formData.billing_address.phone
      }
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Подготавливаем данные для создания заказа в формате, ожидаемом OrderCreateSerializer
      const checkoutData = {
        email: formData.billing_address.email,
        subtotal: total,
        tax: 0, // Пока налоги не рассчитываются
        shipping: 0, // Пока доставка бесплатная
        discount: 0, // Пока скидки нет
        total,
        shipping_method: formData.shipping_method,
        payment_method: formData.payment_method,
        notes: formData.notes
      };

      // Если выбран сохраненный адрес, добавляем его ID
      if (selectedBillingAddress) {
        checkoutData.billing_address_id = parseInt(selectedBillingAddress);
      }

      console.log('Отправляем данные заказа:', checkoutData);

      const orderResult = await createOrder(checkoutData);

      // Очищаем корзину после успешного оформления заказа
      await clearCart();

      showSuccess('Заказ успешно оформлен!');

      // Перенаправляем на страницу подтверждения заказа
      navigate(`/order-confirmation/${orderResult.id}`);
    } catch (error) {
      console.error('Ошибка при создании заказа:', error);
      showError(error.response?.data?.detail || error.response?.data?.message || 'Произошла ошибка при оформлении заказа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="checkout-page">
      <h1>Оформление заказа</h1>

      <div className="checkout-container">
        <form id="checkout-form" className="checkout-form" onSubmit={handleSubmit}>
          <div className="form-section">
            <h2>Информация о плательщике</h2>

            <div className="form-group">
              <label htmlFor="billing_address_select">Сохранённые адреса</label>
              <select
                id="billing_address_select"
                value={selectedBillingAddress}
                onChange={(e) => handleAddressSelect(e.target.value)}
                className="address-select"
              >
                <option value="">-- Выберите адрес или введите новый --</option>
                {savedAddresses.map((address) => (
                  <option key={address.id} value={address.id}>
                    {address.full_name || `${address.first_name || ''} ${address.last_name || ''}`.trim()} |
                    {address.full_address || (
                      `${address.address_line1 || ''}${address.address_line2 ? `, ${address.address_line2}` : ''}, ${address.city || ''}, ${address.postal_code || ''}`
                    )}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="billing_first_name">Имя*</label>
                <input
                  type="text"
                  id="billing_first_name"
                  name="billing_address.first_name"
                  value={formData.billing_address.first_name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="billing_last_name">Фамилия*</label>
                <input
                  type="text"
                  id="billing_last_name"
                  name="billing_address.last_name"
                  value={formData.billing_address.last_name}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="billing_email">Email*</label>
                <input
                  type="email"
                  id="billing_email"
                  name="billing_address.email"
                  value={formData.billing_address.email}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="billing_phone">Телефон*</label>
                <input
                  type="tel"
                  id="billing_phone"
                  name="billing_address.phone"
                  value={formData.billing_address.phone}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="billing_address_line1">Адрес*</label>
              <input
                type="text"
                id="billing_address_line1"
                name="billing_address.address_line1"
                value={formData.billing_address.address_line1}
                onChange={handleChange}
                placeholder="Улица, номер дома"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="billing_address_line2">Квартира/Офис</label>
              <input
                type="text"
                id="billing_address_line2"
                name="billing_address.address_line2"
                value={formData.billing_address.address_line2}
                onChange={handleChange}
                placeholder="Квартира, офис, подъезд"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="billing_city">Город*</label>
                <input
                  type="text"
                  id="billing_city"
                  name="billing_address.city"
                  value={formData.billing_address.city}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="billing_postal_code">Почтовый индекс*</label>
                <input
                  type="text"
                  id="billing_postal_code"
                  name="billing_address.postal_code"
                  value={formData.billing_address.postal_code}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h2>Способ доставки</h2>
            <div className="radio-group">
              <div className="radio-option">
                <input
                  type="radio"
                  id="shipping_standard"
                  name="shipping_method"
                  value="standard"
                  checked={formData.shipping_method === 'standard'}
                  onChange={handleChange}
                />
                <label htmlFor="shipping_standard">
                  <span className="radio-title">Стандартная доставка</span>
                  <span className="radio-description">3-5 рабочих дней</span>
                </label>
              </div>

              <div className="radio-option">
                <input
                  type="radio"
                  id="shipping_express"
                  name="shipping_method"
                  value="express"
                  checked={formData.shipping_method === 'express'}
                  onChange={handleChange}
                />
                <label htmlFor="shipping_express">
                  <span className="radio-title">Экспресс-доставка</span>
                  <span className="radio-description">1-2 рабочих дня</span>
                </label>
              </div>
            </div>
          </div>

          <div className="form-section">
            <h2>Способ оплаты</h2>
            <div className="radio-group">
              <div className="radio-option">
                <input
                  type="radio"
                  id="payment_sbp"
                  name="payment_method"
                  value="sbp"
                  checked={formData.payment_method === 'sbp'}
                  onChange={handleChange}
                />
                <label htmlFor="payment_sbp">
                  <span className="radio-title">СБП</span>
                </label>
              </div>

              <div className="radio-option">
                <input
                  type="radio"
                  id="payment_card"
                  name="payment_method"
                  value="card"
                  checked={formData.payment_method === 'card'}
                  onChange={handleChange}
                />
                <label htmlFor="payment_card">
                  <span className="radio-title">Банковская карта</span>
                </label>
              </div>

              <div className="radio-option">
                <input
                  type="radio"
                  id="payment_foreign_card"
                  name="payment_method"
                  value="foreign_card"
                  checked={formData.payment_method === 'foreign_card'}
                  onChange={handleChange}
                />
                <label htmlFor="payment_foreign_card">
                  <span className="radio-title">Зарубежная карта</span>
                </label>
              </div>

              <div className="radio-option">
                <input
                  type="radio"
                  id="payment_dolyami"
                  name="payment_method"
                  value="dolyami"
                  checked={formData.payment_method === 'dolyami'}
                  onChange={handleChange}
                />
                <label htmlFor="payment_dolyami">
                  <span className="radio-title">Долями</span>
                </label>
              </div>

              <div className="radio-option">
                <input
                  type="radio"
                  id="payment_podeli"
                  name="payment_method"
                  value="podeli"
                  checked={formData.payment_method === 'podeli'}
                  onChange={handleChange}
                />
                <label htmlFor="payment_podeli">
                  <span className="radio-title">Подели</span>
                </label>
              </div>
            </div>
          </div>

          <div className="form-section">
            <h2>Дополнительная информация</h2>
            <div className="form-group">
              <label htmlFor="notes">Примечания к заказу</label>
              <textarea
                id="notes"
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                placeholder="Дополнительная информация о заказе"
              />
            </div>
          </div>

        </form>

        <div className="order-summary">
          <h2>Ваш заказ</h2>
          <div className="order-items">
            {items.map((item) => {
              const productImage = getProductImageUrl(item);
              const productName = getProductName(item);

              return (
                <div key={item.id} className="order-item">
                  {productImage && (
                    <div className="item-image">
                      <img src={productImage} alt={productName} />
                    </div>
                  )}
                  <div className="item-info">
                    <span className="item-name">{productName}</span>
                    {item.size_name && <span className="item-size">Размер: {item.size_name}</span>}
                    <span className="item-quantity">Количество: {item.quantity}</span>
                  </div>
                  <span className="item-price">{((parseFloat(item.price) || 0) * (item.quantity || 0)).toFixed(2)} ₽</span>
                </div>
              );
            })}
          </div>

          <div className="order-totals">
            <div className="total-row">
              <span>Подытог:</span>
              <span>{(total || 0).toFixed(2)} ₽</span>
            </div>
            <div className="total-row">
              <span>Доставка:</span>
              <span>{formData.shipping_method === 'express' ? '300.00' : '150.00'} ₽</span>
            </div>
            <div className="total-row grand-total">
              <span>Итого:</span>
              <span>
                {((total || 0) + (formData.shipping_method === 'express' ? 300 : 150)).toFixed(2)} ₽
              </span>
            </div>
          </div>

          <button 
            type="submit" 
            form="checkout-form"
            className="checkout-button" 
            disabled={loading || !isFormValid}
          >
            {loading ? 'Оформление...' : 'Оформить заказ'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;