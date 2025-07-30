interface AppConfig {
  api: {
    baseUrl: string;
    timeout: number;
  };
  auth: {
    tokenKey: string;
    sessionIdKey: string;
  };
  features: {
    enableGoogleAuth: boolean;
    enableCaptcha: boolean;
    enableQRVerification: boolean;
  };
  logging: {
    level: 'debug' | 'info' | 'warn' | 'error';
  };
}

const getBaseURL = (): string => {
  const currentHost = window.location.host;
  const currentProtocol = window.location.protocol;
  
  // Environment variable takes precedence
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // If frontend loaded from Django server (port 8000), use it for API
  if (currentHost.includes(':8000')) {
    return `${currentProtocol}//${currentHost}`;
  }
  
  // If frontend on development server (port 3000), use Nginx on 80
  if (currentHost.includes(':3000')) {
    return process.env.REACT_APP_API_URL || 'http://localhost';
  }
  
  // Default to current origin
  return window.location.origin;
};

export const config: AppConfig = {
  api: {
    baseUrl: getBaseURL(),
    timeout: Number(process.env.REACT_APP_API_TIMEOUT) || 30000,
  },
  auth: {
    tokenKey: 'token',
    sessionIdKey: 'cart-session-id',
  },
  features: {
    enableGoogleAuth: process.env.REACT_APP_ENABLE_GOOGLE_AUTH === 'true',
    enableCaptcha: process.env.REACT_APP_ENABLE_CAPTCHA === 'true',
    enableQRVerification: process.env.REACT_APP_ENABLE_QR_VERIFICATION === 'true',
  },
  logging: {
    level: (process.env.REACT_APP_LOG_LEVEL as AppConfig['logging']['level']) || 'info',
  },
};

export default config;
