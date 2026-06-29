import React from 'react';
import { useTenant } from '../../context/TenantContext';
import { Home, MapPin } from 'lucide-react';

export default function TenantHeader() {
  const { tenant } = useTenant();

  return (
    <header className="bg-brand-navy text-white px-4 py-3 shadow-lg">
      <div className="max-w-lg mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-gold rounded-lg flex items-center justify-center">
            <Home size={18} className="text-brand-navy" />
          </div>
          <div>
            <h1 className="text-sm font-bold leading-tight">DormTel</h1>
            <p className="text-[11px] text-brand-gold leading-tight">My Dorm, My Home</p>
          </div>
        </div>
        {tenant && (
          <div className="text-right">
            <p className="text-sm font-semibold leading-tight">{tenant.full_name}</p>
            <div className="flex items-center justify-end gap-1 text-[11px] text-gray-300">
              <MapPin size={10} />
              <span>{tenant.room_number} · {tenant.building}</span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
