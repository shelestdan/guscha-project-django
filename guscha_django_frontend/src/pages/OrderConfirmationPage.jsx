import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchOrderDetails } from '../api/ordersApi';
import '../styles/OrderConfirmationPage.css';

const OrderConfirmationPage = () => {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchOrder = async () => {
      try {
        const orderData = await fetchOrderDetails(orderId);
        setOrder(orderData);
      } catch (err) {
        setError('Не удалось загрузить информацию о заказе. Пожалуйста, попробуйте позже.');
      } finally {
        setLoading(false);
      }
    };

    fetchOrder();
  }, [orderId]);

  if (loading) {
    return (
      <div className="order-confirmation-page loading">
        <div className="loading-spinner"></div>
        <p>Загрузка информации о заказе...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="order-confirmation-page error">
        <h1>Ошибка</h1>
        <p>{error}</p>
        <Link to="/" className="button">Вернуться на главную</Link>
      </div>
    );
  }

  return (
    <div className="order-confirmation-page">
      <div className="confirmation-container">
        <div className="confirmation-header">
          <div className="success-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 11.08V12C21.9988 14.1564 21.3005 16.2547 20.0093 17.9818C18.7182 19.709 16.9033 20.9725 14.8354 21.5839C12.7674 22.1953 10.5573 22.1219 8.53447 21.3746C6.51168 20.6273 4.78465 19.2461 3.61096 17.4371C2.43727 15.628 1.87979 13.4881 2.02168 11.3363C2.16356 9.18455 2.99721 7.13631 4.39828 5.49706C5.79935 3.85781 7.69279 2.71537 9.79619 2.24013C11.8996 1.7649 14.1003 1.98232 16.07 2.85999" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 4L12 14.01L9 11.01" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1>Заказ успешно оформлен!</h1>
          <p className="order-number">Номер заказа: <strong>{order?.order_number || orderId}</strong></p>
        </div>
        
        <div className="confirmation-details">
          <p>Спасибо за ваш заказ! Мы отправили подтверждение на указанный вами email.</p>
          
          {order && (
            <div className="order-info">
              <div className="info-section">
                <h2>Информация о заказе</h2>
                <div className="info-grid">
                  <div>
                    <h3>Дата заказа</h3>
                    <p>{new Date(order.created_at).toLocaleDateString('ru-RU')}</p>
                  </div>
                  <div>
                    <h3>Статус</h3>
                    <p>{getStatusText(order.status)}</p>
                  </div>
                  <div>
                    <h3>Способ оплаты</h3>
                    <p>{getPaymentMethodText(order.payment_method)}</p>
                  </div>
                  <div>
                    <h3>Статус оплаты</h3>
                    <p>{getPaymentStatusText(order.payment_status)}</p>
                  </div>
                </div>
              </div>
              
              <div className="info-section">
                <h2>Адрес доставки</h2>
                <p>
                  {order.shipping_address.first_name} {order.shipping_address.last_name}<br />
                  {order.shipping_address.address}<br />
                  {order.shipping_address.city}, {order.shipping_address.postal_code}<br />
                  {order.shipping_address.country}
                </p>
              </div>
              
              <div className="info-section">
                <h2>Способ доставки</h2>
                <p>{getShippingMethodText(order.shipping_method)}</p>
              </div>
              
              <div className="info-section order-items">
                <h2>Товары</h2>
                <div className="items-list">
                  {order.items.map((item, index) => (
                    <div key={index} className="order-item">
                      <div className="item-info">
                        <span className="item-name">{item.name}</span>
                        {item.size_name && <span className="item-size">Размер: {item.size_name}</span>}
                        <span className="item-quantity">Количество: {item.quantity}</span>
                      </div>
                      <span className="item-price">{((parseFloat(item.price) || 0) * (item.quantity || 0)).toFixed(2)} ₽</span>
                    </div>
                  ))}
                </div>
                
                <div className="order-summary">
                  <div className="summary-row">
                    <span>Подытог:</span>
                    <span>{(parseFloat(order.subtotal) || 0).toFixed(2)} ₽</span>
                  </div>
                  <div className="summary-row">
                    <span>Доставка:</span>
                    <span>{(parseFloat(order.shipping_amount) || 0).toFixed(2)} ₽</span>
                  </div>
                  {order.discount_amount > 0 && (
                    <div className="summary-row discount">
                      <span>Скидка:</span>
                      <span>-{(parseFloat(order.discount_amount) || 0).toFixed(2)} ₽</span>
                    </div>
                  )}
                  <div className="summary-row total">
                    <span>Итого:</span>
                    <span>{(parseFloat(order.total) || 0).toFixed(2)} ₽</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="confirmation-actions">
          <Link to="/" className="button primary">Вернуться на главную</Link>
          <Link to="/account/orders" className="button secondary">Мои заказы</Link>
        </div>
      </div>
    </div>
  );
};

// Вспомогательные функции для отображения статусов
function getStatusText(status) {
  const statusMap = {
    'pending': 'В обработке',
    'processing': 'Обрабатывается',
    'shipped': 'Отправлен',
    'delivered': 'Доставлен',
    'cancelled': 'Отменен'
  };
  return statusMap[status] || status;
}

function getPaymentStatusText(status) {
  const statusMap = {
    'pending': 'Ожидает оплаты',
    'paid': 'Оплачен',
    'failed': 'Ошибка оплаты',
    'refunded': 'Возвращен'
  };
  return statusMap[status] || status;
}

function getPaymentMethodText(method) {
  const methodMap = {
    'card': 'Банковская карта',
    'cash': 'Наличными при получении'
  };
  return methodMap[method] || method;
}

function getShippingMethodText(method) {
  const methodMap = {
    'standard': 'Стандартная доставка (3-5 рабочих дней)',
    'express': 'Экспресс-доставка (1-2 рабочих дня)'
  };
  return methodMap[method] || method;
}

export default OrderConfirmationPage;