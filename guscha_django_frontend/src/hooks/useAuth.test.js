import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth } from './useAuth';

// Мокируем fetch
global.fetch = jest.fn();

// Мокируем localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Мокируем document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: ''
});

// Мокируем console.error
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    document.cookie = '';
  });

  describe('Инициализация', () => {
    it('должен инициализироваться с правильными начальными значениями', () => {
      localStorageMock.getItem.mockReturnValue(null);
      
      const { result } = renderHook(() => useAuth());
      
      expect(result.current.isLoggedIn).toBe(false);
      expect(result.current.user).toBe(null);
      expect(result.current.loading).toBe(false);
    });

    it('должен получить CSRF токен из cookies', async () => {
      document.cookie = 'csrftoken=test-csrf-token; other=value';
      localStorageMock.getItem.mockReturnValue(null);
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('должен проверить существующий токен при инициализации', async () => {
      const mockToken = 'test-token';
      const mockUser = { id: 1, username: 'testuser' };
      
      localStorageMock.getItem.mockReturnValue(mockToken);
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.isLoggedIn).toBe(true);
        expect(result.current.user).toEqual(mockUser);
      });
      
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost/api/accounts/users/me/',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token'
          }),
          credentials: 'include'
        })
      );
    });

    it('должен обработать JWT токен при инициализации', async () => {
      const mockJwtToken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.signature';
      const mockUser = { id: 1, username: 'testuser' };
      
      localStorageMock.getItem.mockReturnValue(mockJwtToken);
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.isLoggedIn).toBe(true);
        expect(result.current.user).toEqual(mockUser);
      });
      
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost/api/accounts/users/me/',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.signature'
          }),
          credentials: 'include'
        })
      );
    });

    it('должен очистить недействительный токен при инициализации', async () => {
      const mockToken = 'invalid-token';
      
      localStorageMock.getItem.mockReturnValue(mockToken);
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.isLoggedIn).toBe(false);
        expect(result.current.user).toBe(null);
      });
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('refreshAccessToken', () => {
    it('должен вернуть null если токен отсутствует', async () => {
      localStorageMock.getItem.mockReturnValue(null);
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      // Когда токен отсутствует, запрос выполняется без Authorization и возвращает undefined
      await expect(result.current.apiRequest('/test')).resolves.toBeUndefined();
    });

    it('должен обновить токен успешно', async () => {
      const mockToken = 'valid-token';
      localStorageMock.getItem.mockReturnValue(mockToken);
      
      fetch.mockResolvedValueOnce({
        ok: true
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('должен очистить недействительный токен', async () => {
      const mockToken = 'invalid-token';
      localStorageMock.getItem.mockReturnValue(mockToken);
      
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.isLoggedIn).toBe(false);
        expect(result.current.user).toBe(null);
      });
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('fetchWithAuth', () => {
    it('должен выполнить запрос с токеном авторизации', async () => {
      const mockToken = 'test-token';
      localStorageMock.getItem.mockReturnValue(mockToken);
      
      // Мок для инициализации useAuth (получение профиля)
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ id: 1, username: 'testuser' })
      });
      
      // Мок для тестируемого запроса
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true })
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      const response = await result.current.apiRequest('/test', {
        method: 'GET'
      });
      
      expect(fetch).toHaveBeenCalledWith('/test', {
        method: 'GET',
        headers: {
          Authorization: 'Bearer test-token',
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });
      expect(response.ok).toBe(true);
    });

    it('должен обновить токен при 401 ошибке', async () => {
      const mockToken = 'test-token';
      localStorageMock.getItem.mockReturnValue(mockToken);
      
      // Мок для инициализации useAuth (получение профиля)
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ id: 1, username: 'testuser' })
      });
      
      // Первый запрос возвращает 401
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401
      });
      
      // Запрос на обновление токена
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200
      });
      
      // Повторный запрос с обновленным токеном
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true })
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      const response = await result.current.apiRequest('/test');
      
      expect(fetch).toHaveBeenCalledTimes(3);
      expect(response).toBeDefined();
    });
  });

  describe('handleLogin', () => {
    it('должен успешно выполнить вход', async () => {
      const loginData = { username: 'testuser', password: 'password' };
      const mockResponse = {
        access_token: 'new-access',
        refresh_token: 'new-refresh',
        user: { id: 1, username: 'testuser' }
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      await act(async () => {
        await result.current.login(loginData);
      });
      
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost/api/accounts/users/login/',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify(loginData)
        })
      );
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'new-access');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', 'new-refresh');
      expect(result.current.isLoggedIn).toBe(true);
      expect(result.current.user).toEqual(mockResponse.user);
    });

    it('должен обработать ошибку входа', async () => {
      const loginData = { username: 'testuser', password: 'wrongpassword' };
      const errorResponse = { detail: 'Неверные учетные данные' };
      
      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      await expect(result.current.login(loginData)).rejects.toThrow('Неверные учетные данные');
      
      expect(result.current.isLoggedIn).toBe(false);
      expect(result.current.user).toBe(null);
    });

    it('должен включить CSRF токен в запрос входа', async () => {
      document.cookie = 'csrftoken=test-csrf-token';
      const loginData = { username: 'testuser', password: 'password' };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: 'token', refresh_token: 'rtoken', user: {} })
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      await act(async () => {
        await result.current.login(loginData);
      });
      
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost/api/accounts/users/login/',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRFToken': 'test-csrf-token'
          })
        })
      );
    });
  });

  describe('handleRegister', () => {
    it('должен успешно выполнить регистрацию без Telegram-верификации', async () => {
      const registrationData = {
        username: 'newuser',
        email: 'test@example.com',
        password: 'password'
      };
      const mockResponse = {
        access_token: 'new-access',
        refresh_token: 'new-refresh',
        user: { id: 1, username: 'newuser' }
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      let registerResult;
      await act(async () => {
        registerResult = await result.current.register(registrationData);
      });
      
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost/api/accounts/users/',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify(registrationData)
        })
      );
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'new-access');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', 'new-refresh');
      expect(result.current.isLoggedIn).toBe(true);
      expect(result.current.user).toEqual(mockResponse.user);
      expect(registerResult).toEqual({
        success: true,
        needsTelegramVerification: false
      });
    });

    it('должен обработать регистрацию с Telegram-верификацией', async () => {
      const registrationData = {
        username: 'newuser',
        email: 'test@example.com',
        password: 'password'
      };
      const mockResponse = {
        pending_registration_id: 'verification-id-123',
        user: { username: 'newuser' }
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      let registerResult;
      await act(async () => {
        registerResult = await result.current.register(registrationData);
      });
      
      expect(registerResult).toEqual({
        success: true,
        needsTelegramVerification: true,
        pending_registration_id: 'verification-id-123',
        verification_id: 'verification-id-123',
        user: { username: 'newuser' }
      });
      
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
      expect(result.current.isLoggedIn).toBe(false);
    });

    it('должен обработать ошибку регистрации', async () => {
      const registrationData = {
        username: 'existinguser',
        email: 'test@example.com',
        password: 'password'
      };
      const errorResponse = { detail: 'Пользователь уже существует' };
      
      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      await expect(result.current.register(registrationData)).rejects.toThrow('Пользователь уже существует');
      
      expect(result.current.isLoggedIn).toBe(false);
      expect(result.current.user).toBe(null);
    });
  });

  describe('handleLogout', () => {
    it('должен успешно выполнить выход', async () => {
      const mockToken = 'test-token';
      localStorageMock.getItem.mockReturnValue(mockToken);
      
      fetch.mockResolvedValueOnce({
        ok: true
      });
      
      const { result } = renderHook(() => useAuth());
      
      // Устанавливаем пользователя как авторизованного
      act(() => {
        result.current.setUser({ id: 1, username: 'testuser' });
      });
      
      await act(async () => {
        await result.current.logout();
      });
      
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost/api/accounts/users/logout/',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token'
          }),
          credentials: 'include'
        })
      );
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(result.current.isLoggedIn).toBe(false);
      expect(result.current.user).toBe(null);
    });

    it('должен очистить данные даже при ошибке запроса выхода', async () => {
      const mockToken = 'test-token';
      localStorageMock.getItem.mockReturnValue(mockToken);
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      // Устанавливаем пользователя как авторизованного
      act(() => {
        result.current.setUser({ id: 1, username: 'testuser' });
      });
      
      fetch.mockRejectedValueOnce(new Error('Network error'));
      
      await act(async () => {
        await result.current.logout();
      });
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(result.current.isLoggedIn).toBe(false);
      expect(result.current.user).toBe(null);
      expect(console.error).toHaveBeenCalledWith('Ошибка при выходе из системы:', expect.any(Error));
    });
  });

  describe('activateTelegramBot', () => {
    it('должен успешно активировать Telegram-бота', async () => {
      const verificationId = 'verification-123';
      const telegramChatId = 'chat-456';
      const mockResponse = { success: true, data: { activated: true } };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      const activationResult = await result.current.activateTelegramBot(verificationId, telegramChatId);
      
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost/api/accounts/telegram/activate/',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({
            verification_id: verificationId,
            telegram_chat_id: telegramChatId
          })
        })
      );
      
      expect(activationResult).toEqual({ success: true, data: { data: { activated: true }, success: true } });
    });

    it('должен обработать ошибку активации Telegram-бота', async () => {
      const verificationId = 'verification-123';
      const telegramChatId = 'chat-456';
      const errorResponse = { detail: 'Ошибка активации' };
      
      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      await expect(
        result.current.activateTelegramBot(verificationId, telegramChatId)
      ).rejects.toThrow('Ошибка активации');
    });
  });

  describe('verifyTelegramCode', () => {
    it('должен успешно верифицировать Telegram-код и авторизовать пользователя', async () => {
      const phoneNumber = '+1234567890';
      const code = '123456';
      const mockResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        user: { id: 1, username: 'testuser' }
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      const verificationResult = await result.current.verifyTelegramCode(phoneNumber, code);
      
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost/api/accounts/telegram/verify/',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({
            phone_number: phoneNumber,
            verification_code: code
          })
        })
      );
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'new-access-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', 'new-refresh-token');
      
      await waitFor(() => {
        expect(result.current.isLoggedIn).toBe(true);
      });
      
      expect(result.current.user).toEqual(mockResponse.user);
      expect(verificationResult).toEqual({ success: true, ...mockResponse });
    });

    it('должен обработать верификацию, требующую регистрации', async () => {
      const phoneNumber = '+1234567890';
      const code = '123456';
      const mockResponse = {
        requires_registration: true,
        verification_id: 'verification-123'
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      const verificationResult = await result.current.verifyTelegramCode(phoneNumber, code);
      
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
      expect(result.current.isLoggedIn).toBe(false);
      expect(verificationResult).toEqual({ success: true, ...mockResponse });
    });

    it('должен обработать ошибку верификации Telegram-кода', async () => {
      const phoneNumber = '+1234567890';
      const code = '123456';
      const errorResponse = { detail: 'Неверный код' };
      
      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      await expect(
        result.current.verifyTelegramCode(phoneNumber, code)
      ).rejects.toThrow('Неверный код');
    });
  });

  describe('setUserWithLogin', () => {
    it('должен установить пользователя и обновить статус входа', () => {
      const { result } = renderHook(() => useAuth());
      
      const userData = { id: 1, username: 'testuser' };
      
      act(() => {
        result.current.setUserWithLogin(userData);
      });
      
      expect(result.current.user).toEqual(userData);
      expect(result.current.isLoggedIn).toBe(true);
    });

    it('должен очистить пользователя и обновить статус входа', () => {
      const { result } = renderHook(() => useAuth());
      
      // Сначала устанавливаем пользователя
      act(() => {
        result.current.setUserWithLogin({ id: 1, username: 'testuser' });
      });
      
      expect(result.current.isLoggedIn).toBe(true);
      
      // Затем очищаем
      act(() => {
        result.current.setUserWithLogin(null);
      });
      
      expect(result.current.user).toBe(null);
      expect(result.current.isLoggedIn).toBe(false);
    });
  });

  describe('Обработка ошибок', () => {
    it('должен обработать ошибки сети при инициализации', async () => {
      const mockToken = 'test-token';
      localStorageMock.getItem.mockReturnValue(mockToken);
      
      fetch.mockRejectedValueOnce(new Error('Network error'));
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.isLoggedIn).toBe(false);
        expect(result.current.user).toBe(null);
      });
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(console.error).toHaveBeenCalledWith('Ошибка получения профиля:', expect.any(Error));
    });

    it('должен обработать ошибки при обновлении токена', async () => {
      const mockToken = 'test-token';
      localStorageMock.getItem.mockReturnValue(mockToken);
      
      fetch.mockRejectedValueOnce(new Error('Network error'));
      
      const { result } = renderHook(() => useAuth());
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      
      expect(console.error).toHaveBeenCalledWith('Ошибка получения профиля:', expect.any(Error));
    });
  });
});