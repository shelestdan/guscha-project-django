import { useState, useEffect, useRef } from 'react';

const useScrollPosition = () => {
  const [scrollPosition, setScrollPosition] = useState(0);
  const rafIdRef = useRef(null);
  const lastScrollRef = useRef(0);

  useEffect(() => {
    // Throttled scroll handler через RAF
    const handleScroll = () => {
      if (rafIdRef.current) return; // Уже запланирован update
      
      rafIdRef.current = requestAnimationFrame(() => {
        const currentScroll = window.pageYOffset;
        // Обновляем state только если значение изменилось
        if (currentScroll !== lastScrollRef.current) {
          lastScrollRef.current = currentScroll;
          setScrollPosition(currentScroll);
        }
        rafIdRef.current = null;
      });
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);

  return scrollPosition;
};

export default useScrollPosition; 