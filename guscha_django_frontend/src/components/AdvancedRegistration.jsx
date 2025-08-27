import React, { useState, useEffect } from 'react';
import validator from 'validator';
import { 
  FiEye, 
  FiEyeOff, 
  FiCheck, 
  FiX, 
  FiMail, 
  FiPhone, 
  FiLock, 
  FiUser,
  FiShield
} from 'react-icons/fi';
import '../styles/AdvancedRegistration.css';
import { PasswordSecurityBadge } from './SecurityIndicator';
import { useToast } from '../hooks/useToast';

const AdvancedRegistration = ({ onRegister, onSwitchToLogin }) => {
  const { showSuccess, showError, showWarning } = useToast();
  
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    termsAccepted: true
  });

  const [validation, setValidation] = useState({
    firstName: { isValid: false, message: '' },
    lastName: { isValid: false, message: '' },
    email: { isValid: false, message: '' },
    phone: { isValid: false, message: '' },
    password: { isValid: false, message: '', strength: 0 },
    confirmPassword: { isValid: false, message: '' },
    termsAccepted: { isValid: true, message: '' } // По умолчанию true, так как termsAccepted тоже true
  });

  // Состояние для серверных ошибок
  const [serverErrors, setServerErrors] = useState({
    email: '',
    phone: '',
    general: ''
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFormValid, setIsFormValid] = useState(false);

  // Скролл теперь разрешен на страницах регистрации

  // Валидация имени
  const validateName = (name, _field) => {
    if (!name.trim()) {
      return { isValid: false, message: 'Поле обязательно для заполнения' };
    }
    if (name.length < 2) {
      return { isValid: false, message: 'Минимум 2 символа' };
    }
    if (name.length > 50) {
      return { isValid: false, message: 'Максимум 50 символов' };
    }
    if (!/^[а-яёА-ЯЁa-zA-Z\s-]+$/.test(name)) {
      return { isValid: false, message: 'Только буквы, пробелы и дефисы' };
    }
    return { isValid: true, message: 'Корректно' };
  };

  // Валидация email
  const validateEmail = (email) => {
    if (!email.trim()) {
      return { isValid: false, message: 'Email обязателен' };
    }
    if (!validator.isEmail(email)) {
      return { isValid: false, message: 'Некорректный формат email' };
    }
    if (email.length > 254) {
      return { isValid: false, message: 'Email слишком длинный' };
    }
    return { isValid: true, message: 'Корректный email' };
  };

  // Валидация телефона
  const validatePhone = (phone) => {
    if (!phone) {
      return { isValid: false, message: 'Номер телефона обязателен' };
    }
    // Simple international phone number validation
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    if (!phoneRegex.test(phone.replace(/[\s()-]/g, ''))) {
      return { isValid: false, message: 'Некорректный номер телефона' };
    }
    return { isValid: true, message: 'Корректный номер' };
  };

  // Валидация пароля согласно стандартам OWASP
  const validatePassword = (password) => {
    if (!password) {
      return { 
        isValid: false, 
        errors: ['Пароль обязателен'], 
        suggestions: [],
        score: 0,
        strength: 'weak',
        checks: {
          length: false,
          uppercase: false,
          lowercase: false,
          number: false,
          special: false,
          noSpaces: true
        }
      };
    }

    const errors = [];
    const suggestions = [];
    let score = 0;

    // Создаем объект checks для проверок
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*()_\-+,.?":{}|<>]/.test(password),
      noSpaces: !/\s/.test(password)
    };

    // Минимальная длина
    if (!checks.length) {
      errors.push('Пароль должен содержать минимум 8 символов');
    } else {
      score += 1;
    }

    // Проверка на цифры
    if (!checks.number) {
      errors.push('Пароль должен содержать хотя бы одну цифру');
    } else {
      score += 1;
    }

    // Проверка на строчные буквы
    if (!checks.lowercase) {
      errors.push('Пароль должен содержать строчные буквы');
    } else {
      score += 1;
    }

    // Проверка на заглавные буквы
    if (!checks.uppercase) {
      errors.push('Пароль должен содержать заглавные буквы');
    } else {
      score += 1;
    }

    // Проверка на специальные символы
    if (!checks.special) {
      suggestions.push('Рекомендуется добавить специальные символы для большей безопасности');
    } else {
      score += 1;
    }

    // Проверка на пробелы
    if (!checks.noSpaces) {
      errors.push('Пароль не должен содержать пробелы');
    }
    
    return {
      isValid: errors.length === 0 && score >= 3,
      errors,
      suggestions,
      score,
      strength: score >= 4 ? 'strong' : score >= 2 ? 'medium' : 'weak',
      checks
    };
  };

  // Валидация подтверждения пароля
  const validateConfirmPassword = (confirmPassword, password) => {
    if (!confirmPassword) {
      return { isValid: false, message: 'Подтвердите пароль' };
    }
    if (confirmPassword !== password) {
      return { isValid: false, message: 'Пароли не совпадают' };
    }
    return { isValid: true, message: 'Пароли совпадают' };
  };

  // Валидация принятия условий
  const validateTermsAccepted = (accepted) => {
    if (!accepted) {
      return { isValid: false, message: 'Необходимо принять условия использования' };
    }
    return { isValid: true, message: 'Условия приняты' };
  };

  // Обработка изменений в форме
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));

    // Очищаем серверные ошибки для этого поля
    if (serverErrors[field]) {
      setServerErrors(prev => ({ ...prev, [field]: '' }));
    }

    let validationResult;
    switch (field) {
      case 'firstName':
      case 'lastName':
        validationResult = validateName(value, field);
        break;
      case 'email':
        validationResult = validateEmail(value);
        break;
      case 'phone':
        validationResult = validatePhone(value);
        break;
      case 'password':
        validationResult = validatePassword(value);
        // Также переваlidируем подтверждение пароля
        if (formData.confirmPassword) {
          const confirmValidation = validateConfirmPassword(formData.confirmPassword, value);
          setValidation(prev => ({ 
            ...prev, 
            confirmPassword: confirmValidation 
          }));
        }
        break;
      case 'confirmPassword':
        validationResult = validateConfirmPassword(value, formData.password);
        break;
      case 'termsAccepted':
        validationResult = validateTermsAccepted(value);
        break;
      default:
        return;
    }

    setValidation(prev => ({ ...prev, [field]: validationResult }));
  };

  // Проверка валидности всей формы
  useEffect(() => {
    const allFieldsValid = Object.values(validation).every(field => field.isValid);
    // Проверяем все поля кроме termsAccepted (это boolean)
    const textFieldsFilled = Object.entries(formData)
      .filter(([key]) => key !== 'termsAccepted')
      .every(([_key, value]) => value.trim() !== '');
    const termsAccepted = formData.termsAccepted;
    const noServerErrors = !serverErrors.email && !serverErrors.phone && !serverErrors.general;
    setIsFormValid(allFieldsValid && textFieldsFilled && termsAccepted && noServerErrors);
  }, [validation, formData, serverErrors]);

  // Отправка формы
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Проверяем валидность всех полей
    if (!validation.firstName.isValid || !validation.lastName.isValid || 
        !validation.email.isValid || !validation.phone.isValid || 
        !validation.password.isValid || !validation.confirmPassword.isValid ||
        !validation.termsAccepted.isValid) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      // 🔐 СТАНДАРТ OWASP: Передаем пароль в открытом виде через HTTPS
      // Хеширование происходит только на сервере
      const registrationData = {
        first_name: formData.firstName.trim(),
        last_name: formData.lastName.trim(),
        email: formData.email.trim().toLowerCase(),
        phone: formData.phone,
        password: formData.password, // Пароль в открытом виде
        password_confirm: formData.confirmPassword, // Подтверждение пароля
        terms_accepted: formData.termsAccepted
      };
      
      console.log('DEBUG: Registration data being sent:', registrationData);
      console.log('DEBUG: termsAccepted value:', formData.termsAccepted);
      console.log('DEBUG: termsAccepted in registrationData:', registrationData.terms_accepted);

      console.log('🔐 Отправка данных регистрации');
      const result = await onRegister(registrationData);
      
      console.log('✅ Регистрация успешна:', result);
      
      // Показываем уведомление об успешной регистрации
      showSuccess('🎉 Регистрация прошла успешно! Проверьте Telegram для подтверждения', 5000);
      
      // Результат уже передан через onRegister выше
      // Родительский компонент (AdvancedAuth) обработает переход к Telegram-верификации
      // если в result есть verification_id
    } catch (error) {
      console.error('Ошибка регистрации:', error);
      console.log('Подробности ошибки:');
      console.log('Статус:', error.response?.status);
      console.log('Данные ошибки:', error.response?.data);
      console.log('Сообщение ошибки:', error.message);
      
      // Очищаем предыдущие ошибки
      setServerErrors({ email: '', phone: '', general: '' });
      
      // Небольшая задержка, чтобы избежать конфликтов состояния
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Парсим ошибки сервера и показываем под соответствующими полями
      if (error.response && error.response.data) {
        const errorData = error.response.data;
        
        // Проверяем ошибки валидации из актуального формата сервера
        if (errorData.details) {
          const newServerErrors = { email: '', phone: '', general: '' };
          
          if (errorData.details.email) {
            newServerErrors.email = Array.isArray(errorData.details.email) 
              ? errorData.details.email[0] 
              : errorData.details.email;
            // Показываем уведомление для ошибки email
            console.log('🔔 Отправляем тост об ошибке email');
            const emailErrorMsg = `❌ Пользователь с таким email уже зарегистрирован (${new Date().toLocaleTimeString()})`;
            showError(emailErrorMsg, 6000);
          }
          
          if (errorData.details.phone) {
            newServerErrors.phone = Array.isArray(errorData.details.phone) 
              ? errorData.details.phone[0] 
              : errorData.details.phone;
            // Показываем уведомление для ошибки телефона
            console.log('🔔 Отправляем тост об ошибке телефона');
            const phoneErrorMsg = `📱 Пользователь с таким номером телефона уже зарегистрирован (${new Date().toLocaleTimeString()})`;
            showError(phoneErrorMsg, 6000);
          }
          
          console.log('Установлены серверные ошибки:', newServerErrors);
          setServerErrors(newServerErrors);
        }
        // Резервная проверка старого формата ошибок (на случай изменения API)
        else if (errorData.errors) {
          const newServerErrors = { email: '', phone: '', general: '' };
          
          if (errorData.errors.email) {
            newServerErrors.email = Array.isArray(errorData.errors.email) 
              ? errorData.errors.email[0] 
              : errorData.errors.email;
            showError('❌ Пользователь с таким email уже зарегистрирован', 6000);
          }
          
          if (errorData.errors.phone) {
            newServerErrors.phone = Array.isArray(errorData.errors.phone) 
              ? errorData.errors.phone[0] 
              : errorData.errors.phone;
            showError('📱 Пользователь с таким номером телефона уже зарегистрирован', 6000);
          }
          
          console.log('Установлены серверные ошибки:', newServerErrors);
          setServerErrors(newServerErrors);
        } 
        // Проверяем общие ошибки
        else if (errorData.message) {
          if (errorData.message.includes('email уже зарегистрирован')) {
            setServerErrors({ email: 'Пользователь с таким email уже зарегистрирован', phone: '', general: '' });
            showError('❌ Этот email уже используется другим аккаунтом', 6000);
          } else if (errorData.message.includes('номером телефона уже зарегистрирован')) {
            setServerErrors({ email: '', phone: 'Пользователь с таким номером телефона уже зарегистрирован', general: '' });
            showError('📱 Этот номер телефона уже привязан к другому аккаунту', 6000);
          } else {
            setServerErrors({ email: '', phone: '', general: errorData.message });
            showError('⚠️ Ошибка регистрации: ' + errorData.message, 6000);
          }
        }
        // Если есть общее описание ошибки в поле 'error'
        else if (errorData.error) {
          setServerErrors({ email: '', phone: '', general: errorData.error });
          showError('⚠️ ' + errorData.error, 6000);
        }
      } else {
        // Нет ошибок сервера или нет response.data
        const errorMessage = error.message || 'Произошла ошибка при регистрации. Попробуйте позже.';
        console.log('Общая ошибка:', errorMessage);
        
        setServerErrors({ email: '', phone: '', general: errorMessage });
        
        // Показываем уведомление с подробной информацией
        if (error.response?.status) {
          showError(`🔴 Ошибка сервера ${error.response.status}: ${errorMessage}`, 6000);
        } else {
          showError('🔴 Произошла ошибка при регистрации. Попробуйте позже.', 6000);
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Компонент индикатора силы пароля - компактный
  const PasswordStrengthIndicator = ({ validation }) => {
    if (!validation.checks) return null;

    const getStrengthLabel = (strengthString) => {
      switch (strengthString) {
        case 'weak': return 'Слабый';
        case 'medium': return 'Средний';
        case 'strong': return 'Сильный';
        default: return 'Неизвестно';
      }
    };

    return (
      <div className="password-strength">
        <div className={`password-strength-bar password-strength-${validation.strength}`}>
        </div>
        <div className={`password-strength-text password-strength-${validation.strength}-text`}>
          {getStrengthLabel(validation.strength)}
        </div>
        <div className="password-requirements">
          <div className={`requirement ${validation.checks?.length ? 'met' : ''}`}>
            {validation.checks?.length ? <FiCheck /> : <FiX />}
            <span>8+ символов</span>
          </div>
          <div className={`requirement ${validation.checks?.uppercase ? 'met' : ''}`}>
            {validation.checks?.uppercase ? <FiCheck /> : <FiX />}
            <span>Заглавная</span>
          </div>
          <div className={`requirement ${validation.checks?.lowercase ? 'met' : ''}`}>
            {validation.checks?.lowercase ? <FiCheck /> : <FiX />}
            <span>Строчная</span>
          </div>
          <div className={`requirement ${validation.checks?.number ? 'met' : ''}`}>
            {validation.checks?.number ? <FiCheck /> : <FiX />}
            <span>Цифра</span>
          </div>
          <div className={`requirement ${validation.checks?.special ? 'met' : ''}`}>
            {validation.checks?.special ? <FiCheck /> : <FiX />}
            <span>Спецсимвол</span>
          </div>
          <div className={`requirement ${validation.checks?.noSpaces ? 'met' : ''}`}>
            {validation.checks?.noSpaces ? <FiCheck /> : <FiX />}
            <span>Без пробелов</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="advanced-registration">
      <div className="registration-container form-system">
        <div className="registration-header">
          <h1>Создать аккаунт</h1>
          <p>Заполните поля для регистрации</p>
        </div>

        <form className="registration-form" onSubmit={handleSubmit}>
          {/* Общие серверные ошибки */}
          {serverErrors.general && (
            <div className="error-banner">
              <FiX />
              <span>{serverErrors.general}</span>
            </div>
          )}
          <div className="form-row">
            <div className="form-group">
              <div className="input-with-icon">
                <FiUser className="input-icon" />
                <input
                  type="text"
                  className={`form-input ${
                    formData.firstName ? (validation.firstName.isValid ? 'valid' : 'invalid') : ''
                  }`}
                  value={formData.firstName}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
                  placeholder="Имя"
                  disabled={isSubmitting}
                  autoComplete="given-name"
                />
              </div>
            </div>

            <div className="form-group">
              <div className="input-with-icon">
                <FiUser className="input-icon" />
                <input
                  type="text"
                  className={`form-input ${
                    formData.lastName ? (validation.lastName.isValid ? 'valid' : 'invalid') : ''
                  }`}
                  value={formData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                  placeholder="Фамилия"
                  disabled={isSubmitting}
                  autoComplete="family-name"
                />
              </div>
            </div>
          </div>

          <div className="form-group">
            <div className="input-with-icon">
              <FiMail className="input-icon" />
              <input
                type="email"
                className={`form-input ${
                  serverErrors.email ? 'invalid' : 
                  formData.email ? (validation.email.isValid ? 'valid' : 'invalid') : ''
                }`}
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                placeholder="example@domain.com"
                disabled={isSubmitting}
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-group">
            <div className="input-with-icon">
              <FiPhone className="input-icon" />
              <input
                type="tel"
                className={`form-input ${
                  serverErrors.phone ? 'invalid' : 
                  formData.phone ? (validation.phone.isValid ? 'valid' : 'invalid') : ''
                }`}
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                placeholder="+1 234 567-8900"
                disabled={isSubmitting}
                autoComplete="tel"
              />
            </div>
          </div>

          <div className="form-group">
            <div className="input-with-icon">
              <FiLock className="input-icon" />
              <input
                type={showPassword ? 'text' : 'password'}
                className={`form-input ${
                  formData.password ? (validation.password.isValid ? 'valid' : 'invalid') : ''
                }`}
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                placeholder="Создайте пароль"
                disabled={isSubmitting}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isSubmitting}
                aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
            {formData.password && (
              <PasswordStrengthIndicator validation={validation.password} />
            )}
          </div>

          <div className="form-group">
            <div className="input-with-icon">
              <FiShield className="input-icon" />
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                className={`form-input ${
                  formData.confirmPassword ? (validation.confirmPassword.isValid ? 'valid' : 'invalid') : ''
                }`}
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                placeholder="Повторите пароль"
                disabled={isSubmitting}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                disabled={isSubmitting}
                aria-label={showConfirmPassword ? 'Скрыть пароль' : 'Показать пароль'}
              >
                {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.termsAccepted}
                onChange={(e) => handleInputChange('termsAccepted', e.target.checked)}
                disabled={isSubmitting}
              />
              <span className="checkmark"></span>
              <span className="checkbox-text">
                Я принимаю{' '}
                <a href="/terms" target="_blank" rel="noopener noreferrer">
                  условия использования
                </a>
                {' '}и{' '}
                <a href="/privacy" target="_blank" rel="noopener noreferrer">
                  политику конфиденциальности
                </a>
              </span>
            </label>
            {!validation.termsAccepted.isValid && formData.termsAccepted !== null && (
              <div className="validation-message error">
                <FiX />
                <span>{validation.termsAccepted.message}</span>
              </div>
            )}
          </div>

          <button
            type="submit"
            className={`register-btn ${isFormValid ? 'enabled' : 'disabled'}`}
            disabled={!isFormValid || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <div className="btn-spinner" />
                Создание аккаунта...
              </>
            ) : (
              'Создать аккаунт'
            )}
          </button>
        </form>

        <div className="form-footer">
          <p>
            Уже есть аккаунт?{' '}
            <button
              type="button"
              className="link-btn"
              onClick={onSwitchToLogin}
              disabled={isSubmitting}
            >
              Войти
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdvancedRegistration;