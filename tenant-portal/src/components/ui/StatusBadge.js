import React from 'react';

const colors = {
  paid: 'bg-emerald-100 text-emerald-700',
  verified: 'bg-emerald-100 text-emerald-700',
  matched: 'bg-emerald-100 text-emerald-700',
  active: 'bg-emerald-100 text-emerald-700',
  resolved: 'bg-emerald-100 text-emerald-700',
  completed: 'bg-emerald-100 text-emerald-700',
  closed: 'bg-gray-100 text-gray-600',
  approved: 'bg-blue-100 text-blue-700',
  distributed: 'bg-blue-100 text-blue-700',
  acknowledged: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-amber-100 text-amber-700',
  pending: 'bg-amber-100 text-amber-700',
  pending_review: 'bg-amber-100 text-amber-700',
  submitted: 'bg-amber-100 text-amber-700',
  requested: 'bg-amber-100 text-amber-700',
  clearance: 'bg-orange-100 text-orange-700',
  final_billing: 'bg-orange-100 text-orange-700',
  refund_pending: 'bg-purple-100 text-purple-700',
  overdue: 'bg-red-100 text-red-700',
  draft: 'bg-gray-100 text-gray-600',
  unreconciled: 'bg-red-100 text-red-700',
  urgent: 'bg-red-100 text-red-700',
  important: 'bg-amber-100 text-amber-700',
  normal: 'bg-gray-100 text-gray-600',
  new: 'bg-blue-100 text-blue-700',
  responded: 'bg-emerald-100 text-emerald-700',
  escalated: 'bg-red-100 text-red-700',
  converted: 'bg-purple-100 text-purple-700',
};

export default function StatusBadge({ status }) {
  const label = (status || '').replace(/_/g, ' ');
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize ${colors[status] || 'bg-gray-100 text-gray-600'}`}>
      {label}
    </span>
  );
}
