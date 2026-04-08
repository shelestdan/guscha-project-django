import React, { useState, useEffect } from "react";
import addressesApi from "../../../api/addresses";
import "../../../styles/AddressForm.css";

const AddressForm = ({ address, addressType, onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    address_type: addressType || "shipping",
    address_line1: "",
    address_line2: "",
    city: "",
    postal_code: "",
    is_default: false
  });
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  // Загружаем данные пользователя для отображения информации
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        // Токен теперь в httpOnly cookie
        const response = await fetch(
          "/api/accounts/users/me/",
          {
            headers: {
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          }
        );
        if (response.ok) {
          const user = await response.json();
          setUserData(user);
        }
      } catch (error) {
        // Ошибка загрузки данных пользователя
      }
    };

    fetchUserData();
  }, []);

  useEffect(() => {
    if (address) {
      // Проверяем, есть ли все необходимые поля в объекте address
      const hasCompleteData = address.address_line1 && address.city && address.postal_code;

      if (hasCompleteData) {
        setFormData({
          address_type: address.address_type || addressType || "shipping",
          address_line1: address.address_line1 || "",
          address_line2: address.address_line2 || "",
          city: address.city || "",
          postal_code: address.postal_code || "",
          is_default: address.is_default || false
        });
      } else if (address.id) {
        // Если данные неполные, но есть ID, загружаем полные данные с сервера
        fetchAddressById(address.id);
      }
    }
  }, [address, addressType]);

  const fetchAddressById = async (addressId) => {
    try {
      setLoading(true);
      const response = await addressesApi.getAddress(addressId);
      const addressData = response.data;

      setFormData({
        address_type: addressData.address_type || addressType || "shipping",
        address_line1: addressData.address_line1 || "",
        address_line2: addressData.address_line2 || "",
        city: addressData.city || "",
        postal_code: addressData.postal_code || "",
        is_default: addressData.is_default || false
      });
    } catch (error) {
      // Ошибка загрузки адреса
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.address_line1.trim())
      newErrors.address_line1 = "Адрес обязателен";
    if (!formData.city.trim()) newErrors.city = "Город обязателен";
    if (!formData.postal_code.trim())
      newErrors.postal_code = "Почтовый индекс обязателен";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      // Добавляем данные пользователя к данным формы
      const dataToSend = {
        ...formData,
        first_name: userData?.first_name || "",
        last_name: userData?.last_name || "",
        phone: userData?.phone || ""
      };

      let savedAddress;
      if (address?.id) {
        const response = await addressesApi.updateAddress(address.id, dataToSend);
        savedAddress = response.data;
      } else {
        const response = await addressesApi.createAddress(dataToSend);
        savedAddress = response.data;
      }
      onSuccess(savedAddress);
    } catch (error) {
      if (error.response?.data) {
        setErrors(error.response.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const renderField = (name, label, type = "text", options = {}) => (
    <div className="form-group">
      <label htmlFor={name}>
        {label}
        {options.required && <span className="required">*</span>}
      </label>
      {type === "checkbox" ? (
        <label className="checkbox-label">
          <input
            type="checkbox"
            name={name}
            checked={formData[name]}
            onChange={handleInputChange}
          />
          {label}
        </label>
      ) : (
        <input
          type={type}
          id={name}
          name={name}
          value={formData[name]}
          onChange={handleInputChange}
          placeholder={options.placeholder}
          className={errors[name] ? "error" : ""}
          readOnly={options.readOnly}
        />
      )}
      {errors[name] && <span className="error-message">{errors[name]}</span>}
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="address-form">
      {/* Отображение информации о пользователе */}
      {userData && (
        <div className="user-info">
          <h4>Пользователь:</h4>
          <p>{userData.first_name} {userData.last_name}</p>
          {userData.phone && <p>Телефон: {userData.phone}</p>}
        </div>
      )}

      {renderField("address_line1", "Адрес", "text", {
        required: true,
        placeholder: "Улица, номер дома"
      })}

      {renderField("address_line2", "Квартира/Офис", "text", {
        placeholder: "Квартира, офис, подъезд"
      })}

      <div className="form-row">
        {renderField("city", "Город", "text", {
          required: true,
          placeholder: "Москва"
        })}
        {renderField("postal_code", "Почтовый индекс", "text", {
          required: true,
          placeholder: "123456"
        })}
      </div>

      <div className="form-actions">
        <button type="button" className="btn-cancel" onClick={onCancel}>
          Отмена
        </button>
        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? "Сохранение..." : address ? "Обновить" : "Добавить"}
        </button>
      </div>
    </form>
  );
};

export default AddressForm;
