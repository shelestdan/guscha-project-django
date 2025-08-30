import { getCartSessionId, clearCartSessionId } from './cartSession';

// Мокируем localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: jest.fn((index) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    })
  };
})();

// Переопределяем localStorage глобально
Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true
});

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true
});

describe('cartSession', () => {
  beforeEach(() => {
    // Очищаем localStorage перед каждым тестом
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  describe('getCartSessionId', () => {
    it('должен возвращать существующий session ID из localStorage', () => {
      const existingSessionId = 'existing-session-id';
      // Устанавливаем значение в store напрямую
      localStorageMock.getItem.mockReturnValue(existingSessionId);

      const result = getCartSessionId();

      expect(result).toBe(existingSessionId);
      expect(localStorageMock.getItem).toHaveBeenCalledWith('cart_session_id');
    });

    it('должен генерировать новый session ID если его нет в localStorage', () => {
      const result = getCartSessionId();

      expect(localStorageMock.getItem).toHaveBeenCalledWith('cart_session_id');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('cart_session_id', expect.any(String));
      expect(result).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    });

    it('должен генерировать валидный UUID v4', () => {
      const result = getCartSessionId();
      
      // Проверяем формат UUID v4
      expect(result).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
      expect(result).toHaveLength(36);
    });

    it('должен возвращать один и тот же ID при повторных вызовах', () => {
      // При первом вызове localStorage пуст, генерируется новый ID
      localStorageMock.getItem.mockReturnValueOnce(null);
      const firstCall = getCartSessionId();
      
      // При втором вызове localStorage уже содержит ID
      localStorageMock.getItem.mockReturnValue(firstCall);
      const secondCall = getCartSessionId();

      expect(firstCall).toBe(secondCall);
    });
  });

  describe('clearCartSessionId', () => {
    it('должен удалять session ID из localStorage', () => {
      // Сначала устанавливаем session ID
      localStorageMock.setItem('cart_session_id', 'test-session-id');
      
      clearCartSessionId();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('cart_session_id');
    });

    it('должен работать корректно даже если session ID не существует', () => {
      clearCartSessionId();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('cart_session_id');
      expect(() => clearCartSessionId()).not.toThrow();
    });

    it('должен позволить создать новый session ID после очистки', () => {
      // Создаем session ID
      const firstSessionId = getCartSessionId();
      
      // Очищаем
      clearCartSessionId();
      
      // Создаем новый
      const newSessionId = getCartSessionId();
      
      expect(firstSessionId).not.toBe(newSessionId);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('cart_session_id');
    });
  });
});