import { useEffect, useRef, useCallback } from 'react';
import { useLenis } from 'lenis/react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

/**
 * Хук для синхронизации Lenis с GSAP ScrollTrigger
 * Используется внутри ReactLenis
 * 
 * ОПТИМИЗАЦИЯ: ScrollTrigger.update() теперь вызывается через RAF
 * вместо каждого scroll event для предотвращения торможения
 */
export const useLenisScrollTrigger = () => {
  const lenis = useLenis();
  const updateRef = useRef(null);
  const scrollUpdateScheduledRef = useRef(false);

  useEffect(() => {
    if (!lenis) return;

    // Оптимизированная функция обновления ScrollTrigger через RAF
    // Предотвращает множественные вызовы update() за один кадр
    const scrollUpdate = () => {
      if (!scrollUpdateScheduledRef.current) {
        scrollUpdateScheduledRef.current = true;
        requestAnimationFrame(() => {
          ScrollTrigger.update();
          scrollUpdateScheduledRef.current = false;
        });
      }
    };
    
    // Синхронизация Lenis с ScrollTrigger
    lenis.on('scroll', scrollUpdate);

    // Подключаем к GSAP ticker (только если ещё не добавлен)
    if (!updateRef.current) {
      updateRef.current = (time) => {
        lenis.raf(time * 1000);
      };
      gsap.ticker.add(updateRef.current);
      // Отключаем lag smoothing для более плавной анимации
      gsap.ticker.lagSmoothing(0);
    }

    return () => {
      // Удаляем listener со скролла
      lenis.off('scroll', scrollUpdate);
      
      // Удаляем из ticker
      if (updateRef.current) {
        gsap.ticker.remove(updateRef.current);
        updateRef.current = null;
      }
      
      // Сбрасываем флаг
      scrollUpdateScheduledRef.current = false;
    };
  }, [lenis]);

  return lenis;
};

// Пустые функции для обратной совместимости
export const initSmoothScroll = () => {};
export const destroySmoothScroll = () => {};
