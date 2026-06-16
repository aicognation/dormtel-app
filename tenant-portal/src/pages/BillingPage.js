import React, { useState, useEffect } from 'react';
import { useTenant } from '../context/TenantContext';
import { getBillings } from '../api/tenant';
import { formatCurrency, formatDate } from '../utils/formatters';
import { Receipt, Zap, Droplets, Home, ChevronDown, ChevronUp } from 'lucide-react';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import StatusBadge from '../components/ui/StatusBadge';

export default function BillingPage() {
  const { tenant } = useTenant();
  const [billings, setBillings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    getBillings(tenant.id)
      .then(({ data }) => setBillings(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenant.id]);

  if (loading) return <LoadingSpinner />;

  const current = billings[0];
  const history = billings.slice(1);

  const getNextBillingInfo = () => {
    const period = current?.billing_period;
    if (period) {
      const [year, month] = period.split('-').map(Number);
      if (year && month) {
        const next = new Date(year, month, 1);
        return {
          period: `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}`,
          dueDate: `1 ${next.toLocaleString('default', { month: 'long' })} ${next.getFullYear()}`,
        };
      }
    }
    const now = new Date();
    const next = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    return {
      period: `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}`,
      dueDate: `1 ${next.toLocaleString('default', { month: 'long' })} ${next.getFullYear()}`,
    };
  };
  const nextBilling = getNextBillingInfo();

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-gray-900">My Bills</h2>

      {/* Current Billing */}
      {current && (
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="bg-brand-navy text-white px-4 py-3 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-300">Current Period</p>
              <p className="text-lg font-bold">{current.billing_period}</p>
            </div>
            <StatusBadge status={current.status} />
          </div>
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-gray-600">
                <Home size={16} />
                <span className="text-sm">Rent</span>
              </div>
              <span className="font-semibold text-gray-900">{formatCurrency(current.rent_amount)}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-gray-600">
                <Zap size={16} />
                <span className="text-sm">Electric</span>
              </div>
              <span className="font-semibold text-gray-900">{formatCurrency(current.electric_charge)}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-gray-600">
                <Droplets size={16} />
                <span className="text-sm">Water</span>
              </div>
              <span className="font-semibold text-gray-900">{formatCurrency(current.water_charge)}</span>
            </div>
            {parseFloat(current.other_charges || 0) > 0 && (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-gray-600">
                  <Receipt size={16} />
                  <span className="text-sm">Other</span>
                </div>
                <span className="font-semibold text-gray-900">{formatCurrency(current.other_charges)}</span>
              </div>
            )}
            <div className="border-t pt-3 flex items-center justify-between">
              <span className="text-sm font-bold text-gray-900">Total</span>
              <span className="text-xl font-bold text-brand-navy">{formatCurrency(current.total_amount)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Upcoming Rental Dues */}
      {tenant?.monthly_rate > 0 && (
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-dashed border-gray-200">
          <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500">Upcoming Rental Dues</p>
              <p className="text-lg font-bold text-gray-900">{nextBilling.period}</p>
            </div>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Upcoming
            </span>
          </div>
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Monthly Rate</span>
              <span className="font-semibold text-gray-900">{formatCurrency(tenant.monthly_rate)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Due Date</span>
              <span className="font-semibold text-gray-900">{nextBilling.dueDate}</span>
            </div>
          </div>
        </div>
      )}

      {/* Billing History */}
      {history.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Billing History</h3>
          <div className="space-y-2">
            {history.map((bill) => (
              <div key={bill.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                <button
                  onClick={() => setExpanded(expanded === bill.id ? null : bill.id)}
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="text-left">
                    <p className="text-sm font-semibold text-gray-900">{bill.billing_period}</p>
                    <p className="text-xs text-gray-500">{formatDate(bill.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-900">{formatCurrency(bill.total_amount)}</span>
                    <StatusBadge status={bill.status} />
                    {expanded === bill.id ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
                  </div>
                </button>
                {expanded === bill.id && (
                  <div className="px-4 pb-3 border-t border-gray-50 space-y-2 pt-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Rent</span>
                      <span>{formatCurrency(bill.rent_amount)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Electric</span>
                      <span>{formatCurrency(bill.electric_charge)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Water</span>
                      <span>{formatCurrency(bill.water_charge)}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {billings.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <Receipt size={40} className="mx-auto mb-3 opacity-50" />
          <p className="text-sm">No billing records yet</p>
        </div>
      )}
    </div>
  );
}
