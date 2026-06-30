import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProperty } from '../contexts/PropertyContext';
import {
  TrendingUp,
  MessageSquareText,
  UserPlus,
  Receipt,
  CalendarCheck,
  LogOut,
  QrCode,
  BarChart3,
  HelpCircle,
  Users,
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import Button from '../components/ui/Button';
import { getDashboardStats } from '../api/dashboard';
import { formatCurrency } from '../utils/formatters';
import ReservationsModal from '../components/dashboard/ReservationsModal';
import PendingBillsModal from '../components/dashboard/PendingBillsModal';
import CalendarModal from '../components/dashboard/CalendarModal';
import DormersModal from '../components/dashboard/DormersModal';

const PERIODS = [
  { key: 'daily', label: 'Daily' },
  { key: 'weekly', label: 'Weekly' },
  { key: 'monthly', label: 'Monthly' },
  { key: 'ytd', label: 'YTD' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { propertyCode } = useProperty();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('monthly');
  const [modal, setModal] = useState(null);

  useEffect(() => {
    async function fetchStats() {
      setLoading(true);
      try {
        const data = await getDashboardStats(period);
        setStats(data);
      } catch {
        setStats(null);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, [period, propertyCode]);

  const colorMap = {
    green: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-200' },
    blue: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-200' },
    purple: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-200' },
    yellow: { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-200' },
    red: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-200' },
    orange: { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-200' },
  };

  const statCards = [
    {
      label: 'Revenue',
      icon: TrendingUp,
      value: stats ? formatCurrency(stats.revenue) : '—',
      color: 'green',
    },
    {
      label: 'Total Dormers',
      icon: Users,
      value: stats ? stats.dormers : '—',
      color: 'blue',
      view: 'dormers',
    },
    {
      label: 'Inquiries',
      icon: MessageSquareText,
      value: stats ? stats.inquiries : '—',
      color: 'purple',
      view: 'inquiries',
    },
    {
      label: 'Reservations Received',
      icon: UserPlus,
      value: stats ? stats.reservations : '—',
      color: 'yellow',
      view: 'reservations',
    },
    {
      label: 'Pending Bills',
      icon: Receipt,
      value: stats ? formatCurrency(stats.pending_bills) : '—',
      subValue: stats ? `${stats.pending_bills_count} bill${stats.pending_bills_count !== 1 ? 's' : ''}` : '',
      color: 'red',
      view: 'pending_bills',
    },
    {
      label: 'Scheduled Move-ins',
      icon: CalendarCheck,
      value: stats ? stats.scheduled_moveins : '—',
      color: 'green',
      view: 'moveins',
    },
    {
      label: 'Scheduled Move-outs',
      icon: LogOut,
      value: stats ? stats.scheduled_moveouts : '—',
      color: 'orange',
      view: 'moveouts',
    },
  ];

  return (
    <div>
      <PageHeader
        title="Operations Dashboard"
        subtitle="DormTel Automation — Real-time overview"
      />

      {/* Period Switcher */}
      <div className="mb-6">
        <div className="inline-flex bg-gray-100 rounded-lg p-1">
          {PERIODS.map((p) => (
            <button
              key={p.key}
              onClick={() => setPeriod(p.key)}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                period === p.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
        {statCards.map((card) => (
          <div
            key={card.label}
            className={`bg-white rounded-lg border ${colorMap[card.color]?.border || 'border-gray-200'} shadow-sm p-5`}
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm text-gray-500 font-medium">{card.label}</p>
              </div>
              <div className={`p-2 rounded-lg ${colorMap[card.color]?.bg || 'bg-gray-100'}`}>
                <card.icon className={`w-5 h-5 ${colorMap[card.color]?.text || 'text-gray-600'}`} />
              </div>
            </div>
            <div>
              <p className="text-3xl font-bold text-gray-900">
                {loading ? '...' : card.value}
              </p>
              {card.subValue && (
                <p className="text-sm text-gray-500 mt-1">{card.subValue}</p>
              )}
            </div>
            {card.view && (
              <div className="mt-4 pt-3 border-t border-gray-100">
                <button
                  onClick={() => setModal(card.view)}
                  className="text-xs font-medium text-brand-navy hover:underline"
                >
                  View details →
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
        <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-4">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <Button onClick={() => navigate('/qr-inquiry')} variant="accent"><QrCode className="w-4 h-4 mr-1" /> QR Inquiry</Button>
          <Button onClick={() => navigate('/inquiries')} variant="primary">New Inquiry</Button>
          <Button onClick={() => navigate('/onboarding')} variant="primary">New Reservation</Button>
          <Button onClick={() => navigate('/billing')} variant="primary">Generate Billing</Button>
          <Button onClick={() => navigate('/payments')} variant="primary">View DSR</Button>
          <Button onClick={() => navigate('/monitoring')} variant="secondary"><BarChart3 className="w-4 h-4 mr-1" /> Monitoring</Button>
          <Button onClick={() => navigate('/faq')} variant="secondary"><HelpCircle className="w-4 h-4 mr-1" /> FAQ</Button>
        </div>
      </div>

      {/* Modals */}
      {modal === 'reservations' && (
        <ReservationsModal isOpen={true} onClose={() => setModal(null)} />
      )}
      {modal === 'inquiries' && (
        <ReservationsModal isOpen={true} onClose={() => setModal(null)} />
      )}
      {modal === 'pending_bills' && (
        <PendingBillsModal isOpen={true} onClose={() => setModal(null)} />
      )}
      {modal === 'moveins' && (
        <CalendarModal isOpen={true} onClose={() => setModal(null)} type="movein" />
      )}
      {modal === 'moveouts' && (
        <CalendarModal isOpen={true} onClose={() => setModal(null)} type="moveout" />
      )}
      {modal === 'dormers' && (
        <DormersModal isOpen={true} onClose={() => setModal(null)} />
      )}
    </div>
  );
}
