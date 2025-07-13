import React, { useState } from "react";
import Header from "../components/layout/Header/Header";
import AddressList from "../components/features/addresses/AddressList";
import "../styles/AddressesPage.css";

const AddressesPage = () => {
  const [activeTab, setActiveTab] = useState("shipping");

  return (
    <div className="addresses-page">
      <Header isHome={false} />

      <div className="addresses-container">
        <div className="addresses-header">
          <h1>Управление адресами</h1>
          <p>Управляйте своими адресами доставки и оплаты</p>
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
          {activeTab === "shipping" && <AddressList addressType="shipping" />}
          {activeTab === "billing" && <AddressList addressType="billing" />}
        </div>
      </div>
    </div>
  );
};

export default AddressesPage;
