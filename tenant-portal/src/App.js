import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { TenantProvider, useTenant } from './context/TenantContext';
import TenantShell from './components/layout/TenantShell';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import BillingPage from './pages/BillingPage';
import PaymentPage from './pages/PaymentPage';
import ServiceRequestsPage from './pages/ServiceRequestsPage';
import MoveOutPage from './pages/MoveOutPage';
import InquiryPage from './pages/InquiryPage';
import ProfilePage from './pages/ProfilePage';

function ProtectedRoute({ children }) {
  const { tenant } = useTenant();
  if (!tenant) return <Navigate to="/tenant/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/tenant/login" element={<LoginPage />} />
      <Route path="/tenant" element={
        <ProtectedRoute>
          <TenantShell />
        </ProtectedRoute>
      }>
        <Route index element={<DashboardPage />} />
        <Route path="bills" element={<BillingPage />} />
        <Route path="pay" element={<PaymentPage />} />
        <Route path="payments" element={<PaymentPage />} />
        <Route path="requests" element={<ServiceRequestsPage />} />
        <Route path="inquiry" element={<InquiryPage />} />
        <Route path="moveout" element={<MoveOutPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/tenant" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <TenantProvider>
        <Toaster position="top-center" />
        <AppRoutes />
      </TenantProvider>
    </BrowserRouter>
  );
}
