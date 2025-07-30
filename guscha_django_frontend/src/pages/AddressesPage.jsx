import React, { useState } from "react";
import Header from "../components/layout/Header/Header";
import AddressList from "../components/features/addresses/AddressList";
import AddressForm from "../components/features/addresses/AddressForm";
import "../styles/AddressesPage.css";

const AddressesPage = () => {
  const [activeTab, setActiveTab] = useState("shipping");
  const [showForm, setShowForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleAddAddress = () => {
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
    setRefreshKey(prev => prev + 1); // Принудительно обновляем список
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingAddress(null);
  };

  return (
    <div className="addresses-page">
      <Header isHome={false} />

      <div className="addresses-container">
        <div className="addresses-header">
          <div className="addresses-header-content">
            <div>
              <h1>DELIVERY ADDRESSES</h1>
              <p>Управляйте своими адресами доставки и оплаты</p>
            </div>
            <button className="add-address-btn" onClick={handleAddAddress}>
              ДОБАВИТЬ
            </button>
          </div>
        </div>

        <div className="addresses-tabs">
          <button
            className={`tab-button ${activeTab === "shipping" ? "active" : ""}`}
            onClick={() => setActiveTab("shipping")}
          >
            Адреса доставки
          </button>
          <button
            className={`tab-button ${activeTab === "billing" ? "active" : ""}`}
            onClick={() => setActiveTab("billing")}
          >
            Адреса оплаты
          </button>
        </div>

        <div className="addresses-content">
          {showForm ? (
            <AddressForm
              address={editingAddress}
              addressType={activeTab}
              onSuccess={handleFormSuccess}
              onCancel={handleFormCancel}
            />
          ) : (
            <>
              {activeTab === "shipping" && (
                <AddressList 
                  key={`shipping-${refreshKey}`}
                  addressType="shipping" 
                  onSelectAddress={handleEditAddress}
                />
              )}
              {activeTab === "billing" && (
                <AddressList 
                  key={`billing-${refreshKey}`}
                  addressType="billing" 
                  onSelectAddress={handleEditAddress}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AddressesPage;
