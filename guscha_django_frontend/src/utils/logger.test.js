import { logger, Logger } from './logger';

// Мокируем console методы
const originalConsole = {
  log: console.log,
  info: console.info,
  warn: console.warn,
  error: console.error
};

const mockConsole = {
  log: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Мокируем process.env
const originalEnv = process.env;

describe('Logger', () => {
  beforeEach(() => {
    // Заменяем console методы на моки
    Object.assign(console, mockConsole);
    jest.clearAllMocks();
    
    // Сбрасываем process.env
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    // Восстанавливаем оригинальные console методы
    Object.assign(console, originalConsole);
    process.env = originalEnv;
  });

  describe('constructor', () => {
    it('должен использовать конфигурацию по умолчанию', () => {
      process.env.NODE_ENV = 'development';
      process.env.REACT_APP_LOG_LEVEL = undefined;
      
      const testLogger = new Logger();
      
      expect(testLogger.config.level).toBe('info');
      expect(testLogger.config.isDevelopment).toBe(true);
    });

    it('должен использовать уровень логирования из переменной окружения', () => {
      process.env.REACT_APP_LOG_LEVEL = 'debug';
      process.env.NODE_ENV = 'development';
      
      const testLogger = new Logger();
      
      expect(testLogger.config.level).toBe('debug');
    });

    it('должен определять production окружение', () => {
      process.env.NODE_ENV = 'production';
      
      const testLogger = new Logger();
      
      expect(testLogger.config.isDevelopment).toBe(false);
    });

    it('должен принимать пользовательскую конфигурацию', () => {
      const customConfig = {
        level: 'error',
        isDevelopment: true
      };
      
      const testLogger = new Logger(customConfig);
      
      expect(testLogger.config.level).toBe('error');
      expect(testLogger.config.isDevelopment).toBe(true);
    });
  });

  describe('shouldLog', () => {
    it('должен возвращать false в production окружении', () => {
      const testLogger = new Logger({ isDevelopment: false, level: 'debug' });
      
      expect(testLogger.shouldLog('debug')).toBe(false);
      expect(testLogger.shouldLog('info')).toBe(false);
      expect(testLogger.shouldLog('warn')).toBe(false);
      expect(testLogger.shouldLog('error')).toBe(false);
    });

    it('должен фильтровать по уровню в development окружении', () => {
      const testLogger = new Logger({ isDevelopment: true, level: 'warn' });
      
      expect(testLogger.shouldLog('debug')).toBe(false);
      expect(testLogger.shouldLog('info')).toBe(false);
      expect(testLogger.shouldLog('warn')).toBe(true);
      expect(testLogger.shouldLog('error')).toBe(true);
    });

    it('должен разрешать все уровни для debug', () => {
      const testLogger = new Logger({ isDevelopment: true, level: 'debug' });
      
      expect(testLogger.shouldLog('debug')).toBe(true);
      expect(testLogger.shouldLog('info')).toBe(true);
      expect(testLogger.shouldLog('warn')).toBe(true);
      expect(testLogger.shouldLog('error')).toBe(true);
    });
  });

  describe('formatMessage', () => {
    it('должен форматировать сообщение с временной меткой', () => {
      const testLogger = new Logger();
      const mockDate = new Date('2023-01-01T12:00:00.000Z');
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate);
      
      const result = testLogger.formatMessage('info', 'TestModule', 'Test message');
      
      expect(result).toBe('[2023-01-01T12:00:00.000Z] [INFO] [TestModule] Test message');
      
      global.Date.mockRestore();
    });

    it('должен корректно форматировать разные уровни', () => {
      const testLogger = new Logger();
      const mockDate = new Date('2023-01-01T12:00:00.000Z');
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate);
      
      expect(testLogger.formatMessage('debug', 'Module', 'Debug msg'))
        .toBe('[2023-01-01T12:00:00.000Z] [DEBUG] [Module] Debug msg');
      
      expect(testLogger.formatMessage('error', 'Module', 'Error msg'))
        .toBe('[2023-01-01T12:00:00.000Z] [ERROR] [Module] Error msg');
      
      global.Date.mockRestore();
    });
  });

  describe('logging methods', () => {
    let testLogger;
    
    beforeEach(() => {
      testLogger = new Logger({ isDevelopment: true, level: 'debug' });
    });

    describe('debug', () => {
      it('должен логировать debug сообщения', () => {
        testLogger.debug('TestModule', 'Debug message', { data: 'test' });
        
        expect(mockConsole.log).toHaveBeenCalledWith(
          expect.stringContaining('[DEBUG] [TestModule] Debug message'),
          { data: 'test' }
        );
      });

      it('должен логировать без данных', () => {
        testLogger.debug('TestModule', 'Debug message');
        
        expect(mockConsole.log).toHaveBeenCalledWith(
          expect.stringContaining('[DEBUG] [TestModule] Debug message'),
          ''
        );
      });

      it('не должен логировать если уровень выше debug', () => {
        const restrictedLogger = new Logger({ isDevelopment: true, level: 'info' });
        restrictedLogger.debug('TestModule', 'Debug message');
        
        expect(mockConsole.log).not.toHaveBeenCalled();
      });
    });

    describe('info', () => {
      it('должен логировать info сообщения', () => {
        testLogger.info('TestModule', 'Info message', { data: 'test' });
        
        expect(mockConsole.info).toHaveBeenCalledWith(
          expect.stringContaining('[INFO] [TestModule] Info message'),
          { data: 'test' }
        );
      });

      it('должен логировать без данных', () => {
        testLogger.info('TestModule', 'Info message');
        
        expect(mockConsole.info).toHaveBeenCalledWith(
          expect.stringContaining('[INFO] [TestModule] Info message'),
          ''
        );
      });
    });

    describe('warn', () => {
      it('должен логировать warn сообщения', () => {
        testLogger.warn('TestModule', 'Warning message', { data: 'test' });
        
        expect(mockConsole.warn).toHaveBeenCalledWith(
          expect.stringContaining('[WARN] [TestModule] Warning message'),
          { data: 'test' }
        );
      });

      it('должен логировать без данных', () => {
        testLogger.warn('TestModule', 'Warning message');
        
        expect(mockConsole.warn).toHaveBeenCalledWith(
          expect.stringContaining('[WARN] [TestModule] Warning message'),
          ''
        );
      });
    });

    describe('error', () => {
      it('должен логировать error сообщения', () => {
        const error = new Error('Test error');
        testLogger.error('TestModule', 'Error message', error);
        
        expect(mockConsole.error).toHaveBeenCalledWith(
          expect.stringContaining('[ERROR] [TestModule] Error message'),
          error
        );
      });

      it('должен логировать без ошибки', () => {
        testLogger.error('TestModule', 'Error message');
        
        expect(mockConsole.error).toHaveBeenCalledWith(
          expect.stringContaining('[ERROR] [TestModule] Error message'),
          ''
        );
      });
    });
  });

  describe('default logger instance', () => {
    beforeEach(() => {
      process.env.NODE_ENV = 'development';
      process.env.REACT_APP_LOG_LEVEL = 'info';
    });

    it('должен экспортировать готовый экземпляр логгера', () => {
      expect(logger).toBeInstanceOf(Logger);
    });

    it('должен использовать методы логирования', () => {
      const testLogger = new Logger({ isDevelopment: true, level: 'info' });
      testLogger.info('Test', 'Test message');
      
      expect(mockConsole.info).toHaveBeenCalledWith(
        expect.stringContaining('[INFO] [Test] Test message'),
        ''
      );
    });
  });

  describe('edge cases', () => {
    it('должен обрабатывать null/undefined данные', () => {
      const testLogger = new Logger({ isDevelopment: true, level: 'debug' });
      
      testLogger.debug('Test', 'Message', null);
      testLogger.info('Test', 'Message', undefined);
      
      expect(mockConsole.log).toHaveBeenCalledWith(
        expect.stringContaining('Message'),
        ''
      );
      expect(mockConsole.info).toHaveBeenCalledWith(
        expect.stringContaining('Message'),
        ''
      );
    });

    it('должен обрабатывать сложные объекты данных', () => {
      const testLogger = new Logger({ isDevelopment: true, level: 'debug' });
      const complexData = {
        nested: {
          array: [1, 2, 3],
          object: { key: 'value' }
        },
        function: () => 'test'
      };
      
      testLogger.debug('Test', 'Complex data', complexData);
      
      expect(mockConsole.log).toHaveBeenCalledWith(
        expect.stringContaining('Complex data'),
        complexData
      );
    });

    it('должен обрабатывать пустые строки в модуле и сообщении', () => {
      const testLogger = new Logger({ isDevelopment: true, level: 'debug' });
      
      testLogger.info('', '');
      
      expect(mockConsole.info).toHaveBeenCalledWith(
        expect.stringContaining('[INFO] [] '),
        ''
      );
    });
  });
});