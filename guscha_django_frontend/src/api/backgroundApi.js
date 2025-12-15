import axiosInstance from './axiosInstance';

/**
 * API для работы с фоновым контентом
 */
class BackgroundAPI {
  /**
   * Получить активный фоновый контент
   */
  async getActiveBackground() {
    try {
      const response = await axiosInstance.get('/api/background/active/');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Получить список всего фонового контента
   */
  async getAllBackgrounds() {
    try {
      const response = await axiosInstance.get('/api/background/list/');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Получить детальную информацию о фоновом контенте
   * @param {number} id - ID фонового контента
   */
  async getBackgroundDetail(id) {
    try {
      const response = await axiosInstance.get(`/api/background/detail/${id}/`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Активировать фоновый контент
   * @param {number} id - ID фонового контента для активации
   */
  async activateBackground(id) {
    try {
      const response = await axiosInstance.post(`/api/background/activate/${id}/`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Получить список всех фоновых изображений
   */
  async getBackgroundImages() {
    try {
      const response = await axiosInstance.get('/api/background/images/');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Получить список всех слайдшоу
   */
  async getSlideshows() {
    try {
      const response = await axiosInstance.get('/api/background/slideshows/');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Получить детальную информацию о слайдшоу
   * @param {number} id - ID слайдшоу
   */
  async getSlideshowDetail(id) {
    try {
      const response = await axiosInstance.get(`/api/background/slideshows/${id}/`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Получить список всех фоновых видео
   */
  async getBackgroundVideos() {
    try {
      const response = await axiosInstance.get('/api/background/videos/');
      return response.data;
    } catch (error) {
      throw error;
    }
  }
}

const backgroundApi = new BackgroundAPI();
export default backgroundApi;