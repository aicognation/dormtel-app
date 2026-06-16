import React from 'react';
import { STATUS_COLORS } from '../../utils/constants';

export default function StatusBadge({ status }) {
  const colorClass = STATUS_COLORS[status] || 'bg-gray-100 text-gray-800';
  const label = status ? status.replace(/_/g, ' ') : 'unknown';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${colorClass}`}>
      {label}
    </span>
  );
}
