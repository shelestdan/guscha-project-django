import React, { useState, useEffect } from 'react';
import AddressForm from '../features/addresses/AddressForm';
import addressesApi from '../../api/addresses';
import { useToast } from '../../hooks/useToast';

/**
 * Компонент для управления адресами доставки
 */
const AccountAddresses = ({ user }) => {
  const [addresses, setAddresses] = useState([]);
  const [showAddressModal, setShowAddressModal] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const { showSuccess, showError } = useToast();

  // Отладка состояния (можно убрать после тестирования)
  // console.log('🏠 AccountAddresses рендерится, addresses.length:', addresses.length);

  // Загрузка адресов при монтировании компонента
  useEffect(() => {
    if (user) {
      fetchAddresses();
    }
  }, [user]);

  const fetchAddresses = async () => {
    try {
      setLoading(true);
      const response = await addressesApi.getAddresses();
      
      // Убеждаемся, что данные являются массивом
      let addressesArray = [];
      if (Array.isArray(response.data)) {
        addressesArray = response.data;
      } else if (response.data && Array.isArray(response.data.results)) {
        // Django REST Framework pagination format
        addressesArray = response.data.results;
      } else if (response.data && typeof response.data === "object") {
        addressesArray = Object.values(response.data).flat();
      }
      
      setAddresses(addressesArray);
    } catch (error) {
      console.error('❌ Ошибка загрузки адресов:', error);
      console.error('❌ Детали ошибки:', error.response);
      console.error('❌ Статус ошибки:', error.response?.status);
      console.error('❌ Данные ошибки:', error.response?.data);
      console.error('❌ Показываем ошибку пользователю');
      // showError('Не удалось загрузить адреса');
      setAddresses([]); // Устанавливаем пустой массив в случае ошибки
    } finally {
      setLoading(false);
    }
  };

  const handleAddressSuccess = (newAddress) => {
    if (!newAddress) {
      showError('Ошибка при сохранении адреса');
      return;
    }
    
    if (editingAddress) {
      // Обновляем существующий адрес
      setAddresses(prev => 
        prev.map(addr => addr.id === newAddress.id ? newAddress : addr)
      );
      showSuccess('Адрес успешно обновлен!');
    } else {
      // Добавляем новый адрес
      setAddresses(prev => [...prev, newAddress]);
      showSuccess('Адрес успешно добавлен!');
    }
    handleAddressModalClose();
  };

  const handleAddressModalClose = () => {
    setIsAnimating(false);
    setTimeout(() => {
      setShowAddressModal(false);
      setEditingAddress(null);
    }, 300); // Время анимации
  };

  const handleEditAddress = (address) => {
    setEditingAddress(address);
    setShowAddressModal(true);
    setTimeout(() => setIsAnimating(true), 10); // Небольшая задержка для анимации
  };

  const handleAddAddress = () => {
    setEditingAddress(null);
    setShowAddressModal(true);
    setTimeout(() => setIsAnimating(true), 10); // Небольшая задержка для анимации
  };

  const handleDeleteAddress = async (addressId) => {
    // Проверяем, что ID определен
    if (!addressId || addressId === undefined) {
      console.error('❌ Ошибка: ID адреса не определен:', addressId);
      showError('Ошибка: не удалось определить ID адреса');
      return;
    }

    if (window.confirm('Вы уверены, что хотите удалить этот адрес?')) {
      try {
        console.log('🗑️ Удаляем адрес с ID:', addressId);
        await addressesApi.deleteAddress(addressId);
        setAddresses(prev => prev.filter(addr => addr.id !== addressId));
        showSuccess('Адрес успешно удален!');
      } catch (error) {
        console.error('Ошибка при удалении адреса:', error);
        showError('Не удалось удалить адрес');
      }
    }
  };

  return (
    <>
      <div className="account-details-container">
        <div className="account-details-block">
          <div className="account-details-block-header">
            <span>АДРЕСА ДОСТАВКИ</span>
            <div className="account-details-block-sub"></div>
          </div>
          <div className="account-details-block-value">
            {loading ? (
              <p>Загрузка адресов...</p>
            ) : addresses.length > 0 ? (
              addresses.map((address) => {
                // Отладочная информация
                console.log('🏠 Рендерим адрес:', address);
                console.log('🆔 ID адреса:', address.id);
                
                return (
                <div key={address.id || `address-${Math.random()}`} className="address-item">
                  <div className="address-content">
                    <strong>{address.full_name || `${address.first_name} ${address.last_name}`}</strong>
                    <br />
                    {address.full_address || (
                      <>
                        {address.address_line1}
                        {address.address_line2 && `, ${address.address_line2}`}
                        {address.city && `, ${address.city}`}
                        {address.postal_code && `, ${address.postal_code}`}
                      </>
                    )}
                    {address.phone && (
                      <>
                        <br />
                        Телефон: {address.phone}
                      </>
                    )}
                    {address.is_default && (
                      <>
                        <br />
                        <span style={{color: '#28a745', fontWeight: 'bold'}}>По умолчанию</span>
                      </>
                    )}
                  </div>
                  <div className="address-actions">
                    <button
                      className="address-edit-btn"
                      onClick={() => handleEditAddress(address)}
                    >
                      ИЗМЕНИТЬ
                    </button>
                    <button
                      className="address-edit-btn address-delete-btn"
                      onClick={() => {
                        console.log('🗑️ Клик по кнопке удаления, address:', address);
                        console.log('🆔 ID для удаления:', address.id);
                        handleDeleteAddress(address.id);
                      }}
                    >
                      УДАЛИТЬ
                    </button>
                  </div>
                </div>
                );
              })
            ) : (
              <p>У вас пока нет сохраненных адресов</p>
            )}
          </div>
          <button
            className="account-details-add-btn"
            onClick={handleAddAddress}
          >
            ДОБАВИТЬ АДРЕС
          </button>
        </div>
      </div>

      {/* Модальное окно для добавления/редактирования адреса */}
      {showAddressModal && (
        <div className="modal-overlay" onClick={handleAddressModalClose}>
          <div className={`modal-slide ${isAnimating ? 'modal-slide-enter' : 'modal-slide-exit'}`} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {editingAddress ? 'Редактировать адрес' : 'Добавить адрес'}
              </h3>
              <button className="modal-close" onClick={handleAddressModalClose}>
                ×
              </button>
            </div>
            <AddressForm
              address={editingAddress}
              onSuccess={handleAddressSuccess}
              onCancel={handleAddressModalClose}
            />
          </div>
        </div>
      )}
    </>
  );
};

export default AccountAddresses;