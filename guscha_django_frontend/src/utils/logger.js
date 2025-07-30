/**
 * @typedef {'debug' | 'info' | 'warn' | 'error'} LogLevel
 * @typedef {{level: LogLevel, isDevelopment: boolean}} LoggerConfig
 */

class Logger {
  /**
   * @param {Partial<LoggerConfig>} [config]
   */
  constructor(config) {
    this.levels = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3,
    };
    
    this.config = {
      level: process.env.REACT_APP_LOG_LEVEL || 'info',
      isDevelopment: process.env.NODE_ENV === 'development',
      ...config,
    };
  }

  /**
   * @private
   * @param {LogLevel} level
   * @returns {boolean}
   */
  shouldLog(level) {
    return this.config.isDevelopment && this.levels[level] >= this.levels[this.config.level];
  }

  /**
   * @private
   * @param {LogLevel} level
   * @param {string} module
   * @param {string} message
   * @returns {string}
   */
  formatMessage(level, module, message) {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level.toUpperCase()}] [${module}] ${message}`;
  }

  /**
   * @param {string} module
   * @param {string} message
   * @param {any} [data]
   */
  debug(module, message, data) {
    if (this.shouldLog('debug')) {
      console.log(this.formatMessage('debug', module, message), data || '');
    }
  }

  /**
   * @param {string} module
   * @param {string} message
   * @param {any} [data]
   */
  info(module, message, data) {
    if (this.shouldLog('info')) {
      console.info(this.formatMessage('info', module, message), data || '');
    }
  }

  /**
   * @param {string} module
   * @param {string} message
   * @param {any} [data]
   */
  warn(module, message, data) {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('warn', module, message), data || '');
    }
  }

  /**
   * @param {string} module
   * @param {string} message
   * @param {any} [error]
   */
  error(module, message, error) {
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('error', module, message), error || '');
    }
  }
}

export const logger = new Logger();
export default logger;
