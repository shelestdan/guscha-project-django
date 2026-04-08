import { useState, useEffect, useRef, useCallback } from 'react';

// Оптимизированный хук для определения направления скролла
// Использует RAF throttling для предотвращения лишних ре-рендеров
const useScrollDirection = (containerRef = null) => {
  const [scrollDirection, setScrollDirection] = useState('up');
  const [scrollPosition, setScrollPosition] = useState(0);
  const lastScrollY = useRef(0);
  const rafIdRef = useRef(null);
  const ticking = useRef(false);

  const readScrollY = useCallback(() => {
    try {
      if (containerRef && containerRef.current) {
        const el = containerRef.current;
        const isScrollable = el.scrollHeight > el.clientHeight;
        if (isScrollable) {
          return el.scrollTop;
        }
      }
    } catch (err) {
      // Fallback to window on error
    }

    return window.pageYOffset || document.documentElement.scrollTop || 0;
  }, [containerRef]);

  useEffect(() => {
    // Мгновенная инициализация состояния при монтировании
    const initialScrollY = readScrollY();
    setScrollPosition(initialScrollY);
    lastScrollY.current = initialScrollY;
    
    // Throttled scroll handler через RAF
    const updateScrollState = () => {
      const scrollY = readScrollY();
      
      // Обновляем только если значение изменилось
      if (scrollY !== lastScrollY.current) {
        setScrollPosition(scrollY);
        
        if (scrollY > lastScrollY.current) {
          setScrollDirection('down');
        } else {
          setScrollDirection('up');
        }
        
        lastScrollY.current = scrollY;
      }
      
      ticking.current = false;
    };
    
    const onScroll = () => {
      if (!ticking.current) {
        rafIdRef.current = requestAnimationFrame(updateScrollState);
        ticking.current = true;
      }
    };

    // Слушаем только window - это покрывает большинство случаев
    window.addEventListener('scroll', onScroll, { passive: true });
    
    // Опционально слушаем containerRef если передан
    const container = containerRef?.current;
    if (container && container.scrollHeight > container.clientHeight) {
      container.addEventListener('scroll', onScroll, { passive: true });
    }

    return () => {
      window.removeEventListener('scroll', onScroll);
      if (container) {
        container.removeEventListener('scroll', onScroll);
      }
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, [readScrollY, containerRef]);

  return { scrollDirection, scrollPosition, containerRef };
};

export default useScrollDirection;