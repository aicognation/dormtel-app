import React from 'react';
import { Outlet } from 'react-router-dom';
import TenantHeader from './TenantHeader';
import BottomNav from './BottomNav';

export default function TenantShell() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <TenantHeader />
      <main className="flex-1 pb-20 px-4 pt-4 max-w-lg mx-auto w-full">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
