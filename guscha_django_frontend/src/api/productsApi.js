import axios from './axiosInstance';

export async function fetchProducts(params = {}) {
  const { data } = await axios.get('/api/products/products/', { params });
  return data;
}

export async function fetchProductDetails(productId) {
  const { data } = await axios.get(`/api/products/products/${productId}/`);
  return data;
}

export async function fetchCategories() {
  const { data } = await axios.get('/api/products/categories/');
  return data;
}

export async function fetchSizes() {
  const { data } = await axios.get('/api/products/sizes/');
  return data;
}