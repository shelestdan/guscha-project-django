import { useState, useEffect, useRef, useCallback } from 'react';

// Универсальный хук: слушает прокрутку на window, document, documentElement,
// и опционально на переданном containerRef (если он прокручиваемый).
// Для диагностики добавлены логирующие обработчики wheel/touchmove — они помогут понять,
// где именно происходит прокрутка (внутренний контейнер или окно).
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
          console.log('[useScrollDirection] readScrollY -> container:', val);
          return val;
        }
        console.log('[useScrollDirection] readScrollY -> container NOT scrollable, fallback to document/window');
      }
    } catch (err) {
      console.log('[useScrollDirection] readScrollY -> error reading container, fallback to document/window', err);
    }

    const docEl = document.documentElement;
    const body = document.body;
    const winVal = (typeof window !== 'undefined' && window.pageYOffset) ? window.pageYOffset : 0;
    const docVal = docEl ? docEl.scrollTop : 0;
    const bodyVal = body ? body.scrollTop : 0;

    const resolved = Math.max(winVal || 0, docVal || 0, bodyVal || 0);
    console.log('[useScrollDirection] readScrollY -> window/doc/body resolved:', resolved, { winVal, docVal, bodyVal });
    return resolved;
  }, [containerRef]);

  useEffect(() => {
    const onScroll = () => {
      const scrollY = readScrollY();

      if (Math.abs(scrollY - lastScrollY.current) > 0) {
        console.log('[useScrollDirection] onScroll', { scrollY, lastScrollY: lastScrollY.current });
      }

      setScrollPosition(scrollY);

      if (scrollY > lastScrollY.current) {
        if (lastScrollY.current !== scrollY) {
          setScrollDirection('down');
          console.log('[useScrollDirection] direction -> down');
        }
      } else if (scrollY < lastScrollY.current) {
        if (lastScrollY.current !== scrollY) {
          setScrollDirection('up');
          console.log('[useScrollDirection] direction -> up');
        }
      }

      lastScrollY.current = scrollY;
    };

    const targets = [];

    if (typeof window !== 'undefined') {
      targets.push(window);
      console.log('[useScrollDirection] will attach listener to window');
    }
    if (typeof document !== 'undefined') {
      targets.push(document);
      console.log('[useScrollDirection] will attach listener to document');
      if (document.documentElement) {
        targets.push(document.documentElement);
        console.log('[useScrollDirection] will attach listener to document.documentElement');
      }
    }

    if (containerRef && containerRef.current) {
      try {
        const el = containerRef.current;
        if (el.scrollHeight > el.clientHeight) {
          targets.push(el);
          console.log('[useScrollDirection] will attach listener to provided container', el);
        } else {
          console.log('[useScrollDirection] provided container is not scrollable — not attaching listener');
        }
      } catch (err) {
        console.log('[useScrollDirection] error while checking provided container', err);
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
          console.log('[useScrollDirection] wheel -> attached debug scroll listener to', found);
        }
      } else {
        console.log('[useScrollDirection] wheel -> no scrollable ancestor found, target:', e.target);
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
      console.log('[useScrollDirection] removed scroll/wheel listeners');
    };
  }, [readScrollY, containerRef]);

  return { scrollDirection, scrollPosition, containerRef };
};

export default useScrollDirection;