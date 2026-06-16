import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  MessageSquareText,
  UserPlus,
  Receipt,
  CreditCard,
  LogOut,
  Menu,
  X,
  HelpCircle,
  QrCode,
  BarChart3,
  Users,
  Home,
  MoreHorizontal,
  Wrench,
} from 'lucide-react';

const allNavItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inquiries', icon: MessageSquareText, label: 'Inquiries' },
  { to: '/qr-inquiry', icon: QrCode, label: 'QR Inquiry' },
  { to: '/onboarding', icon: UserPlus, label: 'Onboarding' },
  { to: '/residents', icon: Users, label: 'Residents' },
  { to: '/moveins', icon: Home, label: 'Move-ins' },
  { to: '/billing', icon: Receipt, label: 'Billing' },
  { to: '/payments', icon: CreditCard, label: 'Payments' },
  { to: '/moveouts', icon: LogOut, label: 'Move-Outs' },
  { to: '/service-requests', icon: Wrench, label: 'Service Requests' },
  { to: '/miscellaneous', icon: MoreHorizontal, label: 'Miscellaneous' },
  { to: '/monitoring', icon: BarChart3, label: 'Monitoring' },
  { to: '/faq', icon: HelpCircle, label: 'FAQ' },
];

export default function Sidebar({ isOpen, onToggle }) {
  const { staff } = useAuth();
  const isAdmin = staff?.role === 'manager' || staff?.role === 'admin';

  const navItems = allNavItems.filter((item) => {
    if (item.to === '/residents' || item.to === '/moveins' || item.to === '/miscellaneous') {
      return true; // All authenticated users can see these
    }
    return true;
  });

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={onToggle} />
      )}

      {/* Mobile hamburger */}
      <button
        onClick={onToggle}
        className="fixed top-4 left-4 z-50 lg:hidden p-2 rounded-md bg-brand-navy text-white shadow-lg"
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-48 bg-brand-navy z-40 transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Branding */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-brand-navy-light">
          <img src="/logo.png" alt="DormTel" className="w-10 h-10 rounded-lg" />
          <div>
            <h1 className="text-white font-bold text-lg leading-tight">DormTel</h1>
            <p className="text-brand-gold text-xs">My Dorm My Home</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="mt-4 px-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => window.innerWidth < 1024 && onToggle()}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-gold text-brand-navy'
                    : 'text-gray-300 hover:bg-brand-navy-light hover:text-white'
                }`
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-brand-navy-light">
          <p className="text-xs text-gray-400 text-center">DormTel Automation v1.0</p>
        </div>
      </aside>
    </>
  );
}
