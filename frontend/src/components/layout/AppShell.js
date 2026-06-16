import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Sidebar from './Sidebar';
import { Bell, LogOut, User, ChevronDown } from 'lucide-react';

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const { staff, logout, isManager } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* Top bar */}
      <header className="lg:ml-48 bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="flex items-center justify-between px-4 sm:px-6 py-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-800">Management Portal</h2>
          </div>

          <div className="flex items-center gap-3">
            {isManager && (
              <button className="relative p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
              </button>
            )}

            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="w-8 h-8 bg-brand-navy rounded-full flex items-center justify-center text-white text-sm font-bold">
                  {staff?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <div className="hidden sm:block text-left">
                  <p className="text-sm font-medium text-gray-800 leading-tight">{staff?.full_name || 'User'}</p>
                  <p className="text-xs text-gray-500 capitalize">{staff?.role || ''}</p>
                </div>
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </button>

              {menuOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50 py-1">
                    <div className="px-4 py-2 border-b border-gray-100 sm:hidden">
                      <p className="text-sm font-medium text-gray-800">{staff?.full_name}</p>
                      <p className="text-xs text-gray-500 capitalize">{staff?.role}</p>
                    </div>
                    <button
                      onClick={() => { setMenuOpen(false); }}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <User className="w-4 h-4" />
                      Profile
                    </button>
                    <button
                      onClick={() => { setMenuOpen(false); logout(); }}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="lg:ml-48 min-h-screen">
        <div className="p-4 sm:p-5 lg:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
