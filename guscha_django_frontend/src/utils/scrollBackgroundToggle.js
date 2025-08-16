/**
 * Скрипт для управления фоновым изображением при прокрутке
 * Отключает фоновое изображение при прокрутке, чтобы предотвратить
 * его просвечивание через прозрачный скроллбар
 */

class ScrollBackgroundToggle {
  constructor() {
    this.isScrolling = false;
    this.scrollTimeout = null;
    this.originalBackground = null;
    this.targetElement = null;
    
    this.init();
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
    // Находим элемент с фоновым изображением
    this.targetElement = document.body;
    
    if (!this.targetElement) {
      console.warn('ScrollBackgroundToggle: Target element not found');
      return;
    }

    // Сохраняем оригинальный фон
    const computedStyle = window.getComputedStyle(this.targetElement);
    this.originalBackground = {
      backgroundImage: computedStyle.backgroundImage,
      backgroundColor: computedStyle.backgroundColor,
      background: computedStyle.background
    };

    // Добавляем обработчики событий
    this.addEventListeners();
  }

  addEventListeners() {
    // Обработчик прокрутки с throttling для производительности
    let ticking = false;
    
    const handleScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          this.onScroll();
          ticking = false;
        });
        ticking = true;
      }
    };

    // Слушаем прокрутку на window и document
    window.addEventListener('scroll', handleScroll, { passive: true });
    document.addEventListener('scroll', handleScroll, { passive: true });
    
    // Также слушаем прокрутку на всех элементах с overflow
    const scrollableElements = document.querySelectorAll('[style*="overflow"], .overflow-auto, .overflow-scroll, .overflow-y-auto, .overflow-y-scroll');
    scrollableElements.forEach(element => {
      element.addEventListener('scroll', handleScroll, { passive: true });
    });
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

// Создаем и экспортируем экземпляр
const scrollBackgroundToggle = new ScrollBackgroundToggle();

// Экспортируем для использования в других модулях
export default scrollBackgroundToggle;

// Также делаем доступным глобально для совместимости
if (typeof window !== 'undefined') {
  window.ScrollBackgroundToggle = ScrollBackgroundToggle;
  window.scrollBackgroundToggle = scrollBackgroundToggle;
}