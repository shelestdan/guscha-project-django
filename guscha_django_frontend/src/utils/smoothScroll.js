import { useEffect, useRef } from 'react';
import { useLenis } from 'lenis/react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

/**
 * Хук для синхронизации Lenis с GSAP ScrollTrigger
 * Используется внутри ReactLenis
 */
export const useLenisScrollTrigger = () => {
  const lenis = useLenis();
  const updateRef = useRef(null);

  useEffect(() => {
    if (!lenis) return;

    // Функция обновления ScrollTrigger
    const scrollUpdate = () => ScrollTrigger.update();
    
    // Синхронизация Lenis с ScrollTrigger
    lenis.on('scroll', scrollUpdate);

    // Подключаем к GSAP ticker (только если ещё не добавлен)
    if (!updateRef.current) {
      updateRef.current = (time) => {
        lenis.raf(time * 1000);
      };
      gsap.ticker.add(updateRef.current);
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
    };
  }, [lenis]);

  return lenis;
};

// Пустые функции для обратной совместимости
export const initSmoothScroll = () => {};
export const destroySmoothScroll = () => {};
