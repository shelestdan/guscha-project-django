import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdvancedAuth from './AdvancedAuth';
import AccountDetails from './account/AccountDetails';
import AccountAddresses from './account/AccountAddresses';
import AccountOrders from './account/AccountOrders';
import PasswordReset from './account/PasswordReset';
import Header from './layout/Header/Header';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import ToastContainer from './ui/ToastContainer';
import '../styles/Account.css';

const Account = () => {
  const [activeTab, setActiveTab] = useState('details');
  const { user, loading, isLoggedIn, login, register, logout, setUser, setUserWithLogin } = useAuth();
  const navigate = useNavigate();
  const { showSuccess } = useToast();

  const handleLogout = async () => {
    await logout();
    showSuccess('Вы успешно вышли из системы');
  };

  const handleUserUpdate = (updatedUser) => {
    setUser(updatedUser);
  };

  if (loading) {
    return (
      <>
        <Header isHome={false} />
        <div className="account-figma-root">
          <div className="account-figma-content centered-auth">
            <div className="account-figma-loading">Загрузка...</div>
          </div>
        </div>
      </>
    );
  }

  // Если пользователь авторизован, показываем профиль
  if (isLoggedIn && user) {
    return (
      <>
        <Header isHome={false} />
        <ToastContainer position="top-center" />
        <div className="account-figma-root">
          <div className="account-figma-sidebar account-sidebar-fixed">
            <div className="account-figma-menu">
              <button
                className={`account-figma-menu-item account-menu-item-nowrap${activeTab === "details" ? " account-figma-menu-item-active" : ""}`}
                onClick={() => setActiveTab("details")}
                type="button"
              >
                ACCOUNT DETAILS
              </button>
              <button
                className={`account-figma-menu-item account-menu-item-nowrap${activeTab === "addresses" ? " account-figma-menu-item-active" : ""}`}
                onClick={() => setActiveTab("addresses")}
                type="button"
              >
                АДРЕСА ДОСТАВКИ
              </button>
              <button
                className={`account-figma-menu-item account-menu-item-nowrap${activeTab === "orders" ? " account-figma-menu-item-active" : ""}`}
                onClick={() => setActiveTab("orders")}
                type="button"
              >
                ORDER HISTORY
              </button>
              <button
                className={`account-figma-menu-item account-menu-item-nowrap${activeTab === "password-reset" ? " account-figma-menu-item-active" : ""}`}
                onClick={() => setActiveTab("password-reset")}
                type="button"
              >
                СБРОС ПАРОЛЯ
              </button>
              <button
                className="account-figma-menu-item account-menu-item-nowrap"
                onClick={handleLogout}
                type="button"
              >
                LOGOUT
              </button>
            </div>
          </div>
          <div className="account-figma-content">
            {activeTab === 'details' && <AccountDetails user={user} onUserUpdate={handleUserUpdate} />}
             {activeTab === 'addresses' && <AccountAddresses user={user} />}
             {activeTab === 'orders' && <AccountOrders user={user} />}
             {activeTab === 'password-reset' && <PasswordReset />}
          </div>
        </div>


      </>
    );
  }

  // Если пользователь не авторизован, показываем новую систему аутентификации
  return (
    <>
      <Header isHome={false} />
      <div className="account-auth-wrapper">
        <AdvancedAuth
          onLogin={async (emailOrUser, password) => {
            // Если передан объект пользователя (например, после Telegram-верификации)
            if (typeof emailOrUser === 'object' && emailOrUser !== null) {
              setUserWithLogin(emailOrUser);
              showSuccess('Вход выполнен успешно!');
            } else {
              // Обычный вход по email и паролю
              await login({ email: emailOrUser, password });
            }
          }}
          onRegister={async (data) => {
            const result = await register(data);
            return result;
          }}
          onGoogleLogin={async (data) => {
            // Токен уже сохранен в localStorage в AdvancedAuth
            // Обновляем состояние пользователя и аутентификации
            setUserWithLogin(data.user);
            showSuccess('Вход через Google выполнен успешно!');
          }}
          onTelegramLogin={async (data) => {
            // Обработка входа через Telegram
            console.log('Telegram login data:', data);
            if (data && data.user) {
              setUserWithLogin(data.user);
              showSuccess('Вход через Telegram выполнен успешно!');
            } else {
              showError('Ошибка входа через Telegram');
            }
          }}
          onClose={() => navigate('/')} // Переход на главную при закрытии
        />
      </div>
    </>
  );
};

export default Account;
