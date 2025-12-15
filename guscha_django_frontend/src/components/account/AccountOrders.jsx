import React, { useState, useEffect } from 'react';
import { fetchUserOrders } from '../../api/orderApi';
import { useToast } from '../../hooks/useToast';

/**
 * Компонент для отображения заказов пользователя
 */
const AccountOrders = ({ user }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showError } = useToast();

  // Загрузка заказов при монтировании компонента
  useEffect(() => {
    if (user) {
      fetchOrders();
    }
  }, [user]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const ordersData = await fetchUserOrders();
      setOrders(ordersData);
    } catch (error) {
      showError('Не удалось загрузить заказы');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusText = (status) => {
    const statusMap = {
      'pending': 'Ожидает обработки',
      'processing': 'В обработке',
      'shipped': 'Отправлен',
      'delivered': 'Доставлен',
      'cancelled': 'Отменен'
    };
    return statusMap[status] || status;
  };

  const getStatusClass = (status) => {
    const statusClassMap = {
      'pending': 'status-pending',
      'processing': 'status-processing',
      'shipped': 'status-shipped',
      'delivered': 'status-delivered',
      'cancelled': 'status-cancelled'
    };
    return statusClassMap[status] || 'status-default';
  };

  if (loading) {
    return (
      <div className="account-details-container">
        <div className="account-details-block">
          <div className="account-details-block-header">
            <span>МОИ ЗАКАЗЫ</span>
            <div className="account-details-block-sub"></div>
          </div>
          <div className="account-details-block-value">
            <p>Загрузка заказов...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="account-details-container">
      <div className="account-details-block">
        <div className="account-details-block-header">
          <span>МОИ ЗАКАЗЫ</span>
          <div className="account-details-block-sub"></div>
        </div>
        <div className="account-details-block-value">
          {orders.length > 0 ? (
            <div className="orders-list">
              {orders.map((order) => (
                <div key={order.id} className="order-item">
                  <div className="order-header">
                    <div className="order-number">
                      <strong>Заказ #{order.id}</strong>
                    </div>
                    <div className={`order-status ${getStatusClass(order.status)}`}>
                      {getStatusText(order.status)}
                    </div>
                  </div>
                  
                  <div className="order-details">
                    <div className="order-date">
                      <span>Дата заказа: {formatDate(order.created_at)}</span>
                    </div>
                    
                    {order.items && order.items.length > 0 && (
                      <div className="order-items">
                        <h4>Товары:</h4>
                        {order.items.map((item, index) => (
                          <div key={index} className="order-item-detail">
                            <span className="item-name">{item.product_name}</span>
                            <span className="item-quantity">x{item.quantity}</span>
                            <span className="item-price">{item.price} ₽</span>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    <div className="order-total">
                      <strong>Итого: {order.total_amount} ₽</strong>
                    </div>
                    
                    {order.delivery_address && (
                      <div className="order-address">
                        <h4>Адрес доставки:</h4>
                        <p>
                          {order.delivery_address.address_line_1}
                          {order.delivery_address.address_line_2 && (
                            <>, {order.delivery_address.address_line_2}</>
                          )}
                          <br />
                          {order.delivery_address.city}, {order.delivery_address.postal_code}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>У вас пока нет заказов</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default AccountOrders;