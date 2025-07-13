import React from 'react';

const Button = React.memo(({ 
  children, 
  onClick, 
  type = 'button', 
  variant = 'primary',
  size = 'md',
  className = '', 
  disabled = false, 
  ...props 
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-primary-900 text-white hover:bg-primary-800 focus:ring-primary-500',
    secondary: 'bg-primary-100 text-primary-900 hover:bg-primary-200 focus:ring-primary-500',
    outline: 'border border-primary-300 text-primary-700 hover:bg-primary-50 focus:ring-primary-500',
    ghost: 'text-primary-700 hover:bg-primary-100 focus:ring-primary-500',
    danger: 'bg-accent-600 text-white hover:bg-accent-700 focus:ring-accent-500',
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };
  
  const classes = `${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`;
  
  return (
    <button
      type={type}
      className={classes}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
});

Button.displayName = 'Button';

export default Button; 