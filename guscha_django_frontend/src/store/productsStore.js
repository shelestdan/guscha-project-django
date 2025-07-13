import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import * as productsApi from '../api/productsApi';

export const useProductsStore = create(devtools((set) => ({
  products: [],
  loading: false,
  error: null,
  filters: {},
  page: 1,

  fetchProducts: async (filters = {}, page = 1) => {
    set({ loading: true, error: null, filters, page });
    try {
      const data = await productsApi.fetchProducts({ ...filters, page });
      set({ products: data.products || data, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },
}))); 