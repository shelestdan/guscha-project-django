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
  // Environment variable takes precedence
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // For containerized deployment with nginx, use current origin
  // This works for both development and production environments
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
