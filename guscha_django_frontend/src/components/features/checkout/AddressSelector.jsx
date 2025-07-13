import React, { useState, useEffect } from "react";
import { useAddresses } from "../addresses/useAddresses";
import AddressForm from "../addresses/AddressForm";
import "../styles/AddressSelector.css";

const AddressSelector = ({ onAddressSelect, addressType = "shipping" }) => {
  const { addresses, loading, defaultAddress, fetchAddresses } =
    useAddresses(addressType);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);

  useEffect(() => {
    if (defaultAddress) {
      setSelectedAddress(defaultAddress);
      onAddressSelect(defaultAddress);
    }
  }, [defaultAddress, onAddressSelect]);

  const handleAddressSelect = (address) => {
    setSelectedAddress(address);
    onAddressSelect(address);
  };

  const handleAddNewAddress = () => {
    setEditingAddress(null);
    setShowForm(true);
  };

  const handleEditAddress = (address) => {
    setEditingAddress(address);
    setShowForm(true);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingAddress(null);
    fetchAddresses();
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingAddress(null);
  };

  if (loading) {
    return <div className="address-selector-loading">Загрузка адресов...</div>;
  }

  return (
    <div className="address-selector">
      <h3>{addressType === "shipping" ? "Адрес доставки" : "Адрес оплаты"}</h3>

      {showForm ? (
        <div className="address-form-container">
          <AddressForm
            address={editingAddress}
            addressType={addressType}
            onSuccess={handleFormSuccess}
            onCancel={handleFormCancel}
          />
        </div>
      ) : (
        <>
          {addresses.length === 0 ? (
            <div className="empty-addresses">
              <p>
                У вас пока нет адресов{" "}
                {addressType === "shipping" ? "доставки" : "оплаты"}
              </p>
              <button className="add-address-btn" onClick={handleAddNewAddress}>
                Добавить адрес
              </button>
            </div>
          ) : (
            <div className="address-list">
              {addresses.map((address) => (
                <div
                  key={address.id}
                  className={`address-item ${
                    selectedAddress?.id === address.id ? "selected" : ""
                  }`}
                  onClick={() => handleAddressSelect(address)}
                >
                  <div className="address-radio">
                    <input
                      type="radio"
                      name={`${addressType}-address`}
                      checked={selectedAddress?.id === address.id}
                      onChange={() => handleAddressSelect(address)}
                    />
                  </div>
                  <div className="address-details">
                    <div className="address-name">
                      {address.full_name}
                      {address.is_default && (
                        <span className="default-badge">По умолчанию</span>
                      )}
                    </div>
                    <div className="address-line">{address.full_address}</div>
                    {address.phone && (
                      <div className="address-phone">Тел: {address.phone}</div>
                    )}
                  </div>
                  <div className="address-actions">
                    <button
                      className="edit-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditAddress(address);
                      }}
                    >
                      Редактировать
                    </button>
                  </div>
                </div>
              ))}

              <button className="add-new-btn" onClick={handleAddNewAddress}>
                + Добавить новый адрес
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AddressSelector;
