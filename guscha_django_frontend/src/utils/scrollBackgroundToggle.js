/**
 * Скрипт для управления фоновым изображением при прокрутке
 * Отключает фоновое изображение при прокрутке, чтобы предотвратить
 * его просвечивание через прозрачный скроллбар
 */

class ScrollBackgroundToggle {
  constructor(targetElement = null) {
    this.targetElement = targetElement || (typeof document !== 'undefined' ? document.body : null);
    this.originalBackgroundColor = null;
    this.isEnabled = true;
    this.isScrolling = false;
    this.scrollTimeout = null;
    this.eventListeners = [];
    
    this.setup();
  }

  init() {
    // Ждем загрузки DOM
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    // Используем переданный targetElement или document.body по умолчанию
    if (!this.targetElement && typeof document !== 'undefined') {
      this.targetElement = document.body;
    }
    
    if (!this.targetElement) {
      return;
    }

    // Сохраняем оригинальный фон
    if (typeof window !== 'undefined' && window.getComputedStyle && this.targetElement && this.targetElement.nodeType === 1) {
      try {
        const computedStyle = window.getComputedStyle(this.targetElement);
        this.originalBackground = {
          backgroundImage: computedStyle.backgroundImage,
          backgroundColor: computedStyle.backgroundColor,
          background: computedStyle.background
        };
      } catch (error) {
        this.originalBackground = {
          backgroundImage: '',
          backgroundColor: '',
          background: ''
        };
      }
    } else {
      this.originalBackground = {
        backgroundImage: '',
        backgroundColor: '',
        background: ''
      };
    }

    // Добавляем обработчики событий
    this.addEventListeners();
  }

  addEventListeners() {
    const hasWindow = typeof window !== 'undefined' && window;
    const hasDocument = typeof document !== 'undefined' && document && document.querySelectorAll;
    
    if (hasWindow) {
      window.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
    }
    
    if (hasDocument) {
      document.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
    }
    
    // Добавляем обработчики для элементов с overflow
    if (typeof document !== 'undefined' && document.querySelectorAll) {
      const scrollableElements = document.querySelectorAll('[style*="overflow"], .overflow-auto, .overflow-scroll, .overflow-y-auto, .overflow-y-scroll');
      scrollableElements.forEach(element => {
        if (element && element.addEventListener) {
          element.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
        }
      });
    }
  }

  onScroll() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Если начали прокрутку и фон еще не скрыт
    if (scrollTop > 0 && !this.isScrolling) {
      this.hideBackground();
    }
    
    // Очищаем предыдущий таймаут
    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout);
    }
    
    // Устанавливаем таймаут для восстановления фона после окончания прокрутки
    this.scrollTimeout = setTimeout(() => {
      if (scrollTop === 0) {
        this.showBackground();
      }
    }, 150); // Задержка 150мс после окончания прокрутки
  }

  hideBackground() {
    if (!this.targetElement || this.isScrolling) return;
    
    this.isScrolling = true;
    
    // Плавно скрываем фоновое изображение
    this.targetElement.style.transition = 'background-image 0.3s ease-out';
    this.targetElement.style.backgroundImage = 'none';
    
    // Добавляем класс для дополнительной стилизации если нужно
    this.targetElement.classList.add('scrolling-no-bg');
  }

  showBackground() {
    if (!this.targetElement || !this.isScrolling) return;
    
    this.isScrolling = false;
    
    // Восстанавливаем оригинальный фон
    this.targetElement.style.transition = 'background-image 0.3s ease-in';
    this.targetElement.style.backgroundImage = this.originalBackground.backgroundImage;
    
    // Убираем класс
    this.targetElement.classList.remove('scrolling-no-bg');
    
    // Убираем inline стили после завершения анимации
    setTimeout(() => {
      if (!this.isScrolling) {
        this.targetElement.style.transition = '';
      }
    }, 300);
  }

  // Метод для принудительного обновления
  refresh() {
    this.setup();
  }

  // Метод для отключения функционала
  destroy() {
    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout);
    }
    
    // Восстанавливаем оригинальный фон
    if (this.targetElement && this.originalBackground) {
      this.targetElement.style.backgroundImage = this.originalBackground.backgroundImage;
      this.targetElement.classList.remove('scrolling-no-bg');
      this.targetElement.style.transition = '';
    }
  }
}

// Создаем и экспортируем экземпляр только в браузерной среде
let scrollBackgroundToggle;
if (typeof window !== 'undefined' && typeof document !== 'undefined' && document.body) {
  try {
    scrollBackgroundToggle = new ScrollBackgroundToggle();
  } catch (error) {
    // В случае ошибки создаем заглушку
    scrollBackgroundToggle = {
      init: () => {},
      destroy: () => {},
      toggle: () => {},
      enable: () => {},
      disable: () => {}
    };
  }
} else {
  // В тестовой среде или среде без DOM создаем заглушку
  scrollBackgroundToggle = {
    init: () => {},
    destroy: () => {},
    toggle: () => {},
    enable: () => {},
    disable: () => {}
  };
}

// Экспортируем класс и экземпляр
export { ScrollBackgroundToggle };
export default scrollBackgroundToggle;

// Также делаем доступным глобально для совместимости
if (typeof window !== 'undefined') {
  window.ScrollBackgroundToggle = ScrollBackgroundToggle;
  window.scrollBackgroundToggle = scrollBackgroundToggle;
}