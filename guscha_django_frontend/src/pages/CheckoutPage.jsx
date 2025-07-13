import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCartStore } from '../store/cartStore';
import { useToast } from '../hooks/useToast';
import { createOrder } from '../api/ordersApi';
import { fetchUserProfile } from '../api/profileApi';
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
  const [selectedShippingAddress, setSelectedShippingAddress] = useState('');
  const [formData, setFormData] = useState({
    billing_address: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      address: '',
      city: '',
      postal_code: '',
      country: 'Россия'
    },
    shipping_address: {
      first_name: '',
      last_name: '',
      address: '',
      city: '',
      postal_code: '',
      country: 'Россия'
    },
    shipping_method: 'standard',
    payment_method: 'card',
    notes: '',
    use_same_address: true
  });

  // Функция для загрузки сохраненных адресов
  const fetchSavedAddresses = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      
      const response = await fetch('/api/users/addresses', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setSavedAddresses(data.addresses || []);
      }
    } catch (error) {
      console.error('Ошибка загрузки адресов:', error);
    }
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

  // Проверяем, есть ли товары в корзине и загружаем адреса и данные пользователя
  useEffect(() => {
    if (items.length === 0) {
      navigate('/');
      showError('Корзина пуста. Добавьте товары перед оформлением заказа.');
    } else {
      fetchSavedAddresses();
      fetchUserData();
    }
  }, [items.length]); // eslint-disable-line react-hooks/exhaustive-deps

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
  const handleAddressSelect = (addressId, type) => {
    const address = savedAddresses.find(addr => addr.id === parseInt(addressId));
    if (!address) return;

    const addressData = {
      first_name: address.first_name,
      last_name: address.last_name,
      email: formData.billing_address.email, // Email остается из формы
      phone: formData.billing_address.phone, // Телефон остается из формы
      address: address.address_line2 
        ? `${address.address_line1}, ${address.address_line2}` 
        : address.address_line1,
      city: address.city,
      postal_code: address.postal_code,
      country: address.country || 'Россия'
    };

    if (type === 'billing') {
      setSelectedBillingAddress(addressId);
      setFormData({
        ...formData,
        billing_address: {
          ...formData.billing_address,
          ...addressData
        }
      });
    } else {
      setSelectedShippingAddress(addressId);
      setFormData({
        ...formData,
        shipping_address: addressData
      });
    }
  };

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setFormData({
      ...formData,
      [name]: checked
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Если выбрана опция "Адрес доставки совпадает с адресом плательщика"
      const checkoutData = {
        ...formData,
        shipping_address: formData.use_same_address 
          ? formData.billing_address 
          : formData.shipping_address
      };
      
      // Удаляем служебное поле, которое не нужно отправлять на сервер
      delete checkoutData.use_same_address;
      
      const orderResult = await createOrder(checkoutData);
      
      // Очищаем корзину после успешного оформления заказа
      await clearCart();
      
      showSuccess('Заказ успешно оформлен!');
      
      // Перенаправляем на страницу подтверждения заказа
      navigate(`/order-confirmation/${orderResult.order_id}`);
    } catch (error) {
      showError(error.response?.data?.message || 'Произошла ошибка при оформлении заказа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="checkout-page">
      <h1>Оформление заказа</h1>
      
      <div className="checkout-container">
        <form className="checkout-form" onSubmit={handleSubmit}>
          <div className="form-section">
            <h2>Информация о плательщике</h2>
            
            {savedAddresses.length > 0 && (
              <div className="form-group">
                <label htmlFor="billing_address_select">Выберите сохраненный адрес</label>
                <select
                  id="billing_address_select"
                  value={selectedBillingAddress}
                  onChange={(e) => handleAddressSelect(e.target.value, 'billing')}
                >
                  <option value="">Ввести новый адрес</option>
                  {savedAddresses.map((address) => (
                    <option key={address.id} value={address.id}>
                      {address.first_name} {address.last_name}, {address.city}, {address.address_line1}
                      {address.address_line2 && `, ${address.address_line2}`}
                    </option>
                  ))}
                </select>
              </div>
            )}
            
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
              <label htmlFor="billing_address">Адрес*</label>
              <input
                type="text"
                id="billing_address"
                name="billing_address.address"
                value={formData.billing_address.address}
                onChange={handleChange}
                required
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
          
          <div className="form-group checkbox-group">
            <input
              type="checkbox"
              id="use_same_address"
              name="use_same_address"
              checked={formData.use_same_address}
              onChange={handleCheckboxChange}
            />
            <label htmlFor="use_same_address">Адрес доставки совпадает с адресом плательщика</label>
          </div>
          
          {!formData.use_same_address && (
            <div className="form-section">
              <h2>Адрес доставки</h2>
              
              {savedAddresses.length > 0 && (
                <div className="form-group">
                  <label htmlFor="shipping_address_select">Выберите сохраненный адрес</label>
                  <select
                    id="shipping_address_select"
                    value={selectedShippingAddress}
                    onChange={(e) => handleAddressSelect(e.target.value, 'shipping')}
                  >
                    <option value="">Ввести новый адрес</option>
                    {savedAddresses.map((address) => (
                      <option key={address.id} value={address.id}>
                        {address.first_name} {address.last_name}, {address.city}, {address.address_line1}
                        {address.address_line2 && `, ${address.address_line2}`}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="shipping_first_name">Имя*</label>
                  <input
                    type="text"
                    id="shipping_first_name"
                    name="shipping_address.first_name"
                    value={formData.shipping_address.first_name}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipping_last_name">Фамилия*</label>
                  <input
                    type="text"
                    id="shipping_last_name"
                    name="shipping_address.last_name"
                    value={formData.shipping_address.last_name}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="shipping_address">Адрес*</label>
                <input
                  type="text"
                  id="shipping_address"
                  name="shipping_address.address"
                  value={formData.shipping_address.address}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="shipping_city">Город*</label>
                  <input
                    type="text"
                    id="shipping_city"
                    name="shipping_address.city"
                    value={formData.shipping_address.city}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipping_postal_code">Почтовый индекс*</label>
                  <input
                    type="text"
                    id="shipping_postal_code"
                    name="shipping_address.postal_code"
                    value={formData.shipping_address.postal_code}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
            </div>
          )}
          
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
          
          <button type="submit" className="checkout-button" disabled={loading}>
            {loading ? 'Оформление...' : 'Оформить заказ'}
          </button>
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
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;