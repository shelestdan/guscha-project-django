import React from 'react';

const Input = React.memo(({ 
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
  
  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label 
          htmlFor={inputId}
          className="block mb-2 text-sm font-medium text-primary-700"
        >
          {label}
          {required && <span className="text-accent-500 ml-1">*</span>}
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
        className={`
          w-full px-3 py-2 border rounded-md transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
          disabled:bg-primary-50 disabled:cursor-not-allowed
          ${error 
            ? 'border-accent-500 focus:ring-accent-500' 
            : 'border-primary-300 hover:border-primary-400'
          }
        `}
        {...props}
      />
      {error && (
        <div className="text-accent-600 text-sm mt-1 flex items-center">
          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input; 