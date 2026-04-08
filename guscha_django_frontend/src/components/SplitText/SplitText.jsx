import { useMemo, useRef, useEffect, useState, useCallback } from 'react';
import { gsap } from 'gsap';
import './SplitText.css';

const SplitText = ({
  text = '',
  className = '',
  delay = 0,
  duration = 0.05,
  ease = 'power3.out',
  splitBy = 'char',
  animateFrom = 'bottom',
  stagger = 0.02,
  animationKey = null
}) => {
  const containerRef = useRef(null);
  const [isVisible, setIsVisible] = useState(false);
  const animationRef = useRef(null);

  const elements = useMemo(() => {
    if (splitBy === 'word') {
      return text.split(' ').map((word, i) => ({ content: word, key: `word-${i}` }));
    }
    if (splitBy === 'line') {
      return text.split('\n').map((line, i) => ({ content: line, key: `line-${i}` }));
    }
    return text.split('').map((char, i) => ({ 
      content: char === ' ' ? '\u00A0' : char, 
      key: `char-${i}` 
    }));
  }, [text, splitBy]);

  // Очистка GSAP при размонтировании
  useEffect(() => {
    return () => {
      animationRef.current?.kill();
    };
  }, []);

  // Сброс анимации при изменении текста или animationKey
  useEffect(() => {
    animationRef.current?.kill();
    setIsVisible(false);
    const timer = setTimeout(() => setIsVisible(true), 50);
    return () => clearTimeout(timer);
  }, [text, animationKey]);

  const getFromVars = useCallback(() => {
    switch (animateFrom) {
      case 'top':
        return { y: -30, opacity: 0 };
      case 'left':
        return { x: -20, opacity: 0 };
      case 'right':
        return { x: 20, opacity: 0 };
      case 'fade':
        return { opacity: 0 };
      case 'bottom':
      default:
        return { y: 30, opacity: 0 };
    }
  }, [animateFrom]);

  useEffect(() => {
    if (!isVisible || !containerRef.current) return;

    const chars = containerRef.current.querySelectorAll('.split-text-element');
    
    animationRef.current = gsap.fromTo(chars, 
      getFromVars(),
      {
        y: 0,
        x: 0,
        opacity: 1,
        duration,
        ease,
        stagger,
        delay
      }
    );
  }, [isVisible, getFromVars, duration, ease, stagger, delay]);

  return (
    <span ref={containerRef} className={`split-text-container ${className}`}>
      {elements.map(({ content, key }) => (
        <span key={key} className="split-text-element">
          {content}
          {splitBy === 'word' && ' '}
        </span>
      ))}
    </span>
  );
};

export default SplitText;
