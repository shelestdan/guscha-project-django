import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useDeviceFingerprint } from '../hooks/useDeviceFingerprint';
import { useBehavioralAnalysis } from '../hooks/useBehavioralAnalysis';
import {
  combineSecurityData,
  createSecurityMiddleware,
  debugSecurityData
} from '../utils/antiSpamUtils';

// Контекст безопасности
const SecurityContext = createContext(null);

/**
 * Провайдер безопасности для анти-спам защиты
 * Объединяет device fingerprinting и поведенческий анализ
 */
export const SecurityProvider = ({ 
  children, 
  options = {},
  onSecurityUpdate = null,
  onSecurityBlock = null
}) => {
  const {
    enableFingerprinting = true,
    enableBehavioralAnalysis = true,
    autoAnalysis = true,
    analysisInterval = 15000, // 15 секунд
    debugMode = false,
    serverEndpoint = '/api/security/report',
    blockThresholds = {
      criticalThreshold: 80,
      highThreshold: 70,
      behaviorThreshold: 60,
      automationBlock: true
    }
  } = options;

  // Состояние безопасности
  const [securityState, setSecurityState] = useState({
    isReady: false,
    isBlocked: false,
    blockReason: null,
    lastAnalysis: null,
    analysisHistory: []
  });

  // Хуки для сбора данных
  const fingerprintData = useDeviceFingerprint({
    enabled: enableFingerprinting,
    includeCanvas: true,
    includeWebGL: true,
    includeAudio: false // Отключаем аудио для производительности
  });

  const behaviorAnalysis = useBehavioralAnalysis({
    trackMouse: enableBehavioralAnalysis,
    trackKeyboard: enableBehavioralAnalysis,
    trackScroll: enableBehavioralAnalysis,
    trackFocus: enableBehavioralAnalysis,
    minInteractions: 3
  });

  // Middleware для обработки результатов анализа
  const securityMiddleware = createSecurityMiddleware({
    autoBlock: false, // Мы сами управляем блокировкой
    logToConsole: debugMode,
    sendToServer: true,
    serverEndpoint
  });

  // Функция полного анализа безопасности
  const performSecurityAnalysis = useCallback(async () => {
    if (!fingerprintData.isReady) {
      return null;
    }

    try {
      // Получаем данные поведенческого анализа
      const behaviorData = behaviorAnalysis.performAnalysis();
      
      // Объединяем все данные
      const combinedData = combineSecurityData(fingerprintData, behaviorData);
      
      // Обрабатываем через middleware
      const middlewareResult = await securityMiddleware(combinedData);
      
      // Обновляем состояние
      const newAnalysis = {
        timestamp: Date.now(),
        data: combinedData,
        result: middlewareResult
      };
      
      setSecurityState(prev => ({
        ...prev,
        isReady: true,
        lastAnalysis: newAnalysis,
        analysisHistory: [...prev.analysisHistory.slice(-9), newAnalysis], // Храним последние 10
        isBlocked: middlewareResult.blocked || prev.isBlocked,
        blockReason: middlewareResult.blocked ? middlewareResult.reason : prev.blockReason
      }));
      
      // Debug информация
      if (debugMode) {
        debugSecurityData(combinedData);
      }
      
      // Колбэки
      if (onSecurityUpdate) {
        onSecurityUpdate(newAnalysis);
      }
      
      if (middlewareResult.blocked && onSecurityBlock) {
        onSecurityBlock(middlewareResult);
      }
      
      return newAnalysis;
    } catch (error) {
      console.error('Ошибка анализа безопасности:', error);
      return null;
    }
  }, [fingerprintData, behaviorAnalysis, securityMiddleware, debugMode, onSecurityUpdate, onSecurityBlock]);

  // Функция принудительной блокировки
  const blockUser = useCallback((reason = 'manual_block', message = 'Пользователь заблокирован') => {
    setSecurityState(prev => ({
      ...prev,
      isBlocked: true,
      blockReason: reason
    }));
    
    if (onSecurityBlock) {
      onSecurityBlock({ blocked: true, reason, message });
    }
  }, [onSecurityBlock]);

  // Функция разблокировки
  const unblockUser = useCallback(() => {
    setSecurityState(prev => ({
      ...prev,
      isBlocked: false,
      blockReason: null
    }));
  }, []);

  // Функция сброса анализа поведения
  const resetBehaviorAnalysis = useCallback(() => {
    behaviorAnalysis.reset();
  }, [behaviorAnalysis]);

  // Функция получения текущего статуса безопасности
  const getSecurityStatus = useCallback(() => {
    if (!securityState.lastAnalysis) {
      return {
        status: 'pending',
        message: 'Анализ безопасности не завершен'
      };
    }
    
    if (securityState.isBlocked) {
      return {
        status: 'blocked',
        message: 'Пользователь заблокирован',
        reason: securityState.blockReason
      };
    }
    
    const riskLevel = securityState.lastAnalysis.data.overallRisk.level;
    
    switch (riskLevel) {
      case 'critical':
        return { status: 'critical', message: 'Критический уровень риска' };
      case 'high':
        return { status: 'high', message: 'Высокий уровень риска' };
      case 'medium':
        return { status: 'medium', message: 'Средний уровень риска' };
      case 'low':
        return { status: 'low', message: 'Низкий уровень риска' };
      default:
        return { status: 'safe', message: 'Безопасно' };
    }
  }, [securityState]);

  // Автоматический анализ
  useEffect(() => {
    if (!autoAnalysis || !fingerprintData.isReady) {
      return;
    }

    // Первый анализ через 5 секунд после готовности fingerprint
    const initialTimeout = setTimeout(() => {
      performSecurityAnalysis();
    }, 5000);

    // Периодический анализ
    const interval = setInterval(() => {
      performSecurityAnalysis();
    }, analysisInterval);

    return () => {
      clearTimeout(initialTimeout);
      clearInterval(interval);
    };
  }, [autoAnalysis, fingerprintData.isReady, analysisInterval, performSecurityAnalysis]);

  // Значение контекста
  const contextValue = {
    // Состояние
    isReady: securityState.isReady,
    isBlocked: securityState.isBlocked,
    blockReason: securityState.blockReason,
    lastAnalysis: securityState.lastAnalysis,
    analysisHistory: securityState.analysisHistory,
    
    // Данные
    fingerprintData,
    behaviorAnalysis,
    
    // Функции
    performSecurityAnalysis,
    blockUser,
    unblockUser,
    resetBehaviorAnalysis,
    getSecurityStatus,
    
    // Утилиты
    debugMode
  };

  return (
    <SecurityContext.Provider value={contextValue}>
      {children}
    </SecurityContext.Provider>
  );
};

/**
 * Хук для использования контекста безопасности
 */
export const useSecurity = () => {
  const context = useContext(SecurityContext);
  
  if (!context) {
    throw new Error('useSecurity должен использоваться внутри SecurityProvider');
  }
  
  return context;
};

/**
 * HOC для компонентов, требующих проверки безопасности
 */
export const withSecurityCheck = (WrappedComponent, options = {}) => {
  const {
    blockOnHighRisk = true,
    showBlockMessage = true,
    customBlockComponent = null
  } = options;
  
  return function SecurityCheckedComponent(props) {
    const security = useSecurity();
    
    if (!security.isReady) {
      return (
        <div className="security-loading">
          <div className="spinner"></div>
          <p>Проверка безопасности...</p>
        </div>
      );
    }
    
    if (security.isBlocked || (blockOnHighRisk && security.lastAnalysis?.data.overallRisk.level === 'critical')) {
      if (customBlockComponent) {
        return React.createElement(customBlockComponent, { security });
      }
      
      if (showBlockMessage) {
        return (
          <div className="security-blocked">
            <h2>Доступ ограничен</h2>
            <p>Ваш запрос был заблокирован системой безопасности.</p>
            <p>Причина: {security.blockReason}</p>
            <p>Если вы считаете, что это ошибка, обратитесь в службу поддержки.</p>
          </div>
        );
      }
      
      return null;
    }
    
    return <WrappedComponent {...props} />;
  };
};

/**
 * Компонент индикатора безопасности для разработки
 */
export const SecurityIndicator = ({ className = '' }) => {
  const security = useSecurity();
  
  if (!security.debugMode || !security.isReady) {
    return null;
  }
  
  const status = security.getSecurityStatus();
  const riskScore = security.lastAnalysis?.data.overallRisk.score || 0;
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'safe': return '#4CAF50';
      case 'low': return '#8BC34A';
      case 'medium': return '#FF9800';
      case 'high': return '#FF5722';
      case 'critical': return '#F44336';
      case 'blocked': return '#9C27B0';
      default: return '#9E9E9E';
    }
  };
  
  return (
    <div 
      className={`security-indicator ${className}`}
      style={{
        position: 'fixed',
        top: '10px',
        right: '10px',
        padding: '8px 12px',
        backgroundColor: getStatusColor(status.status),
        color: 'white',
        borderRadius: '4px',
        fontSize: '12px',
        zIndex: 9999,
        cursor: 'pointer'
      }}
      onClick={() => {
        if (security.lastAnalysis) {
          debugSecurityData(security.lastAnalysis.data);
        }
      }}
      title="Нажмите для просмотра деталей в консоли"
    >
      🔒 {status.status.toUpperCase()} ({riskScore}%)
    </div>
  );
};

export default SecurityProvider;