import React from 'react';

const Input = React.memo(
  ({
    label,
    value,
    onChange,
    type = 'text',
    name,
    placeholder = '',
    className = '',
    error = '',
    disabled = false,
    required = false,
    ...props
  }) => {
    const inputId = name || `input-${Math.random().toString(36).substr(2, 9)}`;

    const wrapperClass = `form-group ${className}`.trim();
    const inputStateClass = error ? 'invalid error' : value ? 'valid' : '';
    const inputClass = `form-input ${inputStateClass}`.trim();

    return (
      <div className={wrapperClass}>
        {label && (
          <label htmlFor={inputId} className="form-label">
            {label}
            {required && <span className="required"> *</span>}
          </label>
        )}
        <input
          id={inputId}
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className={inputClass}
          {...props}
        />
        {error && (
          <div className="error-message" role="alert" aria-live="polite">
            <svg
              className="icon-error"
              width="16"
              height="16"
              viewBox="0 0 20 20"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              />
            </svg>
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
