import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Хук для поведенческого анализа пользователя
 * Отслеживает паттерны поведения для выявления ботов
 */
export const useBehavioralAnalysis = (options = {}) => {
  const {
    trackMouse = true,
    trackKeyboard = true,
    trackScroll = true,
    trackFocus = true,
    sessionDuration = 300000, // 5 минут
    minInteractions = 5
  } = options;

  const [behaviorData, setBehaviorData] = useState({
    mouseMovements: [],
    keystrokes: [],
    scrollEvents: [],
    focusEvents: [],
    clickEvents: [],
    sessionStart: Date.now(),
    totalInteractions: 0,
    suspiciousPatterns: []
  });

  const [analysis, setAnalysis] = useState({
    isHuman: null,
    confidence: 0,
    riskScore: 0,
    patterns: []
  });

  const mouseDataRef = useRef([]);
  const keystrokeDataRef = useRef([]);
  const scrollDataRef = useRef([]);
  const focusDataRef = useRef([]);
  const clickDataRef = useRef([]);
  const lastMouseMoveRef = useRef(0);
  const lastKeystrokeRef = useRef(0);

  // Отслеживание движений мыши
  const handleMouseMove = useCallback((event) => {
    if (!trackMouse) return;
    
    const now = Date.now();
    const timeDiff = now - lastMouseMoveRef.current;
    
    if (timeDiff > 50) { // Throttle to avoid too much data
      const mouseData = {
        x: event.clientX,
        y: event.clientY,
        timestamp: now,
        timeDiff,
        velocity: timeDiff > 0 ? Math.sqrt(
          Math.pow(event.movementX || 0, 2) + Math.pow(event.movementY || 0, 2)
        ) / timeDiff : 0
      };
      
      mouseDataRef.current.push(mouseData);
      
      // Ограничиваем размер массива
      if (mouseDataRef.current.length > 1000) {
        mouseDataRef.current = mouseDataRef.current.slice(-500);
      }
      
      lastMouseMoveRef.current = now;
    }
  }, [trackMouse]);

  // Отслеживание кликов мыши
  const handleMouseClick = useCallback((event) => {
    const clickData = {
      x: event.clientX,
      y: event.clientY,
      button: event.button,
      timestamp: Date.now(),
      target: event.target.tagName,
      targetId: event.target.id,
      targetClass: event.target.className
    };
    
    clickDataRef.current.push(clickData);
    
    if (clickDataRef.current.length > 100) {
      clickDataRef.current = clickDataRef.current.slice(-50);
    }
  }, []);

  // Отслеживание нажатий клавиш
  const handleKeyDown = useCallback((event) => {
    if (!trackKeyboard) return;
    
    const now = Date.now();
    const timeDiff = now - lastKeystrokeRef.current;
    
    const keystrokeData = {
      key: event.key,
      code: event.code,
      timestamp: now,
      timeDiff,
      ctrlKey: event.ctrlKey,
      altKey: event.altKey,
      shiftKey: event.shiftKey,
      metaKey: event.metaKey
    };
    
    keystrokeDataRef.current.push(keystrokeData);
    
    if (keystrokeDataRef.current.length > 500) {
      keystrokeDataRef.current = keystrokeDataRef.current.slice(-250);
    }
    
    lastKeystrokeRef.current = now;
  }, [trackKeyboard]);

  // Отслеживание прокрутки
  const handleScroll = useCallback(() => {
    if (!trackScroll) return;
    
    const scrollData = {
      scrollY: window.scrollY,
      scrollX: window.scrollX,
      timestamp: Date.now()
    };
    
    scrollDataRef.current.push(scrollData);
    
    if (scrollDataRef.current.length > 200) {
      scrollDataRef.current = scrollDataRef.current.slice(-100);
    }
  }, [trackScroll]);

  // Отслеживание фокуса
  const handleFocus = useCallback((event) => {
    if (!trackFocus) return;
    
    const focusData = {
      type: event.type, // focus или blur
      target: event.target.tagName,
      targetId: event.target.id,
      timestamp: Date.now()
    };
    
    focusDataRef.current.push(focusData);
    
    if (focusDataRef.current.length > 100) {
      focusDataRef.current = focusDataRef.current.slice(-50);
    }
  }, [trackFocus]);

  // Анализ паттернов движения мыши
  const analyzeMousePatterns = useCallback(() => {
    const movements = mouseDataRef.current;
    if (movements.length < 10) return [];
    
    const patterns = [];
    
    // Проверка на слишком прямые линии (признак бота)
    let straightLineCount = 0;
    for (let i = 2; i < movements.length; i++) {
      const prev2 = movements[i - 2];
      const prev1 = movements[i - 1];
      const curr = movements[i];
      
      const angle1 = Math.atan2(prev1.y - prev2.y, prev1.x - prev2.x);
      const angle2 = Math.atan2(curr.y - prev1.y, curr.x - prev1.x);
      const angleDiff = Math.abs(angle1 - angle2);
      
      if (angleDiff < 0.1) { // Очень прямая линия
        straightLineCount++;
      }
    }
    
    if (straightLineCount / movements.length > 0.7) {
      patterns.push({
        type: 'straight_line_movement',
        severity: 'high',
        description: 'Слишком много прямолинейных движений мыши'
      });
    }
    
    // Проверка на постоянную скорость (признак бота)
    const velocities = movements.map(m => m.velocity).filter(v => v > 0);
    if (velocities.length > 5) {
      const avgVelocity = velocities.reduce((a, b) => a + b, 0) / velocities.length;
      const variance = velocities.reduce((acc, v) => acc + Math.pow(v - avgVelocity, 2), 0) / velocities.length;
      const stdDev = Math.sqrt(variance);
      
      if (stdDev / avgVelocity < 0.3) { // Низкая вариативность скорости
        patterns.push({
          type: 'constant_velocity',
          severity: 'medium',
          description: 'Постоянная скорость движения мыши'
        });
      }
    }
    
    return patterns;
  }, []);

  // Анализ паттернов клавиатуры
  const analyzeKeystrokePatterns = useCallback(() => {
    const keystrokes = keystrokeDataRef.current;
    if (keystrokes.length < 5) return [];
    
    const patterns = [];
    
    // Проверка на слишком регулярные интервалы между нажатиями
    const intervals = [];
    for (let i = 1; i < keystrokes.length; i++) {
      intervals.push(keystrokes[i].timeDiff);
    }
    
    if (intervals.length > 3) {
      const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
      const variance = intervals.reduce((acc, interval) => acc + Math.pow(interval - avgInterval, 2), 0) / intervals.length;
      const stdDev = Math.sqrt(variance);
      
      if (stdDev / avgInterval < 0.2) { // Очень регулярные интервалы
        patterns.push({
          type: 'regular_keystroke_timing',
          severity: 'high',
          description: 'Слишком регулярные интервалы между нажатиями клавиш'
        });
      }
    }
    
    // Проверка на слишком быстрый ввод
    const fastKeystrokes = intervals.filter(interval => interval < 50).length;
    if (fastKeystrokes / intervals.length > 0.8) {
      patterns.push({
        type: 'too_fast_typing',
        severity: 'medium',
        description: 'Слишком быстрый ввод текста'
      });
    }
    
    return patterns;
  }, []);

  // Анализ общих паттернов поведения
  const analyzeGeneralPatterns = useCallback(() => {
    const patterns = [];
    const now = Date.now();
    const sessionDurationMs = now - behaviorData.sessionStart;
    
    // Проверка на отсутствие взаимодействий
    const totalInteractions = mouseDataRef.current.length + keystrokeDataRef.current.length + 
                             clickDataRef.current.length + scrollDataRef.current.length;
    
    if (sessionDurationMs > 30000 && totalInteractions < minInteractions) {
      patterns.push({
        type: 'low_interaction',
        severity: 'medium',
        description: 'Мало взаимодействий за время сессии'
      });
    }
    
    // Проверка на отсутствие движений мыши при наличии кликов
    if (clickDataRef.current.length > 0 && mouseDataRef.current.length === 0) {
      patterns.push({
        type: 'clicks_without_movement',
        severity: 'high',
        description: 'Клики без движений мыши'
      });
    }
    
    return patterns;
  }, [behaviorData.sessionStart, minInteractions]);

  // Основная функция анализа
  const performAnalysis = useCallback(() => {
    const mousePatterns = analyzeMousePatterns();
    const keystrokePatterns = analyzeKeystrokePatterns();
    const generalPatterns = analyzeGeneralPatterns();
    
    const allPatterns = [...mousePatterns, ...keystrokePatterns, ...generalPatterns];
    
    // Расчет риск-скора
    let riskScore = 0;
    allPatterns.forEach(pattern => {
      switch (pattern.severity) {
        case 'high':
          riskScore += 30;
          break;
        case 'medium':
          riskScore += 15;
          break;
        case 'low':
          riskScore += 5;
          break;
        default:
          break;
      }
    });
    
    riskScore = Math.min(100, riskScore);
    
    // Определение человечности
    const confidence = Math.max(0, 100 - riskScore);
    const isHuman = riskScore < 50;
    
    setAnalysis({
      isHuman,
      confidence,
      riskScore,
      patterns: allPatterns
    });
    
    return {
      isHuman,
      confidence,
      riskScore,
      patterns: allPatterns,
      totalInteractions: mouseDataRef.current.length + keystrokeDataRef.current.length + 
                        clickDataRef.current.length + scrollDataRef.current.length
    };
  }, [analyzeMousePatterns, analyzeKeystrokePatterns, analyzeGeneralPatterns]);

  // Получение сводки поведенческих данных
  const getBehaviorSummary = useCallback(() => {
    return {
      mouseMovements: mouseDataRef.current.length,
      keystrokes: keystrokeDataRef.current.length,
      clicks: clickDataRef.current.length,
      scrollEvents: scrollDataRef.current.length,
      focusEvents: focusDataRef.current.length,
      sessionDuration: Date.now() - behaviorData.sessionStart,
      analysis: analysis
    };
  }, [behaviorData.sessionStart, analysis]);

  // Установка обработчиков событий
  useEffect(() => {
    if (trackMouse) {
      document.addEventListener('mousemove', handleMouseMove, { passive: true });
      document.addEventListener('click', handleMouseClick, { passive: true });
    }
    
    if (trackKeyboard) {
      document.addEventListener('keydown', handleKeyDown, { passive: true });
    }
    
    if (trackScroll) {
      window.addEventListener('scroll', handleScroll, { passive: true });
    }
    
    if (trackFocus) {
      document.addEventListener('focus', handleFocus, true);
      document.addEventListener('blur', handleFocus, true);
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('click', handleMouseClick);
      document.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('scroll', handleScroll);
      document.removeEventListener('focus', handleFocus, true);
      document.removeEventListener('blur', handleFocus, true);
    };
  }, [trackMouse, trackKeyboard, trackScroll, trackFocus, handleMouseMove, handleMouseClick, handleKeyDown, handleScroll, handleFocus]);

  // Периодический анализ
  useEffect(() => {
    const interval = setInterval(() => {
      performAnalysis();
    }, 10000); // Анализ каждые 10 секунд
    
    return () => clearInterval(interval);
  }, [performAnalysis]);

  return {
    analysis,
    getBehaviorSummary,
    performAnalysis,
    reset: () => {
      mouseDataRef.current = [];
      keystrokeDataRef.current = [];
      scrollDataRef.current = [];
      focusDataRef.current = [];
      clickDataRef.current = [];
      setBehaviorData(prev => ({
        ...prev,
        sessionStart: Date.now(),
        totalInteractions: 0,
        suspiciousPatterns: []
      }));
      setAnalysis({
        isHuman: null,
        confidence: 0,
        riskScore: 0,
        patterns: []
      });
    }
  };
};

export default useBehavioralAnalysis;