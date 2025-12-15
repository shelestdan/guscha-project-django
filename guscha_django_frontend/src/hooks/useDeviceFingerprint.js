import { useState, useEffect, useCallback } from 'react';

/**
 * Хук для создания отпечатка устройства и браузера
 * Собирает различные характеристики для идентификации потенциальных ботов
 */
export const useDeviceFingerprint = () => {
  const [fingerprint, setFingerprint] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Получение информации о экране
  const getScreenInfo = useCallback(() => {
    return {
      width: window.screen.width,
      height: window.screen.height,
      availWidth: window.screen.availWidth,
      availHeight: window.screen.availHeight,
      colorDepth: window.screen.colorDepth,
      pixelDepth: window.screen.pixelDepth,
      devicePixelRatio: window.devicePixelRatio || 1
    };
  }, []);

  // Получение информации о браузере
  const getBrowserInfo = useCallback(() => {
    const nav = navigator;
    return {
      userAgent: nav.userAgent,
      language: nav.language,
      languages: nav.languages ? Array.from(nav.languages) : [],
      platform: nav.platform,
      cookieEnabled: nav.cookieEnabled,
      doNotTrack: nav.doNotTrack,
      hardwareConcurrency: nav.hardwareConcurrency || 0,
      maxTouchPoints: nav.maxTouchPoints || 0,
      vendor: nav.vendor || '',
      vendorSub: nav.vendorSub || '',
      productSub: nav.productSub || ''
    };
  }, []);

  // Получение информации о временной зоне
  const getTimezoneInfo = useCallback(() => {
    const date = new Date();
    return {
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      timezoneOffset: date.getTimezoneOffset(),
      locale: Intl.DateTimeFormat().resolvedOptions().locale
    };
  }, []);

  // Canvas fingerprinting
  const getCanvasFingerprint = useCallback(() => {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) return null;
      
      canvas.width = 200;
      canvas.height = 50;
      
      // Рисуем текст с различными стилями
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillStyle = '#f60';
      ctx.fillRect(125, 1, 62, 20);
      ctx.fillStyle = '#069';
      ctx.fillText('Device fingerprint test 🔒', 2, 15);
      ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
      ctx.fillText('Security check', 4, 35);
      
      // Добавляем геометрические фигуры
      ctx.globalCompositeOperation = 'multiply';
      ctx.fillStyle = 'rgb(255,0,255)';
      ctx.beginPath();
      ctx.arc(50, 25, 20, 0, Math.PI * 2, true);
      ctx.closePath();
      ctx.fill();
      
      return canvas.toDataURL();
    } catch (e) {
      return null;
    }
  }, []);

  // WebGL fingerprinting
  const getWebGLFingerprint = useCallback(() => {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      
      if (!gl) return null;
      
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      
      return {
        vendor: gl.getParameter(gl.VENDOR),
        renderer: gl.getParameter(gl.RENDERER),
        version: gl.getParameter(gl.VERSION),
        shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
        unmaskedVendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : null,
        unmaskedRenderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : null
      };
    } catch (e) {
      return null;
    }
  }, []);

  // Получение информации о плагинах
  const getPluginsInfo = useCallback(() => {
    if (!navigator.plugins) return [];
    
    return Array.from(navigator.plugins).map(plugin => ({
      name: plugin.name,
      filename: plugin.filename,
      description: plugin.description,
      version: plugin.version || ''
    }));
  }, []);

  // Проверка на наличие автоматизации
  const getAutomationDetection = useCallback(() => {
    return {
      webdriver: navigator.webdriver || false,
      phantom: window.phantom !== undefined,
      selenium: window._selenium !== undefined,
      callPhantom: window.callPhantom !== undefined,
      chromeRuntime: window.chrome && window.chrome.runtime,
      permissions: navigator.permissions !== undefined
    };
  }, []);

  // Создание хеша отпечатка
  const createHash = useCallback((data) => {
    const str = JSON.stringify(data);
    let hash = 0;
    
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(16);
  }, []);

  // Основная функция сбора отпечатка
  const generateFingerprint = useCallback(async () => {
    setIsLoading(true);
    
    try {
      const fingerprintData = {
        screen: getScreenInfo(),
        browser: getBrowserInfo(),
        timezone: getTimezoneInfo(),
        canvas: getCanvasFingerprint(),
        webgl: getWebGLFingerprint(),
        plugins: getPluginsInfo(),
        automation: getAutomationDetection(),
        timestamp: Date.now()
      };
      
      const hash = createHash(fingerprintData);
      
      const result = {
        hash,
        data: fingerprintData,
        confidence: calculateConfidence(fingerprintData)
      };
      
      setFingerprint(result);
      return result;
    } catch (error) {
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [getScreenInfo, getBrowserInfo, getTimezoneInfo, getCanvasFingerprint, getWebGLFingerprint, getPluginsInfo, getAutomationDetection, createHash]);

  // Расчет уровня доверия
  const calculateConfidence = useCallback((data) => {
    let confidence = 100;
    
    // Снижаем доверие при обнаружении признаков автоматизации
    if (data.automation.webdriver) confidence -= 30;
    if (data.automation.phantom) confidence -= 25;
    if (data.automation.selenium) confidence -= 25;
    if (data.automation.callPhantom) confidence -= 20;
    
    // Снижаем доверие при подозрительных характеристиках браузера
    if (!data.browser.cookieEnabled) confidence -= 10;
    if (data.browser.languages.length === 0) confidence -= 15;
    if (!data.canvas) confidence -= 20;
    if (!data.webgl) confidence -= 10;
    
    // Снижаем доверие при нестандартных характеристиках экрана
    if (data.screen.width === 0 || data.screen.height === 0) confidence -= 25;
    if (data.screen.colorDepth < 16) confidence -= 15;
    
    return Math.max(0, confidence);
  }, []);

  useEffect(() => {
    generateFingerprint();
  }, [generateFingerprint]);

  return {
    fingerprint,
    isLoading,
    regenerate: generateFingerprint
  };
};

export default useDeviceFingerprint;