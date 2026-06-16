import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ size = 'md', className = '' }) {
  const sizeClass = size === 'sm' ? 'w-5 h-5' : size === 'lg' ? 'w-10 h-10' : 'w-7 h-7';
  return (
    <div className={`flex items-center justify-center py-12 ${className}`}>
      <Loader2 className={`${sizeClass} animate-spin text-brand-navy`} />
    </div>
  );
}
