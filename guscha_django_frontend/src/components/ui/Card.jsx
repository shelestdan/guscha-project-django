import React from 'react';

const Card = ({ 
  children, 
  className = '', 
  padding = 'md',
  shadow = 'md',
  hover = false,
  ...props 
}) => {
  const baseClasses = 'bg-white rounded-lg border border-primary-200 transition-all duration-200';
  
  const paddings = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };
  
  const shadows = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl',
  };
  
  const hoverEffect = hover ? 'hover:shadow-lg hover:-translate-y-1' : '';
  
  const classes = `${baseClasses} ${paddings[padding]} ${shadows[shadow]} ${hoverEffect} ${className}`;
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

Card.displayName = 'Card';

export default Card;

