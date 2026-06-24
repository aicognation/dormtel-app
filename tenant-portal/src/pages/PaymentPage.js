import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useTenant } from '../context/TenantContext';
import { getPayments, makePayment, getBillings } from '../api/tenant';
import { formatCurrency, formatDateTime, shortUUID } from '../utils/formatters';
import { CreditCard, CheckCircle2, Smartphone, Building2, Banknote, ChevronRight, Upload, FileImage } from 'lucide-react';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import StatusBadge from '../components/ui/StatusBadge';
import Button from '../components/ui/Button';
import toast from 'react-hot-toast';

const paymentMethods = [
  { id: 'gcash', label: 'GCash', icon: Smartphone, color: 'bg-blue-500', requiresProof: false },
  { id: 'maya', label: 'Maya', icon: Smartphone, color: 'bg-green-500', requiresProof: false },
  { id: 'bank_transfer', label: 'Bank Transfer', icon: Building2, color: 'bg-purple-500', requiresProof: true },
  { id: 'cash', label: 'Cash', icon: Banknote, color: 'bg-amber-500', requiresProof: false },
];

export default function PaymentPage() {
  const { tenant } = useTenant();
  const [payments, setPayments] = useState([]);
  const [outstandingBill, setOutstandingBill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [method, setMethod] = useState('');
  const [amount, setAmount] = useState('');
  const [referenceNo, setReferenceNo] = useState('');
  const [proofFile, setProofFile] = useState(null);
  const [paying, setPaying] = useState(false);
  const [success, setSuccess] = useState(null);
  const fileInputRef = useRef(null);

  const loadData = useCallback(async () => {
    if (!tenant?.id) return;
    try {
      const [payRes, billRes] = await Promise.all([
        getPayments(tenant.id),
        getBillings(tenant.id),
      ]);
      setPayments(payRes.data);
      const unpaid = billRes.data.find((b) =>
        ['approved', 'distributed', 'overdue', 'pending_review'].includes(b.status)
      );
      if (unpaid) {
        setOutstandingBill(unpaid);
        setAmount(String(unpaid.total_amount));
      }
    } catch {} finally {
      setLoading(false);
    }
  }, [tenant?.id]);

  useEffect(() => { loadData(); }, [loadData]);

  const selectedMethod = paymentMethods.find((m) => m.id === method);

  const handlePay = async () => {
    if (!method || !amount) {
      toast.error('Select a payment method and enter amount');
      return;
    }
    if (selectedMethod?.requiresProof && !proofFile) {
      toast.error('Please upload proof of transfer');
      return;
    }
    if (!tenant?.id) return;
    setPaying(true);
    try {
      const { data } = await makePayment(tenant.id, {
        billing_id: outstandingBill?.id || null,
        amount: parseFloat(amount),
        method,
      });
      setSuccess(data);
      toast.success('Payment submitted successfully!');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Payment failed');
    } finally {
      setPaying(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('File must be under 5MB');
        return;
      }
      setProofFile(file);
    }
  };

  if (loading) return <LoadingSpinner />;

  // Success receipt screen
  if (success) {
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-2xl p-6 shadow-sm text-center">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 size={40} className="text-emerald-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-1">Payment Submitted!</h2>
          <p className="text-sm text-gray-500 mb-6">Your payment is being processed</p>

          <div className="bg-gray-50 rounded-xl p-4 text-left space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Reference</span>
              <span className="font-mono font-semibold">{shortUUID(success.gateway_ref || success.id)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Amount</span>
              <span className="font-bold text-emerald-600">{formatCurrency(success.amount)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Method</span>
              <span className="capitalize">{(success.method || '').replace('_', ' ')}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Date</span>
              <span>{formatDateTime(success.created_at)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Status</span>
              <StatusBadge status={success.status} />
            </div>
          </div>
        </div>

        <Button variant="accent" className="w-full" onClick={() => setSuccess(null)}>
          Make Another Payment
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-gray-900">My Payments</h2>

      {/* Outstanding Amount */}
      {outstandingBill && (
        <div className="bg-white rounded-2xl p-4 shadow-sm border-l-4 border-brand-navy">
          <p className="text-xs text-gray-500 mb-1">Outstanding Amount ({outstandingBill.billing_period})</p>
          <p className="text-2xl font-bold text-brand-navy">{formatCurrency(outstandingBill.total_amount)}</p>
        </div>
      )}

      {/* Payment Method Selector */}
      <div>
        <p className="text-sm font-semibold text-gray-700 mb-2">Payment Method</p>
        <div className="grid grid-cols-2 gap-2">
          {paymentMethods.map(({ id, label, icon: Icon, color }) => (
            <button
              key={id}
              onClick={() => { setMethod(id); setProofFile(null); setReferenceNo(''); }}
              className={`flex items-center gap-3 p-3 rounded-xl border-2 transition-all ${
                method === id
                  ? 'border-brand-navy bg-brand-navy/5'
                  : 'border-gray-100 bg-white hover:border-gray-200'
              }`}
            >
              <div className={`w-8 h-8 ${color} rounded-lg flex items-center justify-center`}>
                <Icon size={16} className="text-white" />
              </div>
              <span className={`text-sm ${method === id ? 'font-bold text-brand-navy' : 'text-gray-700'}`}>
                {label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Amount Input */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">Amount (PHP)</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full px-4 py-3 border border-gray-200 rounded-xl text-lg font-bold focus:outline-none focus:ring-2 focus:ring-brand-navy"
          placeholder="0.00"
        />
      </div>

      {/* Reference Number (for GCash/Maya/Bank) */}
      {selectedMethod && selectedMethod.id !== 'cash' && (
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Reference Number</label>
          <input
            type="text"
            value={referenceNo}
            onChange={(e) => setReferenceNo(e.target.value)}
            placeholder="Transaction reference number"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy"
          />
        </div>
      )}

      {/* Proof Upload (for Bank Transfer) */}
      {selectedMethod?.requiresProof && (
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Proof of Transfer</label>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,.pdf"
            className="hidden"
            onChange={handleFileChange}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed rounded-xl transition-all ${
              proofFile ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-gray-300'
            }`}
          >
            {proofFile ? <FileImage size={18} /> : <Upload size={18} />}
            <span className="text-sm font-medium">
              {proofFile ? proofFile.name : 'Tap to upload screenshot or PDF'}
            </span>
          </button>
          <p className="text-[10px] text-gray-400 mt-1">Max file size: 5MB</p>
        </div>
      )}

      <Button variant="accent" className="w-full text-base py-3" onClick={handlePay} disabled={paying}>
        {paying ? 'Processing...' : `Pay ${amount ? formatCurrency(amount) : ''}`}
      </Button>

      {/* Payment History */}
      {payments.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Payment History</h3>
          <div className="space-y-2">
            {payments.map((p) => (
              <div key={p.id} className="bg-white rounded-xl p-3 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{formatCurrency(p.amount)}</p>
                  <p className="text-xs text-gray-500 capitalize">{(p.method || '').replace('_', ' ')} · {formatDateTime(p.created_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={p.status} />
                  <ChevronRight size={14} className="text-gray-300" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
