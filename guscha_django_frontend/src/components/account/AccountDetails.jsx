import React, { useState, useEffect } from 'react';
import { updateUserProfile } from '../../api/profileApi';
import { useToast } from '../../hooks/useToast';
import '../../styles/AddressForm.css';

/**
 * Компонент для отображения и редактирования деталей аккаунта
 */
const AccountDetails = ({ user, onUserUpdate }) => {
  const [showEditModal, setShowEditModal] = useState(false);
  const { showSuccess, showError } = useToast();
  const [userForm, setUserForm] = useState({
    first_name: '',
    last_name: '',
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
        email: user.email || ''
      });
    }
  }, [user]);

  const handleEditModalClose = () => {
    setShowEditModal(false);
    document.body.classList.remove('modal-open');
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();

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
              document.body.classList.add('modal-open');
            }}
          >
            ИЗМЕНИТЬ
          </button>
        </div>
      </div>

      {/* Модальное окно редактирования данных пользователя */}
      <div className={`modal-overlay ${showEditModal ? 'open' : ''}`} onClick={handleEditModalClose}>
        <div className={`modal-slide ${showEditModal ? 'open' : ''}`} onClick={(e) => e.stopPropagation()}>
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
    </>
  );
};

export default AccountDetails;