import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AppShell from './components/layout/AppShell';
import ErrorBoundary from './components/ErrorBoundary';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import InquiriesPage from './pages/InquiriesPage';
import QrInquiryPage from './pages/QrInquiryPage';
import OnboardingPage from './pages/OnboardingPage';
import BillingPage from './pages/BillingPage';
import PaymentsPage from './pages/PaymentsPage';
import MoveOutsPage from './pages/MoveOutsPage';
import MonitoringPage from './pages/MonitoringPage';
import FaqPage from './pages/FaqPage';
import ResidentsPage from './pages/ResidentsPage';
import MoveInsPage from './pages/MoveInsPage';
import MiscellaneousPage from './pages/MiscellaneousPage';
import ServiceRequestsAdminPage from './pages/ServiceRequestsAdminPage';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-brand-navy" />
      </div>
    );
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <AppShell />
            </ErrorBoundary>
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/inquiries" element={<InquiriesPage />} />
        <Route path="/qr-inquiry" element={<QrInquiryPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/residents" element={<ResidentsPage />} />
        <Route path="/moveins" element={<MoveInsPage />} />
        <Route path="/billing" element={<BillingPage />} />
        <Route path="/payments" element={<PaymentsPage />} />
        <Route path="/moveouts" element={<MoveOutsPage />} />
        <Route path="/miscellaneous" element={<MiscellaneousPage />} />
        <Route path="/monitoring" element={<MonitoringPage />} />
        <Route path="/faq" element={<FaqPage />} />
        <Route path="/service-requests" element={<ServiceRequestsAdminPage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: { fontSize: '14px' },
            success: { iconTheme: { primary: '#16a34a', secondary: '#fff' } },
            error: { iconTheme: { primary: '#dc2626', secondary: '#fff' } },
          }}
        />
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}
