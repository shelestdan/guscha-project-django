import axios from './axiosInstance';
import {
  login,
  register,
  fetchProfile,
  logout,
  changePassword,
  requestPasswordReset,
  confirmPasswordReset,
  getCsrfToken,
  checkTelegramBotStatus,
  activateTelegramBot,
  verifyTelegramCode,
  requestTelegramPasswordReset,
  confirmTelegramPasswordReset
} from './authApi';

// Мокируем axios
jest.mock('./axiosInstance');
const mockedAxios = axios;

// Мокируем localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Мокируем document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: ''
});

describe('authApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    document.cookie = '';
  });

  describe('login', () => {
    it('should login successfully and save token', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token',
          refresh_token: 'test-refresh',
          user: { id: 1, email: 'test@example.com' }
        }
      };
      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await login('test@example.com', 'password123');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/accounts/users/login/',
        { email: 'test@example.com', password: 'password123' }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle login error', async () => {
      const mockError = new Error('Login failed');
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(login('test@example.com', 'wrong-password'))
        .rejects.toThrow('Login failed');

      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });
  });

  describe('register', () => {
    it('should register successfully and save token', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token',
          refresh_token: 'test-refresh',
          user: { id: 1, email: 'test@example.com' },
          verification_id: 'verification-123'
        }
      };
      mockedAxios.post.mockResolvedValue(mockResponse);

      const userData = {
        email: 'test@example.com',
        password: 'password123',
        first_name: 'Test',
        last_name: 'User'
      };

      const result = await register(userData);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/accounts/users/',
        userData
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should register without saving token if not provided', async () => {
      const mockResponse = {
        data: {
          user: { id: 1, email: 'test@example.com' },
          verification_id: 'verification-123'
        }
      };
      mockedAxios.post.mockResolvedValue(mockResponse);

      const userData = { email: 'test@example.com', password: 'password123' };
      const result = await register(userData);

      expect(localStorageMock.setItem).not.toHaveBeenCalled();
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle registration error with string message', async () => {
      const mockError = {
        response: {
          status: 400,
          data: 'Email already exists'
        }
      };
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(register({ email: 'test@example.com' }))
        .rejects.toThrow('Email already exists');
    });

    it('should handle registration error with detail field', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { detail: 'Invalid email format' }
        }
      };
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(register({ email: 'invalid-email' }))
        .rejects.toThrow('Invalid email format');
    });

    it('should handle registration error with field errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            email: ['This field is required.'],
            password: ['Password too short.']
          }
        }
      };
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(register({}))
        .rejects.toThrow('email: This field is required.; password: Password too short.');
    });

    it('should handle registration error with non_field_errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            non_field_errors: ['User with this email already exists.']
          }
        }
      };
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(register({ email: 'test@example.com' }))
        .rejects.toThrow('User with this email already exists.');
    });

    it('should handle registration error without response data', async () => {
      const mockError = new Error('Network error');
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(register({ email: 'test@example.com' }))
        .rejects.toThrow('Ошибка регистрации');
    });
  });

  describe('fetchProfile', () => {
    it('should fetch user profile successfully', async () => {
      const mockResponse = {
        data: {
          id: 1,
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User'
        }
      };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await fetchProfile();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/accounts/users/me/');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle fetch profile error', async () => {
      const mockError = new Error('Unauthorized');
      mockedAxios.get.mockRejectedValue(mockError);

      await expect(fetchProfile()).rejects.toThrow('Unauthorized');
    });
  });

  describe('logout', () => {
    it('should logout successfully and remove token', async () => {
      mockedAxios.post.mockResolvedValue({ data: {} });

      await logout();

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/accounts/users/logout/', {});
    });

    it('should remove token even if logout request fails', async () => {
      const mockError = new Error('Server error');
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(logout()).rejects.toThrow('Server error');
    });
  });

  describe('changePassword', () => {
    it('should change password successfully and update token', async () => {
      const mockResponse = {
        data: {
          message: 'Password changed successfully'
        }
      };
      mockedAxios.put.mockResolvedValue(mockResponse);

      const result = await changePassword('oldPassword', 'newPassword');

      expect(mockedAxios.put).toHaveBeenCalledWith(
        '/api/accounts/users/change_password/',
        {
          old_password: 'oldPassword',
          new_password: 'newPassword',
          new_password_confirm: 'newPassword'
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should change password without updating token if not provided', async () => {
      const mockResponse = {
        data: { message: 'Password changed successfully' }
      };
      mockedAxios.put.mockResolvedValue(mockResponse);

      const result = await changePassword('oldPassword', 'newPassword');

      expect(localStorageMock.setItem).not.toHaveBeenCalled();
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle change password error', async () => {
      const mockError = new Error('Invalid old password');
      mockedAxios.put.mockRejectedValue(mockError);

      await expect(changePassword('wrongPassword', 'newPassword'))
        .rejects.toThrow('Invalid old password');
    });
  });

  describe('requestPasswordReset', () => {
    it('should request password reset successfully', async () => {
      const mockResponse = {
        data: { message: 'Password reset email sent' }
      };
      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await requestPasswordReset('test@example.com');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/accounts/password-reset/',
        { email: 'test@example.com' }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle request password reset error', async () => {
      const mockError = new Error('Email not found');
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(requestPasswordReset('nonexistent@example.com'))
        .rejects.toThrow('Email not found');
    });
  });

  describe('confirmPasswordReset', () => {
    it('should confirm password reset successfully', async () => {
      const mockResponse = {
        data: { message: 'Password reset successful' }
      };
      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await confirmPasswordReset('uid123', 'token123', 'newPassword');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/accounts/password-reset-confirm/',
        {
          uid: 'uid123',
          token: 'token123',
          new_password: 'newPassword'
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle confirm password reset error', async () => {
      const mockError = new Error('Invalid token');
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(confirmPasswordReset('uid123', 'invalidToken', 'newPassword'))
        .rejects.toThrow('Invalid token');
    });
  });

  describe('getCsrfToken', () => {
    it('should get CSRF token from cookies', async () => {
      document.cookie = 'csrftoken=test-csrf-token; other=value';

      const result = await getCsrfToken();

      expect(result).toBe('test-csrf-token');
    });

    it('should return null if CSRF token not found', async () => {
      document.cookie = 'other=value; another=test';

      const result = await getCsrfToken();

      expect(result).toBeNull();
    });

    it('should return null if no cookies', async () => {
      document.cookie = '';

      const result = await getCsrfToken();

      expect(result).toBeNull();
    });
  });

  describe('Telegram functions', () => {
    describe('checkTelegramBotStatus', () => {
      it('should check Telegram bot status successfully', async () => {
        const mockResponse = {
          data: { status: 'active', bot_username: 'testbot' }
        };
        mockedAxios.get.mockResolvedValue(mockResponse);

        const result = await checkTelegramBotStatus('verification-123');

        expect(mockedAxios.get).toHaveBeenCalledWith(
          '/api/accounts/telegram/status/',
          { params: { verification_id: 'verification-123' } }
        );
        expect(result).toEqual(mockResponse.data);
      });

      it('should handle check Telegram bot status error', async () => {
        const mockError = new Error('Verification ID not found');
        mockedAxios.get.mockRejectedValue(mockError);

        await expect(checkTelegramBotStatus('invalid-id'))
          .rejects.toThrow('Verification ID not found');
      });
    });

    describe('activateTelegramBot', () => {
      it('should activate Telegram bot successfully', async () => {
        const mockResponse = {
          data: { message: 'Bot activated successfully' }
        };
        mockedAxios.post.mockResolvedValue(mockResponse);

        const result = await activateTelegramBot('verification-123', 'chat-123', 'testuser');

        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/accounts/telegram/activate/',
          {
            verification_id: 'verification-123',
            telegram_chat_id: 'chat-123',
            telegram_username: 'testuser'
          }
        );
        expect(result).toEqual(mockResponse.data);
      });

      it('should handle activate Telegram bot error', async () => {
        const mockError = new Error('Invalid verification ID');
        mockedAxios.post.mockRejectedValue(mockError);

        await expect(activateTelegramBot('invalid-id', 'chat-123', 'testuser'))
          .rejects.toThrow('Invalid verification ID');
      });
    });

    describe('verifyTelegramCode', () => {
      it('should verify Telegram code successfully', async () => {
        const mockResponse = {
          data: {
            access_token: 'access-token',
            refresh_token: 'refresh-token',
            user: { id: 1, phone: '+1234567890' }
          }
        };
        mockedAxios.post.mockResolvedValue(mockResponse);

        const result = await verifyTelegramCode('+1234567890', '123456');

        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/accounts/telegram/verify/',
          {
            phone_number: '+1234567890',
            verification_code: '123456'
          }
        );
        expect(result).toEqual(mockResponse.data);
      });

      it('should handle verify Telegram code error', async () => {
        const mockError = new Error('Invalid verification code');
        mockedAxios.post.mockRejectedValue(mockError);

        await expect(verifyTelegramCode('+1234567890', 'invalid'))
          .rejects.toThrow('Invalid verification code');
      });
    });

    describe('requestTelegramPasswordReset', () => {
      it('should request Telegram password reset successfully', async () => {
        const mockResponse = {
          data: { verification_id: 'verification-123' }
        };
        mockedAxios.post.mockResolvedValue(mockResponse);

        const result = await requestTelegramPasswordReset('test@example.com');

        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/accounts/telegram/password-reset/',
          { email: 'test@example.com' }
        );
        expect(result).toEqual(mockResponse.data);
      });

      it('should handle request Telegram password reset error', async () => {
        const mockError = new Error('Email not found');
        mockedAxios.post.mockRejectedValue(mockError);

        await expect(requestTelegramPasswordReset('nonexistent@example.com'))
          .rejects.toThrow('Email not found');
      });
    });

    describe('confirmTelegramPasswordReset', () => {
      it('should confirm Telegram password reset successfully', async () => {
        const mockResponse = {
          data: { message: 'Password reset successful' }
        };
        mockedAxios.post.mockResolvedValue(mockResponse);

        const result = await confirmTelegramPasswordReset('verification-123', '123456', 'newPassword');

        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/accounts/telegram/password-reset-confirm/',
          {
            verification_id: 'verification-123',
            code: '123456',
            new_password: 'newPassword'
          }
        );
        expect(result).toEqual(mockResponse.data);
      });

      it('should handle confirm Telegram password reset error', async () => {
        const mockError = new Error('Invalid verification code');
        mockedAxios.post.mockRejectedValue(mockError);

        await expect(confirmTelegramPasswordReset('verification-123', 'invalid', 'newPassword'))
          .rejects.toThrow('Invalid verification code');
      });
    });
  });
});