import { useState, useEffect, useRef, useCallback } from 'react';

// Универсальный хук: если передан ref — слушает scroll на контейнере, иначе на window
const useScrollDirection = (containerRef = null) => {
  const [scrollDirection, setScrollDirection] = useState('up');
  const [scrollPosition, setScrollPosition] = useState(0);
  const lastScrollY = useRef(0);

  // Получить текущий scrollY
  const getScrollY = useCallback(() => {
    if (containerRef && containerRef.current) {
      return containerRef.current.scrollTop;
    }
    return window.pageYOffset;
  }, [containerRef]);

  useEffect(() => {
    const onScroll = () => {
      const scrollY = getScrollY();
      setScrollPosition(scrollY);
      
      // Вычисляем direction ДО обновления lastScrollY
      let newDirection = scrollDirection;
      if (scrollY > lastScrollY.current) {
        newDirection = 'down';
        setScrollDirection('down');
      } else if (scrollY < lastScrollY.current) {
        newDirection = 'up';
        setScrollDirection('up');
      }
      
      
      lastScrollY.current = scrollY;
    };
    const target = containerRef && containerRef.current ? containerRef.current : window;
    target.addEventListener('scroll', onScroll);
    return () => target.removeEventListener('scroll', onScroll);
  }, [getScrollY, containerRef]);

  return { scrollDirection, scrollPosition, containerRef };
};

export default useScrollDirection; 