import { useState, useEffect, useCallback } from 'react';
import addressesApi from '../../../api/addresses';

export const useAddresses = (addressType = null) => {
    const [addresses, setAddresses] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [defaultAddress, setDefaultAddr] = useState(null);

    const fetchAddresses = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            let response;
            if (addressType) {
                response = await addressesApi.getAddresses();
                const filtered = response.data.filter(addr => addr.address_type === addressType);
                setAddresses(filtered);

                // Find default address
                const defaultAddr = filtered.find(addr => addr.is_default);
                setDefaultAddr(defaultAddr);
            } else {
                response = await addressesApi.getAddresses();
                setAddresses(response.data);
            }
        } catch (err) {
            setError(err.response?.data?.message || 'Ошибка при загрузке адресов');
            console.error('Error fetching addresses:', err);
        } finally {
            setLoading(false);
        }
    }, [addressType]);

    const fetchDefaultAddresses = useCallback(async () => {
        try {
            const response = await addressesApi.getDefaultAddresses();
            return response.data;
        } catch (err) {
            console.error('Error fetching default addresses:', err);
            return { shipping: null, billing: null };
        }
    }, []);

    const createAddress = useCallback(async (addressData) => {
        setLoading(true);
        setError(null);

        try {
            const response = await addressesApi.createAddress(addressData);
            await fetchAddresses();
            return response.data;
        } catch (err) {
            setError(err.response?.data?.message || 'Ошибка при создании адреса');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [fetchAddresses]);

    const updateAddress = useCallback(async (id, addressData) => {
        setLoading(true);
        setError(null);

        try {
            const response = await addressesApi.updateAddress(id, addressData);
            await fetchAddresses();
            return response.data;
        } catch (err) {
            setError(err.response?.data?.message || 'Ошибка при обновлении адреса');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [fetchAddresses]);

    const deleteAddress = useCallback(async (id) => {
        setLoading(true);
        setError(null);

        try {
            await addressesApi.deleteAddress(id);
            await fetchAddresses();
        } catch (err) {
            setError(err.response?.data?.message || 'Ошибка при удалении адреса');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [fetchAddresses]);

    const setDefaultAddress = useCallback(async (id) => {
        try {
            await addressesApi.setDefaultAddress(id);
            await fetchAddresses();
        } catch (err) {
            setError(err.response?.data?.message || 'Ошибка при установке адреса по умолчанию');
            throw err;
        }
    }, [fetchAddresses]);

    useEffect(() => {
        fetchAddresses();
    }, [fetchAddresses]);

    return {
        addresses,
        loading,
        error,
        defaultAddress,
        fetchAddresses,
        fetchDefaultAddresses,
        createAddress,
        updateAddress,
        deleteAddress,
        setDefaultAddress,
        refresh: fetchAddresses,
    };
};