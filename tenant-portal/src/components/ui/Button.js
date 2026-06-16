import React from 'react';

const variants = {
  primary: 'bg-brand-navy text-white hover:bg-brand-navy-dark',
  secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
  success: 'bg-emerald-500 text-white hover:bg-emerald-600',
  danger: 'bg-red-500 text-white hover:bg-red-600',
  accent: 'bg-brand-gold text-brand-navy hover:bg-yellow-400 font-semibold',
  ghost: 'bg-transparent text-gray-600 hover:bg-gray-100',
};

export default function Button({ children, variant = 'primary', className = '', disabled, ...props }) {
  return (
    <button
      className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
