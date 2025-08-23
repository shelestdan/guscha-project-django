import React, { useState, useEffect } from 'react';
import PhoneInput from 'react-phone-number-input';
import { isValidPhoneNumber } from 'libphonenumber-js';
import { updateUserProfile } from '../../api/profileApi';
import { useToast } from '../../hooks/useToast';
import 'react-phone-number-input/style.css';

/**
 * Компонент для отображения и редактирования деталей аккаунта
 */
const AccountDetails = ({ user, onUserUpdate }) => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const { showSuccess, showError } = useToast();
  const [userForm, setUserForm] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    email: ''
  });

  // Очищаем modal-open класс при размонтировании компонента
  useEffect(() => {
    return () => {
      document.body.classList.remove('modal-open');
    };
  }, []);

  // Инициализация формы при изменении пользователя
  useEffect(() => {
    if (user) {
      setUserForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone: user.phone || '',
        email: user.email || ''
      });
    }
  }, [user]);

  const handleEditModalClose = () => {
    setIsAnimating(false);
    // Убираем класс для предотвращения прокрутки
    document.body.classList.remove('modal-open');
    setTimeout(() => {
      setShowEditModal(false);
    }, 300); // Время анимации
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();

    // Валидация телефонного номера
    if (userForm.phone && !isValidPhoneNumber(userForm.phone)) {
      showError(
        'Некорректный формат российского номера телефона. Пример: +79372172203'
      );
      return;
    }

    try {
      await updateUserProfile(userForm);
      // Обновляем данные пользователя в родительском компоненте
      onUserUpdate({
        ...user,
        ...userForm
      });
      setShowEditModal(false);
      showSuccess('Данные успешно обновлены!');
    } catch (error) {
      console.error('Ошибка обновления данных:', error);
      showError(
        'Произошла ошибка при обновлении данных: ' +
          (error.response?.data?.message || 'Неизвестная ошибка')
      );
    }
  };

  return (
    <>
      <div className="account-details-container">
        <div className="account-details-block">
          <div className="account-details-block-header">
            <span>ОСНОВНАЯ ИНФОРМАЦИЯ</span>
            <div className="account-details-block-sub"></div>
          </div>
          <div className="account-details-block-value">
            {user.first_name} {user.last_name}
            <br />
            {user.email}
            {user.phone && (
              <>
                <br />
                {user.phone}
              </>
            )}
          </div>
          <button
            className="account-details-add-btn"
            onClick={() => {
              setShowEditModal(true);
              // Добавляем класс для предотвращения прокрутки
              document.body.classList.add('modal-open');
              setTimeout(() => setIsAnimating(true), 10);
            }}
          >
            ИЗМЕНИТЬ
          </button>
        </div>
      </div>

      {/* Модальное окно редактирования данных пользователя */}
      {showEditModal && (
        <div className={`modal-overlay ${isAnimating ? 'show' : ''}`} onClick={handleEditModalClose}>
          <div className={`modal-slide ${isAnimating ? 'modal-slide-enter' : 'modal-slide-exit'}`} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Редактировать данные</h3>
              <button className="modal-close" onClick={handleEditModalClose}>
                ×
              </button>
            </div>
            <form onSubmit={handleProfileUpdate} className="address-form">
              <div className="form-group">
                <label>Имя*</label>
                <input
                  type="text"
                  name="first_name"
                  value={userForm.first_name}
                  onChange={(e) =>
                    setUserForm((prev) => ({
                      ...prev,
                      first_name: e.target.value
                    }))
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label>Фамилия*</label>
                <input
                  type="text"
                  name="last_name"
                  value={userForm.last_name}
                  onChange={(e) =>
                    setUserForm((prev) => ({
                      ...prev,
                      last_name: e.target.value
                    }))
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label>Email*</label>
                <input
                  type="email"
                  name="email"
                  value={userForm.email}
                  onChange={(e) =>
                    setUserForm((prev) => ({
                      ...prev,
                      email: e.target.value
                    }))
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label>Телефон</label>
                <PhoneInput
                  international
                  defaultCountry="RU"
                  name="phone"
                  value={userForm.phone}
                  onChange={(value) =>
                    setUserForm((prev) => ({ ...prev, phone: value }))
                  }
                  placeholder="+7 (999) 123-45-67"
                />
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={handleEditModalClose}
                  className="btn-cancel"
                >
                  Отмена
                </button>
                <button type="submit" className="btn-submit">
                  Сохранить
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default AccountDetails;