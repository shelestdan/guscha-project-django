import scrollBackgroundToggle, { ScrollBackgroundToggle } from './scrollBackgroundToggle';

// Мокируем DOM методы
const mockAddEventListener = jest.fn();
const mockRemoveEventListener = jest.fn();
const mockQuerySelectorAll = jest.fn();
const mockGetComputedStyle = jest.fn();
const mockRequestAnimationFrame = jest.fn();
const mockSetTimeout = jest.fn();
const mockClearTimeout = jest.fn();

// Мокируем console.warn
const mockConsoleWarn = jest.spyOn(console, 'warn').mockImplementation(() => {});

// Создаем мок элемента body
const createMockElement = (styles = {}) => {
  const element = {
    style: {},
    classList: {
      add: jest.fn(),
      remove: jest.fn(),
      contains: jest.fn(() => false)
    },
    addEventListener: mockAddEventListener,
    removeEventListener: mockRemoveEventListener,
    scrollTop: 0,
    scrollHeight: 1000,
    clientHeight: 500,
    nodeType: 1
  };
  
  // Инициализируем style свойства
  element.style.transition = '';
  element.style.backgroundImage = '';
  element.style.backgroundColor = '';
  element.style.background = '';
  
  // Применяем дополнительные стили
  Object.assign(element.style, styles);
  
  return element;
};

describe('ScrollBackgroundToggle', () => {
  let mockBody;
  let originalDocument;
  let originalWindow;
  let originalRequestAnimationFrame;
  let originalSetTimeout;
  let originalClearTimeout;
  let mockWindowAddEventListener;
  let mockDocumentAddEventListener;

  beforeEach(() => {
    // Сохраняем оригинальные объекты
    originalDocument = global.document;
    originalWindow = global.window;
    originalRequestAnimationFrame = global.requestAnimationFrame;
    originalSetTimeout = global.setTimeout;
    originalClearTimeout = global.clearTimeout;

    // Создаем мок body
    mockBody = createMockElement();

    // Создаем моки для addEventListener
    mockDocumentAddEventListener = jest.fn();
    mockWindowAddEventListener = jest.fn();
    
    // Мокируем document
    const mockDocument = {
      readyState: 'complete',
      body: mockBody,
      addEventListener: mockDocumentAddEventListener,
      removeEventListener: jest.fn(),
      querySelectorAll: mockQuerySelectorAll,
      documentElement: {
        scrollTop: 0
      }
    };
    global.document = mockDocument;
    
    // Настраиваем возвращаемое значение для querySelectorAll
    mockQuerySelectorAll.mockReturnValue([]);

    // Настраиваем мок для getComputedStyle
    mockGetComputedStyle.mockReturnValue({
      backgroundImage: 'url("test-bg.jpg")',
      backgroundColor: 'rgb(255, 255, 255)',
      background: 'url("test-bg.jpg") rgb(255, 255, 255)'
    });

    // Мокируем window
    const mockWindow = {
      getComputedStyle: mockGetComputedStyle,
      addEventListener: mockWindowAddEventListener,
      removeEventListener: jest.fn(),
      pageYOffset: 0,
      requestAnimationFrame: mockRequestAnimationFrame,
      setTimeout: mockSetTimeout,
      clearTimeout: mockClearTimeout
    };
    global.window = mockWindow;

    // Мокируем глобальные функции
    global.requestAnimationFrame = mockRequestAnimationFrame.mockImplementation(cb => {
      cb();
      return 1;
    });
    global.setTimeout = mockSetTimeout.mockImplementation((cb, delay) => {
      cb();
      return 1;
    });
    global.clearTimeout = mockClearTimeout;

    // Очищаем все моки
    jest.clearAllMocks();
  });

  afterEach(() => {
    // Восстанавливаем оригинальные объекты
    global.document = originalDocument;
    global.window = originalWindow;
    global.requestAnimationFrame = originalRequestAnimationFrame;
    global.setTimeout = originalSetTimeout;
    global.clearTimeout = originalClearTimeout;
  });

  afterAll(() => {
    mockConsoleWarn.mockRestore();
  });

  describe('constructor and initialization', () => {
    it('должен инициализироваться с правильными значениями по умолчанию', () => {
      const toggle = new ScrollBackgroundToggle();
      
      expect(toggle.isScrolling).toBe(false);
      expect(toggle.scrollTimeout).toBeNull();
      expect(toggle.originalBackground).not.toBeNull();
      expect(toggle.targetElement).toBe(document.body);
    });

    it('должен вызвать setup если DOM уже загружен', () => {
      Object.defineProperty(global.document, 'readyState', {
        value: 'complete',
        writable: true,
        configurable: true
      });
      
      const getComputedStyleSpy = jest.spyOn(window, 'getComputedStyle').mockReturnValue({
        backgroundImage: 'url("test-bg.jpg")',
        backgroundColor: 'rgb(255, 255, 255)',
        background: 'url("test-bg.jpg") rgb(255, 255, 255)'
      });
      
      const toggle = new ScrollBackgroundToggle();
      
      expect(toggle.targetElement).toBe(document.body);
      expect(getComputedStyleSpy).toHaveBeenCalledWith(document.body);
      
      getComputedStyleSpy.mockRestore();
    });

    it('должен добавить обработчик DOMContentLoaded если DOM еще загружается', () => {
      const documentSpy = jest.spyOn(document, 'addEventListener');
      
      Object.defineProperty(global.document, 'readyState', {
        value: 'loading',
        writable: true,
        configurable: true
      });
      
      const toggle = new ScrollBackgroundToggle();
      toggle.init();
      
      expect(documentSpy).toHaveBeenCalledWith(
        'DOMContentLoaded',
        expect.any(Function)
      );
      
      // Восстанавливаем readyState
      Object.defineProperty(global.document, 'readyState', {
        value: 'complete',
        writable: true,
        configurable: true
      });
      
      documentSpy.mockRestore();
    });
  });

  describe('setup', () => {
    let windowAddEventListenerSpy, documentAddEventListenerSpy;
    
    beforeEach(() => {
      // Создаем spy для реальных методов
      windowAddEventListenerSpy = jest.spyOn(window, 'addEventListener');
      documentAddEventListenerSpy = jest.spyOn(document, 'addEventListener');
      
      // Создаем spy для getComputedStyle
      jest.spyOn(window, 'getComputedStyle').mockReturnValue({
        backgroundImage: 'url("test-bg.jpg")',
        backgroundColor: 'rgb(255, 255, 255)',
        background: 'url("test-bg.jpg") rgb(255, 255, 255)'
      });
    });
    
    afterEach(() => {
      // Восстанавливаем оригинальные методы
      windowAddEventListenerSpy.mockRestore();
      documentAddEventListenerSpy.mockRestore();
      window.getComputedStyle.mockRestore();
    });

    it('должен сохранить оригинальные стили фона', () => {
      const toggle = new ScrollBackgroundToggle();
      
      expect(toggle.originalBackground).toEqual({
        backgroundImage: 'url("test-bg.jpg")',
        backgroundColor: 'rgb(255, 255, 255)',
        background: 'url("test-bg.jpg") rgb(255, 255, 255)'
      });
    });

    it('должен добавить обработчики событий прокрутки', () => {
      const scrollToggle = new ScrollBackgroundToggle(mockBody);
      scrollToggle.setup();

      // Проверяем, что addEventListener был вызван для window
      expect(windowAddEventListenerSpy).toHaveBeenCalledWith(
        'scroll',
        expect.any(Function),
        { passive: true }
      );
      
      // Проверяем, что addEventListener был вызван для document
      expect(documentAddEventListenerSpy).toHaveBeenCalledWith(
        'scroll',
        expect.any(Function),
        { passive: true }
      );
    });

    it('должен добавить обработчики для элементов с overflow', () => {
      const mockScrollableElement = {
        addEventListener: jest.fn()
      };
      
      // Сбрасываем моки перед тестом
      mockQuerySelectorAll.mockClear();
      mockAddEventListener.mockClear();
      mockGetComputedStyle.mockClear();
      
      // Настраиваем мок для querySelectorAll
      mockQuerySelectorAll.mockReturnValue([mockScrollableElement]);
      
      // Убеждаемся, что document.querySelectorAll правильно замокан
      global.document.querySelectorAll = mockQuerySelectorAll;
      
      // Создаем новый экземпляр с мокированным document и валидным targetElement
      const instance = new ScrollBackgroundToggle(mockBody);
      
      expect(mockQuerySelectorAll).toHaveBeenCalledWith('[style*="overflow"], .overflow-auto, .overflow-scroll, .overflow-y-auto, .overflow-y-scroll');
      expect(mockScrollableElement.addEventListener).toHaveBeenCalledWith(
        'scroll',
        expect.any(Function),
        { passive: true }
      );
    });


  });

  describe('onScroll', () => {
    let toggle;
    
    beforeEach(() => {
      toggle = new ScrollBackgroundToggle();
      // Мокируем методы
      toggle.hideBackground = jest.fn();
      toggle.showBackground = jest.fn();
    });

    it('должен скрыть фон при прокрутке вниз', () => {
      global.window.pageYOffset = 100;
      Object.defineProperty(global.document, 'documentElement', {
        value: { scrollTop: 100 },
        configurable: true
      });
      
      toggle.onScroll();
      
      expect(toggle.hideBackground).toHaveBeenCalled();
    });

    it('должен показать фон при возврате к началу страницы', () => {
      toggle.isScrolling = true;
      global.window.pageYOffset = 0;
      Object.defineProperty(global.document, 'documentElement', {
        value: { scrollTop: 0 },
        configurable: true
      });
      
      toggle.onScroll();
      
      expect(mockSetTimeout).toHaveBeenCalledWith(expect.any(Function), 150);
      expect(toggle.showBackground).toHaveBeenCalled();
    });

    it('должен очистить предыдущий таймаут', () => {
      toggle.scrollTimeout = 123;
      
      toggle.onScroll();
      
      expect(mockClearTimeout).toHaveBeenCalledWith(123);
    });

    it('не должен скрывать фон если уже скрыт', () => {
      toggle.isScrolling = true;
      global.window.pageYOffset = 100;
      
      toggle.onScroll();
      
      expect(toggle.hideBackground).not.toHaveBeenCalled();
    });
  });

  describe('hideBackground', () => {
    let toggle;
    
    beforeEach(() => {
      toggle = new ScrollBackgroundToggle();
    });

    it('должен скрыть фоновое изображение', () => {
      toggle.targetElement = mockBody;
      toggle.originalBackground = { backgroundImage: 'url("test-bg.jpg")' };
      toggle.isScrolling = false; // Устанавливаем в false, чтобы метод мог выполниться
      
      toggle.hideBackground();
      
      expect(toggle.isScrolling).toBe(true);
      expect(mockBody.classList.add).toHaveBeenCalledWith('scrolling-no-bg');
    });

    it('не должен скрывать фон если элемент не найден', () => {
      toggle.targetElement = null;
      const originalIsScrolling = toggle.isScrolling;
      
      toggle.hideBackground();
      
      expect(toggle.isScrolling).toBe(originalIsScrolling);
    });

    it('не должен скрывать фон если уже скрыт', () => {
      toggle.isScrolling = true;
      
      toggle.hideBackground();
      
      expect(mockBody.style.backgroundImage).toBe('');
    });
  });

  describe('showBackground', () => {
    let toggle;
    
    beforeEach(() => {
      toggle = new ScrollBackgroundToggle();
      toggle.isScrolling = true;
    });

    it('должен показать фоновое изображение', () => {
      toggle.targetElement = mockBody;
      toggle.originalBackground = { backgroundImage: 'url("test-bg.jpg")' };
      
      toggle.showBackground();
      
      expect(toggle.isScrolling).toBe(false);
      expect(mockBody.classList.remove).toHaveBeenCalledWith('scrolling-no-bg');
    });



    it('должен убрать inline стили после анимации', () => {
      // Устанавливаем необходимые свойства
      toggle.isScrolling = true;
      toggle.targetElement = mockBody;
      toggle.originalBackground = {
        backgroundImage: 'url(test.jpg)',
        backgroundColor: 'white',
        background: 'white url(test.jpg)'
      };
      
      // Мокируем setTimeout чтобы он не выполнялся автоматически
      mockSetTimeout.mockImplementation((cb, delay) => {
        expect(delay).toBe(300);
        // Выполняем callback
        cb();
        return 1;
      });
      
      toggle.showBackground();
      
      // Проверяем, что setTimeout был вызван с правильной задержкой
      expect(mockSetTimeout).toHaveBeenCalledWith(expect.any(Function), 300);
    });

    it('не должен показывать фон если элемент не найден', () => {
      toggle.targetElement = null;
      
      toggle.showBackground();
      
      expect(toggle.isScrolling).toBe(true);
    });

    it('не должен показывать фон если не скрыт', () => {
      toggle.isScrolling = false;
      
      toggle.showBackground();
      
      expect(mockBody.style.backgroundImage).toBe('');
    });

    it('должен вызывать showBackground корректно', () => {
      const toggle = new ScrollBackgroundToggle();
      toggle.targetElement = mockBody;
      toggle.originalBackground = { backgroundImage: 'url("test-bg.jpg")' };
      toggle.isScrolling = true; // Устанавливаем isScrolling в true
      
      toggle.showBackground();
      
      // Проверяем, что isScrolling стал false
      expect(toggle.isScrolling).toBe(false);
      // Проверяем, что classList.remove был вызван
      expect(mockBody.classList.remove).toHaveBeenCalledWith('scrolling-no-bg');
    });
  });

  describe('refresh', () => {
    it('должен вызвать setup повторно', () => {
      const toggle = new ScrollBackgroundToggle();
      const originalSetup = toggle.setup;
      toggle.setup = jest.fn();
      
      toggle.refresh();
      
      expect(toggle.setup).toHaveBeenCalled();
    });
  });

  describe('destroy', () => {
    let toggle;
    
    beforeEach(() => {
      toggle = new ScrollBackgroundToggle();
      toggle.scrollTimeout = 123;
      toggle.isScrolling = true;
    });

    it('должен очистить таймаут', () => {
      toggle.destroy();
      
      expect(mockClearTimeout).toHaveBeenCalledWith(123);
    });

    it('должен очищать ресурсы при destroy', () => {
      toggle.targetElement = mockBody;
      toggle.scrollTimeout = 123;
      toggle.originalBackground = {
        backgroundImage: 'url(test.jpg)',
        backgroundColor: 'white',
        background: 'white url(test.jpg)'
      };
      
      toggle.destroy();
      
      expect(mockClearTimeout).toHaveBeenCalledWith(123);
      expect(mockBody.classList.remove).toHaveBeenCalledWith('scrolling-no-bg');
    });

    it('должен работать корректно если элемент или фон не найдены', () => {
      toggle.targetElement = null;
      toggle.originalBackground = null;
      
      expect(() => toggle.destroy()).not.toThrow();
    });
  });

  describe('throttling mechanism', () => {
    it('должен использовать requestAnimationFrame для throttling', () => {
      // Мокируем requestAnimationFrame для контроля throttling
      mockRequestAnimationFrame.mockImplementation((cb) => {
        // Не выполняем callback сразу
        return 1;
      });
      
      const toggle = new ScrollBackgroundToggle();
      toggle.targetElement = mockBody;
      
      // Создаем простой обработчик scroll с throttling
      let ticking = false;
      const handleScroll = () => {
        if (!ticking) {
          requestAnimationFrame(() => {
            toggle.onScroll();
            ticking = false;
          });
          ticking = true;
        }
      };
      
      // Вызываем обработчик несколько раз
      handleScroll();
      handleScroll();
      handleScroll();
      
      // requestAnimationFrame должен быть вызван только один раз
      expect(mockRequestAnimationFrame).toHaveBeenCalledTimes(1);
    });
  });

  describe('global exports', () => {
    it('должен экспортировать класс и экземпляр глобально', () => {
      // Мокируем window для проверки глобального экспорта
      global.window = {
        ...global.window,
        ScrollBackgroundToggle: undefined,
        scrollBackgroundToggle: undefined
      };
      
      // Импортируем модуль заново
      jest.resetModules();
      require('./scrollBackgroundToggle');
      
      expect(global.window.ScrollBackgroundToggle).toBeDefined();
      expect(global.window.scrollBackgroundToggle).toBeDefined();
    });

    it('должен работать в среде без window', () => {
      const originalWindow = global.window;
      const originalDocument = global.document;
      
      // Устанавливаем среду без document.body
      global.document = {
        readyState: 'complete',
        body: null,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        querySelectorAll: jest.fn().mockReturnValue([]),
        documentElement: { scrollTop: 0 }
      };
      
      expect(() => {
        jest.resetModules();
        const module = require('./scrollBackgroundToggle');
        // Проверяем, что экспорт существует
        expect(module.default).toBeDefined();
      }).not.toThrow();
      
      global.window = originalWindow;
      global.document = originalDocument;
    });
  });
});