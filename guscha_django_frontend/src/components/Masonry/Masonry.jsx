import React, { useEffect, useLayoutEffect, useMemo, useRef, useState, useCallback } from 'react';
import { gsap } from 'gsap';
import './Masonry.css';

const useMedia = (queries, values, defaultValue) => {
  const get = useCallback(() => 
    values[queries.findIndex(q => matchMedia(q).matches)] ?? defaultValue,
    [queries, values, defaultValue]
  );
  const [value, setValue] = useState(get);

  useEffect(() => {
    const handler = () => setValue(get());
    const mediaQueries = queries.map(q => matchMedia(q));
    
    mediaQueries.forEach(mq => mq.addEventListener('change', handler));
    return () => mediaQueries.forEach(mq => mq.removeEventListener('change', handler));
  }, [queries, get]);

  return value;
};

const useMeasure = () => {
  const ref = useRef(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useLayoutEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ width, height });
    });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);

  return [ref, size];
};

const preloadImages = async (urls) => {
  await Promise.all(urls.map(src =>
    new Promise(resolve => {
      const img = new Image();
      img.src = src;
      img.onload = img.onerror = () => resolve();
    })
  ));
};

const Masonry = ({
  items,
  ease = 'power3.out',
  duration = 0.6,
  stagger = 0.05,
  animateFrom = 'bottom',
  scaleOnHover = true,
  hoverScale = 0.95,
  blurToFocus = true,
  colorShiftOnHover = false,
  onItemClick
}) => {
  const columns = useMedia(
    ['(min-width:1500px)', '(min-width:1000px)', '(min-width:600px)', '(min-width:400px)'],
    [5, 4, 3, 2],
    1
  );

  const [containerRef, { width }] = useMeasure();
  const [imagesReady, setImagesReady] = useState(false);
  const hasMounted = useRef(false);
  const animationsRef = useRef([]);

  const getInitialPosition = useCallback((item) => {
    const containerRect = containerRef.current?.getBoundingClientRect();
    if (!containerRect) return { x: item.x, y: item.y };

    let direction = animateFrom;
    if (animateFrom === 'random') {
      const dirs = ['top', 'bottom', 'left', 'right'];
      direction = dirs[Math.floor(Math.random() * dirs.length)];
    }

    switch (direction) {
      case 'top':
        return { x: item.x, y: -200 };
      case 'bottom':
        return { x: item.x, y: window.innerHeight + 200 };
      case 'left':
        return { x: -200, y: item.y };
      case 'right':
        return { x: window.innerWidth + 200, y: item.y };
      case 'center':
        return {
          x: containerRect.width / 2 - item.w / 2,
          y: containerRect.height / 2 - item.h / 2
        };
      default:
        return { x: item.x, y: item.y + 100 };
    }
  }, [animateFrom, containerRef]);

  // Очистка GSAP анимаций при размонтировании
  useEffect(() => {
    return () => {
      animationsRef.current.forEach(tween => tween?.kill());
      animationsRef.current = [];
    };
  }, []);

  useEffect(() => {
    // Убиваем предыдущие анимации при смене items
    animationsRef.current.forEach(tween => tween?.kill());
    animationsRef.current = [];
    
    hasMounted.current = false;
    setImagesReady(false);
    
    let isCancelled = false;
    preloadImages(items.map(i => i.img)).then(() => {
      if (!isCancelled) setImagesReady(true);
    });
    
    return () => { isCancelled = true; };
  }, [items]);

  const grid = useMemo(() => {
    if (!width) return [];
    const colHeights = new Array(columns).fill(0);
    const gap = 16;
    const totalGaps = (columns - 1) * gap;
    const columnWidth = (width - totalGaps) / columns;

    return items.map(child => {
      const col = colHeights.indexOf(Math.min(...colHeights));
      const x = col * (columnWidth + gap);
      const height = child.height / 2;
      const y = colHeights[col];
      colHeights[col] += height + gap;
      return { ...child, x, y, w: columnWidth, h: height };
    });
  }, [columns, items, width]);

  const containerHeight = useMemo(() => {
    if (grid.length === 0) return 0;
    return Math.max(...grid.map(item => item.y + item.h)) + 16;
  }, [grid]);

  useLayoutEffect(() => {
    if (!imagesReady || grid.length === 0) return;

    // Очищаем предыдущие анимации
    animationsRef.current.forEach(tween => tween?.kill());
    animationsRef.current = [];

    grid.forEach((item, index) => {
      const selector = `[data-masonry-key="${item.id}"]`;
      const animProps = { x: item.x, y: item.y, width: item.w, height: item.h };

      if (!hasMounted.current) {
        const start = getInitialPosition(item);
        const tween = gsap.fromTo(selector,
          {
            opacity: 0,
            x: start.x,
            y: start.y,
            width: item.w,
            height: item.h,
            ...(blurToFocus && { filter: 'blur(10px)' })
          },
          {
            opacity: 1,
            ...animProps,
            ...(blurToFocus && { filter: 'blur(0px)' }),
            duration: 0.8,
            ease: 'power3.out',
            delay: index * stagger
          }
        );
        animationsRef.current.push(tween);
      } else {
        const tween = gsap.to(selector, {
          ...animProps,
          duration,
          ease,
          overwrite: 'auto'
        });
        animationsRef.current.push(tween);
      }
    });

    hasMounted.current = true;
  }, [grid, imagesReady, stagger, blurToFocus, duration, ease, getInitialPosition]);

  const handleMouseEnter = useCallback((id) => {
    if (scaleOnHover) {
      gsap.to(`[data-masonry-key="${id}"]`, {
        scale: hoverScale,
        duration: 0.3,
        ease: 'power2.out'
      });
    }
    if (colorShiftOnHover) {
      const overlay = document.querySelector(`[data-masonry-key="${id}"] .masonry-color-overlay`);
      if (overlay) gsap.to(overlay, { opacity: 0.3, duration: 0.3 });
    }
  }, [scaleOnHover, hoverScale, colorShiftOnHover]);

  const handleMouseLeave = useCallback((id) => {
    if (scaleOnHover) {
      gsap.to(`[data-masonry-key="${id}"]`, {
        scale: 1,
        duration: 0.3,
        ease: 'power2.out'
      });
    }
    if (colorShiftOnHover) {
      const overlay = document.querySelector(`[data-masonry-key="${id}"] .masonry-color-overlay`);
      if (overlay) gsap.to(overlay, { opacity: 0, duration: 0.3 });
    }
  }, [scaleOnHover, colorShiftOnHover]);

  const handleClick = useCallback((item) => {
    if (onItemClick) {
      onItemClick(item);
    } else if (item.url) {
      window.open(item.url, '_blank', 'noopener');
    }
  }, [onItemClick]);

  return (
    <div 
      ref={containerRef} 
      className="masonry-container"
      style={{ height: containerHeight > 0 ? containerHeight : 'auto' }}
    >
      {grid.map(item => (
        <div
          key={item.id}
          data-masonry-key={item.id}
          className="masonry-item"
          style={{ willChange: 'transform, width, height, opacity' }}
          onClick={() => handleClick(item)}
          onMouseEnter={() => handleMouseEnter(item.id)}
          onMouseLeave={() => handleMouseLeave(item.id)}
        >
          <div
            className="masonry-item-inner"
            style={{ backgroundImage: `url(${item.img})` }}
          >
            {colorShiftOnHover && (
              <div className="masonry-color-overlay" />
            )}
            {item.caption && (
              <div className="masonry-caption">{item.caption}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default React.memo(Masonry);
