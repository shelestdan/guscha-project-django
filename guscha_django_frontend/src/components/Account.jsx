import React, { useState, useEffect, useCallback } from "react";
import AdvancedAuth from "./AdvancedAuth";
import Header from "./layout/Header/Header";
import { updateUserProfile } from "../api/profileApi";
import PhoneInput from "react-phone-number-input";
import { isValidPhoneNumber } from "libphonenumber-js";
import { useToast } from "../hooks/useToast";
import ToastContainer from "./ui/ToastContainer";
import AddressList from "./features/addresses/AddressList";
import AddressForm from "./features/addresses/AddressForm";
import addressesApi from "../api/addresses";
import "../styles/Account.css";
import "../styles/AccountDetails.css";
import "../styles/OrderHistory.css";
import "../styles/AddressModal.css";
import "react-phone-number-input/style.css";

const Account = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("details");
  const [csrfToken, setCsrfToken] = useState(null);
  const [showAddressModal, setShowAddressModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [shippingAddresses, setShippingAddresses] = useState([]);
  const { showSuccess, showError } = useToast();
  const [userForm, setUserForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    email: ""
  });
  const [editingAddress, setEditingAddress] = useState(null);

  // В Django DRF Token Auth нет механизма обновления токена, поэтому просто проверяем валидность текущего
  const refreshAccessToken = async () => {
    try {
      // Проверяем текущий токен через запрос к профилю
      const token = localStorage.getItem("token");
      if (!token) return null;

      const response = await fetch(
        "http://127.0.0.1:8000/api/accounts/users/me/",
        {
          method: "GET",
          headers: {
            Authorization: `Token ${token}`
          },
          credentials: "include"
        }
      );

      if (response.ok) {
        return token;
      } else {
        localStorage.removeItem("token");
        setIsLoggedIn(false);
        setUser(null);
        return null;
      }
    } catch (error) {
      console.error("Ошибка обновления токена:", error);
      return null;
    }
  };

  const fetchWithAuth = async (url, options = {}) => {
    let token = localStorage.getItem("token");

    const makeRequest = async (authToken) => {
      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Token ${authToken}`,
          "Content-Type": "application/json"
        },
        credentials: "include"
      });
    };

    let response = await makeRequest(token);

    if (response.status === 401) {
      token = await refreshAccessToken();
      if (token) {
        response = await makeRequest(token);
      }
    }

    return response;
  };

  const fetchUserProfile = useCallback(async () => {
    try {
      const response = await fetchWithAuth(
        "http://127.0.0.1:8000/api/accounts/users/me/"
      );

      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setIsLoggedIn(true);
      } else {
        localStorage.removeItem("token");
        setIsLoggedIn(false);
        setUser(null);
      }
    } catch (error) {
      console.error("Ошибка получения профиля:", error);
      localStorage.removeItem("token");
      setIsLoggedIn(false);
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Получаем CSRF токен из cookie (Django автоматически устанавливает его)
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
          const [name, value] = cookie.trim().split("=");
          if (name === "csrftoken") {
            setCsrfToken(value);
            break;
          }
        }

        // Проверяем токен доступа
        const token = localStorage.getItem("token");
        if (token) {
          await fetchUserProfile();
        }
      } catch (error) {
        console.error("Ошибка инициализации:", error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, [fetchUserProfile]);

  // Обработка входа
  const handleLogin = async (loginData) => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/accounts/users/login/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {})
          },
          credentials: "include",
          body: JSON.stringify(loginData)
        }
      );

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("token", data.token);
        setUser(data.user);
        setIsLoggedIn(true);
      } else {
        throw new Error(data.detail || data.message || "Ошибка входа");
      }
    } catch (error) {
      throw error;
    }
  };

  // Обработка регистрации
  const handleRegister = async (registrationData) => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/accounts/users/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {})
          },
          credentials: "include",
          body: JSON.stringify(registrationData)
        }
      );

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("token", data.token);
        setUser(data.user);
        setIsLoggedIn(true);
      } else {
        const error = new Error(
          data.detail || data.message || "Ошибка регистрации"
        );
        error.response = { data };
        throw error;
      }
    } catch (error) {
      throw error;
    }
  };

  const handleLogout = async () => {
    try {
      // Отправляем запрос на выход из системы
      await fetch("http://127.0.0.1:8000/api/accounts/users/logout/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          Authorization: `Token ${localStorage.getItem("token")}`
        },
        credentials: "include"
      });
    } catch (error) {
      console.error("Ошибка при выходе из системы:", error);
    } finally {
      // Удаляем токен из localStorage и сбрасываем состояние
      localStorage.removeItem("token");
      setIsLoggedIn(false);
      setUser(null);
    }
  };

  // Новые функции для работы с адресами через новый API
  const fetchAddresses = async () => {
    try {
      const response = await addressesApi.getAddresses();
      const allAddresses = Array.isArray(response.data)
        ? response.data
        : response.data.results || [];

      setShippingAddresses(
        allAddresses.filter((addr) => addr.address_type === "shipping")
      );
    } catch (error) {
      console.error("Ошибка загрузки адресов:", error);
      showError(
        "Ошибка при загрузке адресов: " +
          (error.message || "Проверьте подключение к серверу")
      );
    }
  };

  const handleAddressSuccess = () => {
    setShowAddressModal(false);
    setEditingAddress(null);
    fetchAddresses();
    showSuccess("Адрес успешно сохранен");
  };

  const handleAddressModalClose = () => {
    setShowAddressModal(false);
    setEditingAddress(null);
  };

  const handleEditAddress = (address) => {
    setEditingAddress(address);
    setShowAddressModal(true);
  };

  const handleAddAddress = () => {
    setEditingAddress(null);
    setShowAddressModal(true);
  };

  const handleEditModalClose = () => {
    setShowEditModal(false);
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();

    // Валидация телефонного номера
    if (userForm.phone && !isValidPhoneNumber(userForm.phone)) {
      showError(
        "Некорректный формат российского номера телефона. Пример: +79372172203"
      );
      return;
    }

    try {
      await updateUserProfile(userForm);
      // Обновляем данные пользователя в состоянии
      setUser((prev) => ({
        ...prev,
        ...userForm
      }));
      setShowEditModal(false);
      showSuccess("Данные успешно обновлены!");
    } catch (error) {
      console.error("Ошибка обновления данных:", error);
      showError(
        "Произошла ошибка при обновлении данных: " +
          (error.response?.data?.message || "Неизвестная ошибка")
      );
    }
  };

  // Загружаем адреса при входе пользователя
  useEffect(() => {
    if (isLoggedIn && user) {
      fetchAddresses();
      setUserForm({
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        phone: user.phone || "",
        email: user.email || ""
      });
    }
  }, [isLoggedIn, user]);

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
              <div
                className={
                  "account-figma-menu-item account-menu-item-nowrap" +
                  (activeTab === "details"
                    ? " account-figma-menu-item-active"
                    : "")
                }
                onClick={() => setActiveTab("details")}
              >
                ACCOUNT DETAILS
              </div>
              <div
                className={
                  "account-figma-menu-item account-menu-item-nowrap" +
                  (activeTab === "addresses"
                    ? " account-figma-menu-item-active"
                    : "")
                }
                onClick={() => setActiveTab("addresses")}
              >
                АДРЕСА ДОСТАВКИ
              </div>
              <div
                className={
                  "account-figma-menu-item account-menu-item-nowrap" +
                  (activeTab === "orders"
                    ? " account-figma-menu-item-active"
                    : "")
                }
                onClick={() => setActiveTab("orders")}
              >
                ORDER HISTORY
              </div>
              <div
                className="account-figma-menu-item account-menu-item-nowrap"
                onClick={handleLogout}
              >
                LOGOUT
              </div>
            </div>
          </div>
          <div className="account-figma-content">
            {activeTab === "details" ? (
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
                    onClick={() => setShowEditModal(true)}
                  >
                    ИЗМЕНИТЬ
                  </button>
                </div>
              </div>
            ) : activeTab === "addresses" ? (
              <div className="account-details-container">
                <div className="account-details-block">
                  <div
                    className="account-details-block-header"
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center"
                    }}
                  >
                    <span>АДРЕСА ДОСТАВКИ</span>
                    <button
                      className="account-details-add-btn"
                      onClick={handleAddAddress}
                      style={{ marginLeft: "20px" }}
                    >
                      ДОБАВИТЬ
                    </button>
                  </div>
                  <AddressList
                    addressType="shipping"
                    onSelectAddress={handleEditAddress}
                  />
                </div>
              </div>
            ) : (
              <div className="account-figma-orders-block">
                <div className="account-figma-orders-header">
                  <div className="account-figma-orders-col">ORDER NO.</div>
                  <div className="account-figma-orders-col">DATE</div>
                  <div className="account-figma-orders-col">PAYMENT STATUS</div>
                  <div className="account-figma-orders-col">
                    FULFILLMENT STATUS
                  </div>
                  <div className="account-figma-orders-col">TOTAL</div>
                </div>
                <div className="account-figma-orders-empty">Нет заказов</div>
              </div>
            )}
          </div>
        </div>

        {/* Модальное окно редактирования данных пользователя */}
        {showEditModal && (
          <div className="modal-overlay" onClick={handleEditModalClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
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

        {/* Модальное окно добавления/редактирования адреса */}
        {showAddressModal && (
          <div className="modal-overlay" onClick={handleAddressModalClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>
                  {editingAddress ? "Редактировать адрес" : "Добавить адрес"}
                </h3>
                <button
                  className="modal-close"
                  onClick={handleAddressModalClose}
                >
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
  }

  // Если пользователь не авторизован, показываем новую систему аутентификации
  return (
    <>
      <Header isHome={false} />
      <div className="account-auth-wrapper">
        <AdvancedAuth
          onLogin={handleLogin}
          onRegister={handleRegister}
          onGoogleLogin={() => {}} // Google login disabled for now
        />
      </div>
    </>
  );
};

export default Account;
