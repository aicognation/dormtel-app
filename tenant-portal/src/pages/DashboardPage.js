import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { getDashboard } from '../api/tenant';
import { formatCurrency, formatDate } from '../utils/formatters';
import { Receipt, Wrench, CreditCard, Bell, ChevronRight, AlertTriangle, Calendar, FileCheck, MessageSquare } from 'lucide-react';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import StatusBadge from '../components/ui/StatusBadge';

export default function DashboardPage() {
  const { tenant } = useTenant();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getDashboard(tenant.id)
      .then(({ data }) => setData(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenant.id]);

  if (loading) return <LoadingSpinner />;
  if (!data) return <p className="text-center text-gray-500 py-8">Unable to load dashboard</p>;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="space-y-4">
      {/* Greeting */}
      <div className="bg-white rounded-2xl p-4 shadow-sm">
        <p className="text-sm text-gray-500">{greeting},</p>
        <h2 className="text-xl font-bold text-gray-900">{data.resident_name}</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Room {data.room_number} · {data.building} · Bed {data.bed_number}
        </p>
        <p className="text-[10px] text-brand-navy mt-1">Last updated: {new Date().toLocaleDateString('en-PH')}</p>
      </div>

      {/* Contract Status */}
      {data.months_to_end_contract !== null && data.months_to_end_contract !== undefined && (
        <div className="bg-brand-navy/5 rounded-2xl p-4 border border-brand-navy/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-navy rounded-xl flex items-center justify-center flex-shrink-0">
              <Calendar size={20} className="text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Contract Remaining</p>
              <p className="text-lg font-bold text-brand-navy">
                {data.months_to_end_contract} {data.months_to_end_contract === 1 ? 'month' : 'months'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Outstanding Balance Card */}
      <div
        className="bg-brand-navy rounded-2xl p-5 text-white shadow-lg cursor-pointer"
        onClick={() => navigate('/tenant/bills')}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-300 mb-1">Outstanding Balance</p>
            <p className="text-3xl font-bold">{formatCurrency(data.outstanding_balance)}</p>
            {data.current_billing_period && (
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-gray-300">Period: {data.current_billing_period}</span>
                <StatusBadge status={data.current_billing_status} />
              </div>
            )}
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); navigate('/tenant/pay'); }}
            className="bg-brand-gold text-brand-navy px-4 py-2 rounded-xl text-sm font-bold hover:bg-yellow-400 transition-colors"
          >
            Pay Now
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div
          className="bg-white rounded-xl p-3 shadow-sm text-center cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate('/tenant/requests')}
        >
          <Wrench size={20} className="mx-auto text-amber-500 mb-1" />
          <p className="text-xl font-bold text-gray-900">{data.open_requests}</p>
          <p className="text-[10px] text-gray-500">Open Requests</p>
        </div>
        <div
          className="bg-white rounded-xl p-3 shadow-sm text-center cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate('/tenant/pay')}
        >
          <CreditCard size={20} className="mx-auto text-emerald-500 mb-1" />
          <p className="text-sm font-bold text-gray-900">
            {data.last_payment_amount ? formatCurrency(data.last_payment_amount) : '-'}
          </p>
          <p className="text-[10px] text-gray-500">Last Payment</p>
        </div>
        <div
          className="bg-white rounded-xl p-3 shadow-sm text-center cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate('/tenant/bills')}
        >
          <Receipt size={20} className="mx-auto text-blue-500 mb-1" />
          <p className="text-sm font-bold text-gray-900">
            {data.current_billing_total ? formatCurrency(data.current_billing_total) : '-'}
          </p>
          <p className="text-[10px] text-gray-500">Current Bill</p>
        </div>
        <div
          className="bg-white rounded-xl p-3 shadow-sm text-center cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate('/tenant/payments')}
        >
          <FileCheck size={20} className="mx-auto text-purple-500 mb-1" />
          <p className="text-xl font-bold text-gray-900">{data.paid_billings_count}</p>
          <p className="text-[10px] text-gray-500">My Payments</p>
        </div>
      </div>

      {/* Billing & Requests Summary */}
      <div className="bg-white rounded-2xl p-4 shadow-sm space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">Account Summary</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-amber-50 rounded-xl p-3">
            <p className="text-xs text-amber-600 mb-0.5">Pending Bills</p>
            <p className="text-xl font-bold text-amber-700">{data.pending_billings_count}</p>
          </div>
          <div className="bg-emerald-50 rounded-xl p-3">
            <p className="text-xs text-emerald-600 mb-0.5">Paid Bills</p>
            <p className="text-xl font-bold text-emerald-700">{data.paid_billings_count}</p>
          </div>
          <div className="bg-blue-50 rounded-xl p-3">
            <p className="text-xs text-blue-600 mb-0.5">Requests Submitted</p>
            <p className="text-xl font-bold text-blue-700">{data.total_requests_submitted}</p>
          </div>
          <div className="bg-purple-50 rounded-xl p-3">
            <p className="text-xs text-purple-600 mb-0.5">Responses Received</p>
            <p className="text-xl font-bold text-purple-700">{data.total_responses_received}</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => navigate('/tenant/inquiry')}
          className="bg-white rounded-xl p-3 shadow-sm flex items-center gap-3 hover:shadow-md transition-shadow text-left"
        >
          <div className="w-10 h-10 bg-brand-navy/10 rounded-lg flex items-center justify-center flex-shrink-0">
            <MessageSquare size={18} className="text-brand-navy" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">My Inquiries</p>
            <p className="text-[10px] text-gray-500">Submit inquiry or complaint</p>
          </div>
        </button>
        <button
          onClick={() => navigate('/tenant/moveout')}
          className="bg-white rounded-xl p-3 shadow-sm flex items-center gap-3 hover:shadow-md transition-shadow text-left"
        >
          <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center flex-shrink-0">
            <Calendar size={18} className="text-red-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">My Moving-out</p>
            <p className="text-[10px] text-gray-500">Request clearance</p>
          </div>
        </button>
      </div>

      {/* Announcements */}
      {data.announcements && data.announcements.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Bell size={16} className="text-gray-500" />
            <h3 className="text-sm font-semibold text-gray-700">Announcements</h3>
          </div>
          <div className="space-y-2">
            {data.announcements.map((a) => (
              <div key={a.id} className={`bg-white rounded-xl p-3 shadow-sm border-l-4 ${
                a.priority === 'urgent' ? 'border-red-500' :
                a.priority === 'important' ? 'border-amber-500' :
                'border-blue-300'
              }`}>
                <div className="flex items-start gap-2">
                  {(a.priority === 'urgent' || a.priority === 'important') && (
                    <AlertTriangle size={14} className={a.priority === 'urgent' ? 'text-red-500' : 'text-amber-500'} />
                  )}
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-900">{a.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{a.content}</p>
                    <p className="text-[10px] text-gray-400 mt-1">{formatDate(a.published_at)}</p>
                  </div>
                  <ChevronRight size={16} className="text-gray-300 flex-shrink-0 mt-0.5" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
