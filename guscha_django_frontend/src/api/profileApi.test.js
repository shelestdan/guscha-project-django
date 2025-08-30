import axios from './axiosInstance';
import {
  fetchUserProfile,
  updateUserProfile,
  updateUserAvatar,
  fetchUserAddresses,
  addUserAddress,
  updateUserAddress,
  deleteUserAddress,
  setDefaultAddress
} from './profileApi';

// Мокируем axios instance
jest.mock('./axiosInstance');
const mockedAxios = axios;

describe('profileApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchUserProfile', () => {
    it('должен успешно получить профиль пользователя', async () => {
      const mockProfile = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
        phone: '+1234567890',
        avatar: 'avatar.jpg'
      };
      mockedAxios.get.mockResolvedValue({ data: mockProfile });

      const result = await fetchUserProfile();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/accounts/users/me/');
      expect(result).toEqual(mockProfile);
    });

    it('должен обработать ошибку при получении профиля', async () => {
      const errorMessage = 'Unauthorized';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchUserProfile()).rejects.toThrow(errorMessage);
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/accounts/users/me/');
    });
  });

  describe('updateUserProfile', () => {
    it('должен успешно обновить профиль пользователя', async () => {
      const profileData = {
        first_name: 'Updated',
        last_name: 'User',
        phone: '+9876543210'
      };
      const mockUpdatedProfile = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        ...profileData
      };
      mockedAxios.put.mockResolvedValue({ data: mockUpdatedProfile });

      const result = await updateUserProfile(profileData);

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/accounts/users/me/', profileData);
      expect(result).toEqual(mockUpdatedProfile);
    });

    it('должен обработать ошибку валидации при обновлении профиля', async () => {
      const profileData = { email: 'invalid-email' };
      const error = {
        response: {
          status: 400,
          data: { email: ['Enter a valid email address.'] }
        }
      };
      mockedAxios.put.mockRejectedValue(error);

      await expect(updateUserProfile(profileData)).rejects.toEqual(error);
    });
  });

  describe('updateUserAvatar', () => {
    it('должен успешно обновить аватар пользователя', async () => {
      const formData = new FormData();
      formData.append('avatar', new File([''], 'avatar.jpg', { type: 'image/jpeg' }));
      
      const mockResponse = {
        avatar: 'new-avatar.jpg',
        message: 'Avatar updated successfully'
      };
      mockedAxios.post.mockResolvedValue({ data: mockResponse });

      const result = await updateUserAvatar(formData);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/accounts/users/me/avatar/',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('должен обработать ошибку при обновлении аватара', async () => {
      const formData = new FormData();
      const error = {
        response: {
          status: 413,
          data: { error: 'File too large' }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(updateUserAvatar(formData)).rejects.toEqual(error);
    });
  });

  describe('fetchUserAddresses', () => {
    it('должен успешно получить адреса пользователя', async () => {
      const mockAddresses = [
        {
          id: 1,
          street: '123 Main St',
          city: 'New York',
          postal_code: '10001',
          is_default: true
        },
        {
          id: 2,
          street: '456 Oak Ave',
          city: 'Los Angeles',
          postal_code: '90210',
          is_default: false
        }
      ];
      mockedAxios.get.mockResolvedValue({ data: mockAddresses });

      const result = await fetchUserAddresses();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/accounts/addresses/');
      expect(result).toEqual(mockAddresses);
    });

    it('должен обработать ошибку при получении адресов', async () => {
      const errorMessage = 'Network Error';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(fetchUserAddresses()).rejects.toThrow(errorMessage);
    });
  });

  describe('addUserAddress', () => {
    it('должен успешно добавить новый адрес', async () => {
      const addressData = {
        street: '789 Pine St',
        city: 'Chicago',
        postal_code: '60601',
        country: 'USA'
      };
      const mockNewAddress = {
        id: 3,
        ...addressData,
        is_default: false
      };
      mockedAxios.post.mockResolvedValue({ data: mockNewAddress });

      const result = await addUserAddress(addressData);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/accounts/addresses/', addressData);
      expect(result).toEqual(mockNewAddress);
    });

    it('должен обработать ошибку валидации при добавлении адреса', async () => {
      const addressData = { street: '' }; // Невалидные данные
      const error = {
        response: {
          status: 400,
          data: { street: ['This field may not be blank.'] }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(addUserAddress(addressData)).rejects.toEqual(error);
    });
  });

  describe('updateUserAddress', () => {
    it('должен успешно обновить существующий адрес', async () => {
      const addressId = 1;
      const addressData = {
        street: '123 Updated St',
        city: 'New York',
        postal_code: '10002'
      };
      const mockUpdatedAddress = {
        id: addressId,
        ...addressData,
        is_default: true
      };
      mockedAxios.put.mockResolvedValue({ data: mockUpdatedAddress });

      const result = await updateUserAddress(addressId, addressData);

      expect(mockedAxios.put).toHaveBeenCalledWith(
        `/api/accounts/addresses/${addressId}/`,
        addressData
      );
      expect(result).toEqual(mockUpdatedAddress);
    });

    it('должен обработать ошибку 404 при обновлении несуществующего адреса', async () => {
      const addressId = 999;
      const addressData = { street: 'Test St' };
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found.' }
        }
      };
      mockedAxios.put.mockRejectedValue(error);

      await expect(updateUserAddress(addressId, addressData)).rejects.toEqual(error);
    });
  });

  describe('deleteUserAddress', () => {
    it('должен успешно удалить адрес', async () => {
      const addressId = 1;
      mockedAxios.delete.mockResolvedValue({});

      const result = await deleteUserAddress(addressId);

      expect(mockedAxios.delete).toHaveBeenCalledWith(`/api/accounts/addresses/${addressId}/`);
      expect(result).toBe(true);
    });

    it('должен обработать ошибку при удалении адреса', async () => {
      const addressId = 1;
      const errorMessage = 'Cannot delete default address';
      mockedAxios.delete.mockRejectedValue(new Error(errorMessage));

      await expect(deleteUserAddress(addressId)).rejects.toThrow(errorMessage);
    });

    it('должен обработать ошибку 404 при удалении несуществующего адреса', async () => {
      const addressId = 999;
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found.' }
        }
      };
      mockedAxios.delete.mockRejectedValue(error);

      await expect(deleteUserAddress(addressId)).rejects.toEqual(error);
    });
  });

  describe('setDefaultAddress', () => {
    it('должен успешно установить адрес по умолчанию', async () => {
      const addressId = 2;
      const mockResponse = {
        message: 'Default address updated successfully',
        address_id: addressId
      };
      mockedAxios.post.mockResolvedValue({ data: mockResponse });

      const result = await setDefaultAddress(addressId);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `/api/accounts/addresses/${addressId}/set_default/`
      );
      expect(result).toEqual(mockResponse);
    });

    it('должен обработать ошибку при установке адреса по умолчанию', async () => {
      const addressId = 999;
      const error = {
        response: {
          status: 404,
          data: { detail: 'Address not found.' }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(setDefaultAddress(addressId)).rejects.toEqual(error);
    });

    it('должен обработать ошибку доступа при установке чужого адреса', async () => {
      const addressId = 1;
      const error = {
        response: {
          status: 403,
          data: { detail: 'You do not have permission to perform this action.' }
        }
      };
      mockedAxios.post.mockRejectedValue(error);

      await expect(setDefaultAddress(addressId)).rejects.toEqual(error);
    });
  });
});