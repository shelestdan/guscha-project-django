import CryptoJS from 'crypto-js';

/**
 * Утилиты для анти-спам защиты
 * Объединяет device fingerprinting и поведенческий анализ
 */

/**
 * Генерирует уникальный идентификатор сессии
 */
export const generateSessionId = () => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2);
  return CryptoJS.SHA256(`${timestamp}-${random}`).toString();
};

/**
 * Объединяет данные fingerprinting и поведенческого анализа
 */
export const combineSecurityData = (fingerprintData, behaviorData) => {
  const combined = {
    timestamp: Date.now(),
    sessionId: generateSessionId(),
    fingerprint: {
      hash: fingerprintData.hash,
      confidence: fingerprintData.confidence,
      components: fingerprintData.components
    },
    behavior: {
      isHuman: behaviorData.isHuman,
      confidence: behaviorData.confidence,
      riskScore: behaviorData.riskScore,
      totalInteractions: behaviorData.totalInteractions,
      patterns: behaviorData.patterns
    },
    overallRisk: calculateOverallRisk(fingerprintData, behaviorData)
  };
  
  return combined;
};

/**
 * Рассчитывает общий риск-скор на основе всех данных
 */
export const calculateOverallRisk = (fingerprintData, behaviorData) => {
  const fingerprintRisk = 100 - fingerprintData.confidence;
  const behaviorRisk = behaviorData.riskScore || 0;
  
  // Взвешенная оценка (поведение важнее fingerprinting)
  const weightedRisk = (fingerprintRisk * 0.3) + (behaviorRisk * 0.7);
  
  // Дополнительные факторы риска
  let additionalRisk = 0;
  
  // Высокий риск если есть признаки автоматизации
  if (fingerprintData.components.automation?.webdriver || 
      fingerprintData.components.automation?.phantom ||
      fingerprintData.components.automation?.selenium) {
    additionalRisk += 40;
  }
  
  // Высокий риск если нет взаимодействий
  if (behaviorData.totalInteractions === 0) {
    additionalRisk += 30;
  }
  
  // Высокий риск если есть подозрительные паттерны
  const highSeverityPatterns = behaviorData.patterns?.filter(p => p.severity === 'high').length || 0;
  additionalRisk += highSeverityPatterns * 15;
  
  const totalRisk = Math.min(100, weightedRisk + additionalRisk);
  
  return {
    score: Math.round(totalRisk),
    level: getRiskLevel(totalRisk),
    factors: {
      fingerprint: Math.round(fingerprintRisk),
      behavior: Math.round(behaviorRisk),
      additional: Math.round(additionalRisk)
    }
  };
};

/**
 * Определяет уровень риска
 */
export const getRiskLevel = (riskScore) => {
  if (riskScore >= 80) return 'critical';
  if (riskScore >= 60) return 'high';
  if (riskScore >= 40) return 'medium';
  if (riskScore >= 20) return 'low';
  return 'minimal';
};

/**
 * Проверяет, следует ли блокировать пользователя
 */
export const shouldBlockUser = (securityData, thresholds = {}) => {
  const {
    criticalThreshold = 80,
    highThreshold = 70,
    behaviorThreshold = 60,
    automationBlock = true
  } = thresholds;
  
  const overallRisk = securityData.overallRisk.score;
  const behaviorRisk = securityData.behavior.riskScore;
  const hasAutomation = securityData.fingerprint.components.automation?.webdriver ||
                       securityData.fingerprint.components.automation?.phantom ||
                       securityData.fingerprint.components.automation?.selenium;
  
  // Критический уровень риска
  if (overallRisk >= criticalThreshold) {
    return {
      shouldBlock: true,
      reason: 'critical_risk_score',
      message: 'Критический уровень риска безопасности'
    };
  }
  
  // Высокий уровень риска
  if (overallRisk >= highThreshold) {
    return {
      shouldBlock: true,
      reason: 'high_risk_score',
      message: 'Высокий уровень риска безопасности'
    };
  }
  
  // Обнаружена автоматизация
  if (automationBlock && hasAutomation) {
    return {
      shouldBlock: true,
      reason: 'automation_detected',
      message: 'Обнаружены признаки автоматизации'
    };
  }
  
  // Подозрительное поведение
  if (behaviorRisk >= behaviorThreshold) {
    return {
      shouldBlock: true,
      reason: 'suspicious_behavior',
      message: 'Подозрительные паттерны поведения'
    };
  }
  
  return {
    shouldBlock: false,
    reason: 'passed_security_checks',
    message: 'Проверки безопасности пройдены'
  };
};

/**
 * Генерирует отчет о безопасности для логирования
 */
export const generateSecurityReport = (securityData) => {
  const blockDecision = shouldBlockUser(securityData);
  
  return {
    timestamp: securityData.timestamp,
    sessionId: securityData.sessionId,
    decision: blockDecision,
    risk: {
      overall: securityData.overallRisk.score,
      level: securityData.overallRisk.level,
      factors: securityData.overallRisk.factors
    },
    fingerprint: {
      hash: securityData.fingerprint.hash,
      confidence: securityData.fingerprint.confidence,
      browser: securityData.fingerprint.components.browser,
      screen: securityData.fingerprint.components.screen,
      timezone: securityData.fingerprint.components.timezone,
      automation: securityData.fingerprint.components.automation
    },
    behavior: {
      isHuman: securityData.behavior.isHuman,
      confidence: securityData.behavior.confidence,
      riskScore: securityData.behavior.riskScore,
      interactions: securityData.behavior.totalInteractions,
      suspiciousPatterns: securityData.behavior.patterns?.length || 0,
      highRiskPatterns: securityData.behavior.patterns?.filter(p => p.severity === 'high').length || 0
    }
  };
};

/**
 * Отправляет данные безопасности на сервер
 */
export const sendSecurityData = async (securityData, endpoint = '/api/security/report') => {
  try {
    const report = generateSecurityReport(securityData);
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(report)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ошибка отправки данных безопасности:', error);
    throw error;
  }
};

/**
 * Создает middleware для проверки безопасности
 */
export const createSecurityMiddleware = (options = {}) => {
  const {
    autoBlock = true,
    logToConsole = false,
    sendToServer = true,
    serverEndpoint = '/api/security/report'
  } = options;
  
  return async (securityData) => {
    const blockDecision = shouldBlockUser(securityData);
    
    if (logToConsole) {
      console.log('Security Analysis:', generateSecurityReport(securityData));
    }
    
    if (sendToServer) {
      try {
        await sendSecurityData(securityData, serverEndpoint);
      } catch (error) {
        console.warn('Не удалось отправить данные безопасности на сервер:', error);
      }
    }
    
    if (autoBlock && blockDecision.shouldBlock) {
      // Можно добавить дополнительную логику блокировки
      console.warn('Пользователь заблокирован:', blockDecision.reason);
      return {
        blocked: true,
        reason: blockDecision.reason,
        message: blockDecision.message
      };
    }
    
    return {
      blocked: false,
      risk: securityData.overallRisk
    };
  };
};

/**
 * Утилита для дебага - показывает детальную информацию о проверках
 */
export const debugSecurityData = (securityData) => {
  console.group('🔒 Security Analysis Debug');
  
  console.log('📊 Overall Risk:', securityData.overallRisk);
  
  console.group('🖥️ Device Fingerprint');
  console.log('Hash:', securityData.fingerprint.hash);
  console.log('Confidence:', securityData.fingerprint.confidence);
  console.log('Components:', securityData.fingerprint.components);
  console.groupEnd();
  
  console.group('👤 Behavioral Analysis');
  console.log('Is Human:', securityData.behavior.isHuman);
  console.log('Confidence:', securityData.behavior.confidence);
  console.log('Risk Score:', securityData.behavior.riskScore);
  console.log('Interactions:', securityData.behavior.totalInteractions);
  console.log('Suspicious Patterns:', securityData.behavior.patterns);
  console.groupEnd();
  
  const blockDecision = shouldBlockUser(securityData);
  console.log('🚫 Block Decision:', blockDecision);
  
  console.groupEnd();
};

export default {
  generateSessionId,
  combineSecurityData,
  calculateOverallRisk,
  getRiskLevel,
  shouldBlockUser,
  generateSecurityReport,
  sendSecurityData,
  createSecurityMiddleware,
  debugSecurityData
};