import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Token ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Handle response errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized access
            localStorage.removeItem('token');
            window.location.href = '/account';
        }
        return Promise.reject(error);
    }
);

const addressesApi = {
    // Get all addresses for current user
    getAddresses: () => api.get('/api/addresses/'),

    // Get addresses by type
    getShippingAddresses: () => api.get('/api/addresses/shipping/'),
    getBillingAddresses: () => api.get('/api/addresses/billing/'),

    // Get default addresses
    getDefaultAddresses: () => api.get('/api/addresses/default/'),

    // Get single address
    getAddress: (id) => api.get(`/api/addresses/${id}/`),

    // Create new address
    createAddress: (addressData) => api.post('/api/addresses/', addressData),

    // Update address
    updateAddress: (id, addressData) => api.put(`/api/addresses/${id}/`, addressData),

    // Partial update address
    patchAddress: (id, addressData) => api.patch(`/api/addresses/${id}/`, addressData),

    // Delete address (soft delete)
    deleteAddress: (id) => api.delete(`/api/addresses/${id}/`),

    // Set address as default
    setDefaultAddress: (id) => api.post(`/api/addresses/${id}/set_default/`),

    // Search addresses
    searchAddresses: (query) => api.get(`/api/addresses/?search=${query}`),
};

export default addressesApi;