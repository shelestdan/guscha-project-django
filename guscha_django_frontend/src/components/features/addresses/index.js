// Export all address-related components
export { default as AddressList } from './AddressList';
export { default as AddressForm } from './AddressForm';
export { default as GoogleAddressAutocomplete } from './GoogleAddressAutocomplete';
export { default as AddressSelector } from '../checkout/AddressSelector';

// Export API client
export { default as addressesApi } from '../../../api/addresses';

// Export hooks
export { useAddresses } from './useAddresses';