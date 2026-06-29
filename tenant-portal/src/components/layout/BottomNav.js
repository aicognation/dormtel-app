import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Receipt, CreditCard, Wrench, Menu } from 'lucide-react';

const tabs = [
  { path: '/tenant', icon: LayoutDashboard, label: 'Home' },
  { path: '/tenant/bills', icon: Receipt, label: 'My Bills' },
  { path: '/tenant/pay', icon: CreditCard, label: 'Pay' },
  { path: '/tenant/requests', icon: Wrench, label: 'My Requests' },
  { path: '/tenant/profile', icon: Menu, label: 'More' },
];

export default function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => {
    if (path === '/tenant') return location.pathname === '/tenant';
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50">
      <div className="max-w-lg mx-auto flex">
        {tabs.map(({ path, icon: Icon, label }) => (
          <button
            key={path}
            onClick={() => navigate(path)}
            className={`flex-1 flex flex-col items-center py-2.5 px-1 transition-colors min-h-[48px] ${
              isActive(path)
                ? 'text-brand-navy'
                : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            <Icon size={20} strokeWidth={isActive(path) ? 2.5 : 1.5} />
            <span className={`text-xs mt-0.5 ${isActive(path) ? 'font-bold' : ''}`}>
              {label}
            </span>
          </button>
        ))}
      </div>
    </nav>
  );
}
