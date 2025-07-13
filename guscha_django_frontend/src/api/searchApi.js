import axios from './axiosInstance';

// Поиск товаров по запросу
export async function searchProducts(query, params = {}) {
  const searchParams = { ...params, search: query };
  const { data } = await axios.get('/api/products/products/', { params: searchParams });
  return data;
}

// Поиск товаров по категории
export async function searchProductsByCategory(categoryId, params = {}) {
  const searchParams = { ...params, category: categoryId };
  const { data } = await axios.get('/api/products/products/', { params: searchParams });
  return data;
}

// Поиск товаров по фильтрам (цена, размер, цвет и т.д.)
export async function searchProductsByFilters(filters = {}, params = {}) {
  const searchParams = { ...params, ...filters };
  const { data } = await axios.get('/api/products/products/', { params: searchParams });
  return data;
}

// Получение популярных поисковых запросов
export async function fetchPopularSearches() {
  const { data } = await axios.get('/api/search/popular/');
  return data;
}

// Получение рекомендаций для автозаполнения поиска
export async function fetchSearchSuggestions(query) {
  const { data } = await axios.get('/api/search/suggestions/', { params: { query } });
  return data;
}