import React, { useState, useEffect } from "react";
import addressesApi from "../../../api/addresses";
import "../../../styles/AddressList.css";

const AddressList = ({ addressType, onSelectAddress }) => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAddresses();
  }, [addressType]);

  const fetchAddresses = async () => {
    try {
      setLoading(true);
      const response = await addressesApi.getAddresses();

      // Правильная обработка ответа API
      let allAddresses = [];
      if (Array.isArray(response.data)) {
        allAddresses = response.data;
      } else if (response.data && Array.isArray(response.data.results)) {
        // Django REST Framework pagination format
        allAddresses = response.data.results;
      } else if (response.data && typeof response.data === "object") {
        allAddresses = Object.values(response.data).flat();
      } else {
        allAddresses = [];
      }

      // Фильтруем адреса по типу
      const filteredAddresses = allAddresses.filter(
        (addr) => addr && addr.address_type === (addressType || "shipping")
      );

      setAddresses(filteredAddresses);
    } catch (error) {
      console.error("Error fetching addresses:", error);
      setError("Ошибка при загрузке адресов");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (addressId) => {
    if (window.confirm("Вы уверены, что хотите удалить этот адрес?")) {
      try {
        await addressesApi.deleteAddress(addressId);
        setAddresses(addresses.filter((addr) => addr.id !== addressId));
      } catch (error) {
        console.error("Error deleting address:", error);
        setError("Ошибка при удалении адреса");
      }
    }
  };

  const handleSetDefault = async (addressId) => {
    try {
      await addressesApi.setDefaultAddress(addressId);
      fetchAddresses(); // Перезагружаем список
    } catch (error) {
      console.error("Error setting default address:", error);
      setError("Ошибка при установке адреса по умолчанию");
    }
  };

  const handleEdit = (address) => {
    if (onSelectAddress) {
      onSelectAddress(address);
    }
  };

  if (loading) {
    return <div className="address-list-loading">Загрузка адресов...</div>;
  }

  if (error) {
    return <div className="address-list-error">{error}</div>;
  }

  if (addresses.length === 0) {
    return (
      <div className="address-list-empty">
        <p>У вас пока нет сохраненных адресов доставки.</p>
      </div>
    );
  }

  return (
    <div className="address-list">
      {addresses.map((address) => (
        <div key={address.id} className="address-card">
          <div className="address-info">
            <div className="address-name">
              {address.first_name} {address.last_name}
            </div>
            <div className="address-details">
              {address.address_line1}
              {address.address_line2 && <span>, {address.address_line2}</span>}
            </div>
            <div className="address-city">
              {address.city}, {address.postal_code}
            </div>
            <div className="address-phone">{address.phone}</div>
            {address.is_default && (
              <span className="default-badge">По умолчанию</span>
            )}
          </div>
          <div className="address-actions">
            <button
              className="address-edit-btn"
              onClick={() => handleEdit(address)}
            >
              Редактировать
            </button>
            {!address.is_default && (
              <button
                className="address-default-btn"
                onClick={() => handleSetDefault(address.id)}
              >
                Установить по умолчанию
              </button>
            )}
            <button
              className="address-delete-btn"
              onClick={() => handleDelete(address.id)}
            >
              Удалить
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default AddressList;
