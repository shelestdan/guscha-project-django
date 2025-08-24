import { useState, useEffect, useRef, useCallback } from 'react';

// Оптимизированный хук: слушает прокрутку на window, document, documentElement,
// и опционально на переданном containerRef. Мгновенная инициализация для немедленной работы анимации.
const useScrollDirection = (containerRef = null) => {
  const [scrollDirection, setScrollDirection] = useState('up');
  const [scrollPosition, setScrollPosition] = useState(0);
  const lastScrollY = useRef(0);

  const readScrollY = useCallback(() => {
    try {
      if (containerRef && containerRef.current) {
        const el = containerRef.current;
        const isScrollable = el.scrollHeight > el.clientHeight;
        if (isScrollable) {
          const val = el.scrollTop;
          return val;
        }
      }
    } catch (err) {
      // Fallback to document/window on error
    }

    const docEl = document.documentElement;
    const body = document.body;
    const winVal = (typeof window !== 'undefined' && window.pageYOffset) ? window.pageYOffset : 0;
    const docVal = docEl ? docEl.scrollTop : 0;
    const bodyVal = body ? body.scrollTop : 0;

    const resolved = Math.max(winVal || 0, docVal || 0, bodyVal || 0);
    return resolved;
  }, [containerRef]);

  useEffect(() => {
    // Мгновенная инициализация состояния при монтировании
    const initialScrollY = readScrollY();
    setScrollPosition(initialScrollY);
    lastScrollY.current = initialScrollY;
    
    const onScroll = () => {
      const scrollY = readScrollY();



      setScrollPosition(scrollY);

      if (scrollY > lastScrollY.current) {
        if (lastScrollY.current !== scrollY) {
          setScrollDirection('down');
        }
      } else if (scrollY < lastScrollY.current) {
        if (lastScrollY.current !== scrollY) {
          setScrollDirection('up');
        }
      }

      lastScrollY.current = scrollY;
    };

    const targets = [];

    if (typeof window !== 'undefined') {
      targets.push(window);
    }
    if (typeof document !== 'undefined') {
      targets.push(document);
      if (document.documentElement) {
        targets.push(document.documentElement);
      }
    }

    if (containerRef && containerRef.current) {
      try {
        const el = containerRef.current;
        if (el.scrollHeight > el.clientHeight) {
          targets.push(el);
        }
      } catch (err) {
        // Error checking container
      }
    }

    // discovery set for dynamically found scrollable ancestors (via wheel)
    const discovered = new Set();

    const onWheelDetect = (e) => {
      // find nearest ancestor that is scrollable
      let el = e.target;
      let found = null;
      while (el && el !== document && el !== document.documentElement) {
        try {
          if (el.scrollHeight > el.clientHeight) {
            found = el;
            break;
          }
        } catch (err) {
          break;
        }
        el = el.parentElement;
      }

      if (found) {
        if (!discovered.has(found)) {
          discovered.add(found);
          found.addEventListener('scroll', onScroll, { passive: true });
        }
      }
    };

    targets.forEach((t) => t.addEventListener('scroll', onScroll, { passive: true }));

    // Listen to wheel/touchmove for diagnostics (to detect which element receives scroll events)
    document.addEventListener('wheel', onWheelDetect, { passive: true, capture: true });
    document.addEventListener('touchmove', onWheelDetect, { passive: true, capture: true });

    // Initialize once
    onScroll();

    return () => {
      targets.forEach((t) => t.removeEventListener('scroll', onScroll));
      discovered.forEach((el) => el.removeEventListener('scroll', onScroll));
      document.removeEventListener('wheel', onWheelDetect, { capture: true });
      document.removeEventListener('touchmove', onWheelDetect, { capture: true });
    };
  }, [readScrollY, containerRef]);

  return { scrollDirection, scrollPosition, containerRef };
};

export default useScrollDirection;