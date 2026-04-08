/* global describe, it, expect, beforeEach, afterEach */
import '@testing-library/jest-dom';

describe('axiosInstance', () => {
  const originalEnv = process.env.REACT_APP_API_URL;

  beforeEach(() => {
    localStorage.clear();
    document.cookie = '';
  });

  afterEach(() => {
    process.env.REACT_APP_API_URL = originalEnv;
    jest.resetModules();
  });

  it('использует REACT_APP_API_URL как baseURL при наличии', () => {
    process.env.REACT_APP_API_URL = 'https://api.example.com';

    jest.isolateModules(() => {
      const instance = require('./axiosInstance').default; // eslint-disable-line global-require
      expect(instance.defaults.baseURL).toBe('https://api.example.com');
    });
  });

  it('добавляет Authorization, CSRF и X-Session-ID заголовки', () => {
    jest.isolateModules(() => {
      const localStorageMock = {
        getItem: (key) => {
          if (key === 'access_token') return 'jwt-123';
          if (key === 'cart_session_id') return 'session-456';
          return null;
        },
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      };
      Object.defineProperty(window, 'localStorage', {
        value: localStorageMock,
        writable: true,
      });
      document.cookie = 'csrftoken=csrf-token-value';

      const instance = require('./axiosInstance').default; // eslint-disable-line global-require
      const handler = instance.interceptors.request.handlers[0].fulfilled;

      const config = handler({
        url: '/api/cart/add/',
        method: 'post',
        headers: {},
      });

      expect(config.headers['Authorization']).toBe('Bearer jwt-123');
      expect(config.headers['X-CSRFToken']).toBe('csrf-token-value');
      expect(config.headers['X-Session-ID']).toBe('session-456');
    });
  });
});

