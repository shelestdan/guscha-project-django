import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import * as authApi from '../api/authApi';

export const useUserStore = create(devtools((set, get) => ({
  user: null,
  accessToken: null,
  isLoggedIn: false,
  loading: false,
  csrfToken: null,

  login: async (email, password) => {
    set({ loading: true });
    try {
      const data = await authApi.login(email, password);
      set({ user: data.user, accessToken: data.access_token, isLoggedIn: true });
    } finally {
      set({ loading: false });
    }
  },

  register: async (userData) => {
    set({ loading: true });
    try {
      const data = await authApi.register(userData);
      set({ user: data.user, accessToken: data.access_token, isLoggedIn: true });
    } finally {
      set({ loading: false });
    }
  },

  fetchProfile: async () => {
    set({ loading: true });
    try {
      const { accessToken } = get();
      const data = await authApi.fetchProfile(accessToken);
      set({ user: data.user });
    } finally {
      set({ loading: false });
    }
  },

  refresh: async () => {
    const data = await authApi.refresh();
    set({ accessToken: data.access_token, isLoggedIn: true });
    return data.access_token;
  },

  logout: async () => {
    await authApi.logout();
    set({ user: null, accessToken: null, isLoggedIn: false });
  },

  googleLogin: async (id_token) => {
    set({ loading: true });
    try {
      const data = await authApi.googleLogin(id_token);
      set({ user: data.user, accessToken: data.access_token, isLoggedIn: true });
    } finally {
      set({ loading: false });
    }
  },

  fetchCsrfToken: async () => {
    const token = await authApi.getCsrfToken();
    set({ csrfToken: token });
    return token;
  },
}))); 