import axiosInstance from './axiosInstance';

const addressesApi = {
    // Get all addresses for current user
    getAddresses: () => axiosInstance.get('/api/addresses/'),

    // Get addresses by type
    getShippingAddresses: () => axiosInstance.get('/api/addresses/shipping/'),
    getBillingAddresses: () => axiosInstance.get('/api/addresses/billing/'),

    // Get default addresses
    getDefaultAddresses: () => axiosInstance.get('/api/addresses/default/'),

    // Get single address
    getAddress: (id) => axiosInstance.get(`/api/addresses/${id}/`),

    // Create new address
    createAddress: (addressData) => axiosInstance.post('/api/addresses/', addressData),

    // Update address
    updateAddress: (id, addressData) => axiosInstance.put(`/api/addresses/${id}/`, addressData),

    // Partial update address
    patchAddress: (id, addressData) => axiosInstance.patch(`/api/addresses/${id}/`, addressData),

    // Delete address (soft delete)
    deleteAddress: (id) => axiosInstance.delete(`/api/addresses/${id}/`),

    // Set address as default
    setDefaultAddress: (id) => axiosInstance.post(`/api/addresses/${id}/set_default/`),

    // Search addresses
    searchAddresses: (query) => axiosInstance.get(`/api/addresses/?search=${query}`),
};

export default addressesApi;