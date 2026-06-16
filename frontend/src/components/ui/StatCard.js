import React from 'react';

export default function StatCard({ label, value, icon: Icon, color = 'brand-navy' }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{label}</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
        </div>
        {Icon && (
          <div className={`p-3 rounded-lg bg-${color}/10`}>
            <Icon className={`w-6 h-6 text-${color}`} />
          </div>
        )}
      </div>
    </div>
  );
}
