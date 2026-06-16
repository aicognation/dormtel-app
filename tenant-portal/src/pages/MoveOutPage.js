import React, { useState, useEffect } from 'react';
import { useTenant } from '../context/TenantContext';
import { getMoveOut, createMoveOut, getProfile, getBillings } from '../api/tenant';
import { formatDate, formatCurrency } from '../utils/formatters';
import { LogOut, Calendar, CheckCircle2, Clock, FileText, Banknote, ArrowRight, Printer } from 'lucide-react';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Button from '../components/ui/Button';
import toast from 'react-hot-toast';

const reasons = [
  'Graduating',
  'Relocating',
  'End of employment',
  'Transferring to another dorm',
  'Personal reasons',
  'Other',
];

const steps = [
  { key: 'requested', label: 'Requested', icon: Clock },
  { key: 'clearance', label: 'Clearance', icon: CheckCircle2 },
  { key: 'final_billing', label: 'Final Billing', icon: FileText },
  { key: 'refund_pending', label: 'Refund', icon: Banknote },
  { key: 'completed', label: 'Complete', icon: CheckCircle2 },
];

function calculateLengthOfStay(moveInDate, moveOutDate) {
  if (!moveInDate) return '-';
  const start = new Date(moveInDate);
  const end = moveOutDate ? new Date(moveOutDate) : new Date();
  if (end < start) return '-';
  let months = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
  if (end.getDate() < start.getDate()) months -= 1;
  if (months < 0) months = 0;
  const y = Math.floor(months / 12);
  const m = months % 12;
  if (y > 0 && m > 0) return `${y} year${y !== 1 ? 's' : ''}, ${m} month${m !== 1 ? 's' : ''}`;
  if (y > 0) return `${y} year${y !== 1 ? 's' : ''}`;
  return `${m} month${m !== 1 ? 's' : ''}`;
}

function getLast6Months() {
  const months = [];
  const now = new Date();
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    months.push(d.toLocaleDateString('en-PH', { year: 'numeric', month: 'short' }));
  }
  return months;
}

export default function MoveOutPage() {
  const { tenant } = useTenant();
  const [moveout, setMoveout] = useState(null);
  const [profile, setProfile] = useState(null);
  const [billings, setBillings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ requested_date: '', reason: '', forwarding_contact: '' });
  const [submitting, setSubmitting] = useState(false);

  // Clearance form state
  const [clearanceForm, setClearanceForm] = useState({
    keycardReturned: false,
    remoteReturned: false,
    roomOccupied: false,
    refundType: 'pickup',
    ledger: getLast6Months().map((month) => ({ month, rent: '', electric: '', water: '', others: '', total: '' })),
    securityDeposit: '',
    utilityDeposit: '',
    lessDeductions: '',
    totalRefund: '',
    refundMethod: 'pickup',
    bankName: '',
    bankAccountName: '',
    bankAccountNumber: '',
    authorized: false,
    address: '',
    phone: '',
    email: '',
    tenantSignatureDate: '',
    adminSignatureDate: '',
    dmSignatureDate: '',
  });

  useEffect(() => {
    Promise.all([
      getMoveOut(tenant.id).then(({ data }) => setMoveout(data)).catch(() => {}),
      getProfile(tenant.id).then(({ data }) => {
        setProfile(data);
        setClearanceForm((prev) => ({
          ...prev,
          securityDeposit: data.deposit_paid ? String(data.deposit_paid) : '',
          phone: data.phone || '',
          email: data.email || '',
        }));
      }).catch(() => {}),
      getBillings(tenant.id).then(({ data }) => {
        if (Array.isArray(data) && data.length > 0) {
          setBillings(data);
          const mapped = data.slice(0, 6).map((b) => ({
            month: b.period || formatDate(b.due_date),
            rent: b.rent_amount ? String(b.rent_amount) : '',
            electric: b.electric_amount ? String(b.electric_amount) : '',
            water: b.water_amount ? String(b.water_amount) : '',
            others: b.other_amount ? String(b.other_amount) : '',
            total: b.total_amount ? String(b.total_amount) : '',
          }));
          // Pad to 6 rows if fewer
          while (mapped.length < 6) {
            mapped.push({ month: '', rent: '', electric: '', water: '', others: '', total: '' });
          }
          setClearanceForm((prev) => ({ ...prev, ledger: mapped }));
        }
      }).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [tenant.id]);

  const handleClearanceChange = (field, value) => {
    setClearanceForm((prev) => {
      const next = { ...prev, [field]: value };
      // Auto-calculate total refund
      if (field === 'securityDeposit' || field === 'utilityDeposit' || field === 'lessDeductions') {
        const sec = parseFloat(next.securityDeposit) || 0;
        const util = parseFloat(next.utilityDeposit) || 0;
        const ded = parseFloat(next.lessDeductions) || 0;
        next.totalRefund = String((sec + util - ded).toFixed(2));
      }
      return next;
    });
  };

  const handleLedgerChange = (index, field, value) => {
    setClearanceForm((prev) => {
      const ledger = prev.ledger.map((row, i) => (i === index ? { ...row, [field]: value } : row));
      // Auto-calculate row total
      if (field !== 'total' && field !== 'month') {
        const row = ledger[index];
        const rent = parseFloat(row.rent) || 0;
        const electric = parseFloat(row.electric) || 0;
        const water = parseFloat(row.water) || 0;
        const others = parseFloat(row.others) || 0;
        ledger[index] = { ...row, total: String((rent + electric + water + others).toFixed(2)) };
      }
      return { ...prev, ledger };
    });
  };

  const handleSubmit = async () => {
    if (!form.requested_date) {
      toast.error('Please select a move-out date');
      return;
    }
    setSubmitting(true);
    try {
      const { data } = await createMoveOut(tenant.id, {
        resident_id: tenant.id,
        ...form,
      });
      setMoveout(data);
      setShowForm(false);
      toast.success('Move-out request submitted');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const showClearance = moveout && (moveout.status === 'requested' || moveout.status === 'clearance');
  const lengthOfStay = calculateLengthOfStay(profile?.move_in_date, moveout?.requested_date);

  if (loading) return <LoadingSpinner />;

  // Status tracker view
  if (moveout) {
    const currentIdx = steps.findIndex((s) => s.key === moveout.status);
    return (
      <div className="space-y-4 moveout-page">
        <style>{`
          @media print {
            .moveout-page { max-width: 100% !important; padding: 0 !important; }
            .no-print { display: none !important; }
            .print-only { display: block !important; }
            .clearance-card { box-shadow: none !important; border: 1px solid #ddd !important; border-radius: 0 !important; }
            body { background: white !important; }
            input, select, textarea { border: none !important; background: transparent !important; }
            input[type="checkbox"], input[type="radio"] { -webkit-appearance: auto !important; accent-color: #1a2744; }
            .print-signature-line { border-bottom: 1px solid #000 !important; min-height: 40px !important; }
            .print-table th, .print-table td { border: 1px solid #333 !important; padding: 6px 8px !important; }
          }
          .print-only { display: none; }
        `}</style>

        <div className="flex items-center justify-between no-print">
          <h2 className="text-lg font-bold text-gray-900">My Moving-out</h2>
        </div>

        {/* Print header */}
        <div className="print-only mb-6">
          <h1 className="text-2xl font-bold text-center text-gray-900 mb-2">MOVE-OUT CLEARANCE FORM</h1>
          <p className="text-center text-sm text-gray-600">DormTel Management</p>
        </div>

        <div className="bg-white rounded-2xl p-5 shadow-sm no-print">
          {/* Stepper */}
          <div className="flex items-center justify-between mb-6">
            {steps.map((step, i) => {
              const Icon = step.icon;
              const isCompleted = i <= currentIdx;
              const isCurrent = i === currentIdx;
              return (
                <React.Fragment key={step.key}>
                  <div className="flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      isCompleted ? 'bg-brand-navy text-white' :
                      'bg-gray-100 text-gray-400'
                    } ${isCurrent ? 'ring-2 ring-brand-gold ring-offset-2' : ''}`}>
                      <Icon size={18} />
                    </div>
                    <span className={`text-[9px] mt-1 text-center leading-tight ${
                      isCompleted ? 'font-semibold text-brand-navy' : 'text-gray-400'
                    }`}>{step.label}</span>
                  </div>
                  {i < steps.length - 1 && (
                    <ArrowRight size={14} className={`-mt-4 ${i < currentIdx ? 'text-brand-navy' : 'text-gray-200'}`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Details */}
          <div className="space-y-3 border-t pt-4">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Requested Date</span>
              <span className="font-semibold">{formatDate(moveout.requested_date)}</span>
            </div>
            {moveout.reason && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Reason</span>
                <span className="font-semibold">{moveout.reason}</span>
              </div>
            )}
            {moveout.forwarding_contact && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Forwarding Contact</span>
                <span className="font-semibold">{moveout.forwarding_contact}</span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Submitted</span>
              <span className="font-semibold">{formatDate(moveout.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Clearance Form */}
        {showClearance && (
          <div className="bg-white rounded-2xl p-5 shadow-sm space-y-6 clearance-card">
            <div className="flex items-center justify-between no-print">
              <h3 className="font-bold text-gray-900 flex items-center gap-2">
                <FileText size={18} className="text-brand-navy" />
                Clearance Form
              </h3>
              <Button variant="secondary" className="text-sm" onClick={handlePrint}>
                <Printer size={14} className="mr-1" />
                Print Form
              </Button>
            </div>

            {/* Tenant Information */}
            <div>
              <h4 className="text-sm font-bold text-brand-navy uppercase tracking-wider mb-3 border-b pb-1">Tenant Information</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Tenant's Name</label>
                  <input
                    type="text"
                    value={profile?.full_name || tenant?.full_name || ''}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-700"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Unit & Bed</label>
                  <input
                    type="text"
                    value={`${profile?.room_number || tenant?.room_number || ''} - Bed ${profile?.bed_number || ''}`}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-700"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Length of Stay</label>
                  <input
                    type="text"
                    value={lengthOfStay}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-700"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Rate</label>
                  <input
                    type="text"
                    value={formatCurrency(profile?.monthly_rate || tenant?.monthly_rate)}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-700"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Move-In Date</label>
                  <input
                    type="text"
                    value={formatDate(profile?.move_in_date)}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-700"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Move-Out Date</label>
                  <input
                    type="text"
                    value={formatDate(moveout.requested_date)}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-700"
                  />
                </div>
              </div>
            </div>

            {/* Checklist */}
            <div>
              <h4 className="text-sm font-bold text-brand-navy uppercase tracking-wider mb-3 border-b pb-1">Return Checklist</h4>
              <div className="space-y-2 text-sm">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={clearanceForm.keycardReturned}
                    onChange={(e) => handleClearanceChange('keycardReturned', e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-brand-navy focus:ring-brand-navy"
                  />
                  <span>Keycard Access returned?</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={clearanceForm.remoteReturned}
                    onChange={(e) => handleClearanceChange('remoteReturned', e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-brand-navy focus:ring-brand-navy"
                  />
                  <span>Remote Control (Air-con) returned?</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={clearanceForm.roomOccupied}
                    onChange={(e) => handleClearanceChange('roomOccupied', e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-brand-navy focus:ring-brand-navy"
                  />
                  <span>Room still occupied?</span>
                </label>
              </div>
            </div>

            {/* Refund Type */}
            <div>
              <h4 className="text-sm font-bold text-brand-navy uppercase tracking-wider mb-3 border-b pb-1">Refund For</h4>
              <div className="flex gap-6 text-sm">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="refundType"
                    value="pickup"
                    checked={clearanceForm.refundType === 'pickup'}
                    onChange={(e) => handleClearanceChange('refundType', e.target.value)}
                    className="w-4 h-4 border-gray-300 text-brand-navy focus:ring-brand-navy"
                  />
                  <span>For Pick up</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="refundType"
                    value="deposit"
                    checked={clearanceForm.refundType === 'deposit'}
                    onChange={(e) => handleClearanceChange('refundType', e.target.value)}
                    className="w-4 h-4 border-gray-300 text-brand-navy focus:ring-brand-navy"
                  />
                  <span>For Deposit</span>
                </label>
              </div>
            </div>

            {/* Ledger Section */}
            <div>
              <h4 className="text-sm font-bold text-brand-navy uppercase tracking-wider mb-3 border-b pb-1">Ledger</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm print-table">
                  <thead>
                    <tr className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                      <th className="px-3 py-2 border border-gray-200">Month</th>
                      <th className="px-3 py-2 border border-gray-200 text-right">Rent</th>
                      <th className="px-3 py-2 border border-gray-200 text-right">Electric</th>
                      <th className="px-3 py-2 border border-gray-200 text-right">Water</th>
                      <th className="px-3 py-2 border border-gray-200 text-right">Others</th>
                      <th className="px-3 py-2 border border-gray-200 text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clearanceForm.ledger.map((row, idx) => (
                      <tr key={idx}>
                        <td className="px-1 py-1 border border-gray-200">
                          <input
                            type="text"
                            value={row.month}
                            onChange={(e) => handleLedgerChange(idx, 'month', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-brand-navy"
                          />
                        </td>
                        <td className="px-1 py-1 border border-gray-200">
                          <input
                            type="number"
                            value={row.rent}
                            onChange={(e) => handleLedgerChange(idx, 'rent', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded text-right focus:outline-none focus:ring-1 focus:ring-brand-navy"
                            placeholder="0.00"
                          />
                        </td>
                        <td className="px-1 py-1 border border-gray-200">
                          <input
                            type="number"
                            value={row.electric}
                            onChange={(e) => handleLedgerChange(idx, 'electric', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded text-right focus:outline-none focus:ring-1 focus:ring-brand-navy"
                            placeholder="0.00"
                          />
                        </td>
                        <td className="px-1 py-1 border border-gray-200">
                          <input
                            type="number"
                            value={row.water}
                            onChange={(e) => handleLedgerChange(idx, 'water', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded text-right focus:outline-none focus:ring-1 focus:ring-brand-navy"
                            placeholder="0.00"
                          />
                        </td>
                        <td className="px-1 py-1 border border-gray-200">
                          <input
                            type="number"
                            value={row.others}
                            onChange={(e) => handleLedgerChange(idx, 'others', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded text-right focus:outline-none focus:ring-1 focus:ring-brand-navy"
                            placeholder="0.00"
                          />
                        </td>
                        <td className="px-1 py-1 border border-gray-200">
                          <input
                            type="number"
                            value={row.total}
                            readOnly
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded text-right bg-gray-50"
                            placeholder="0.00"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Refund Breakdown */}
            <div>
              <h4 className="text-sm font-bold text-brand-navy uppercase tracking-wider mb-3 border-b pb-1">Dormer's Refund Breakdown</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Security Deposit</label>
                  <input
                    type="number"
                    value={clearanceForm.securityDeposit}
                    onChange={(e) => handleClearanceChange('securityDeposit', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-right focus:outline-none focus:ring-2 focus:ring-brand-navy"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Utility Deposit</label>
                  <input
                    type="number"
                    value={clearanceForm.utilityDeposit}
                    onChange={(e) => handleClearanceChange('utilityDeposit', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-right focus:outline-none focus:ring-2 focus:ring-brand-navy"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Less Deductions</label>
                  <input
                    type="number"
                    value={clearanceForm.lessDeductions}
                    onChange={(e) => handleClearanceChange('lessDeductions', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-right focus:outline-none focus:ring-2 focus:ring-brand-navy"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Total Refund</label>
                  <input
                    type="number"
                    value={clearanceForm.totalRefund}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-right bg-gray-50 font-semibold"
                    placeholder="0.00"
                  />
                </div>
              </div>
            </div>

            {/* Refund Method */}
            <div>
              <h4 className="text-sm font-bold text-brand-navy uppercase tracking-wider mb-3 border-b pb-1">Refund Method</h4>
              <div className="flex gap-6 text-sm mb-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="refundMethod"
                    value="pickup"
                    checked={clearanceForm.refundMethod === 'pickup'}
                    onChange={(e) => handleClearanceChange('refundMethod', e.target.value)}
                    className="w-4 h-4 border-gray-300 text-brand-navy focus:ring-brand-navy"
                  />
                  <span>Pick-up</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="refundMethod"
                    value="bank"
                    checked={clearanceForm.refundMethod === 'bank'}
                    onChange={(e) => handleClearanceChange('refundMethod', e.target.value)}
                    className="w-4 h-4 border-gray-300 text-brand-navy focus:ring-brand-navy"
                  />
                  <span>Bank Deposit</span>
                </label>
              </div>
              {clearanceForm.refundMethod === 'bank' && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                  <div>
                    <label className="block text-xs text-gray-500 mb-0.5">Bank Name</label>
                    <input
                      type="text"
                      value={clearanceForm.bankName}
                      onChange={(e) => handleClearanceChange('bankName', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                      placeholder="e.g. BDO, BPI"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-0.5">Account Name</label>
                    <input
                      type="text"
                      value={clearanceForm.bankAccountName}
                      onChange={(e) => handleClearanceChange('bankAccountName', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                      placeholder="Account holder name"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-0.5">Account Number</label>
                    <input
                      type="text"
                      value={clearanceForm.bankAccountNumber}
                      onChange={(e) => handleClearanceChange('bankAccountNumber', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                      placeholder="Account number"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Authorization */}
            <div>
              <h4 className="text-sm font-bold text-brand-navy uppercase tracking-wider mb-3 border-b pb-1">Authorization</h4>
              <label className="flex items-start gap-2 cursor-pointer text-sm">
                <input
                  type="checkbox"
                  checked={clearanceForm.authorized}
                  onChange={(e) => handleClearanceChange('authorized', e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded border-gray-300 text-brand-navy focus:ring-brand-navy"
                />
                <span className="text-gray-600">
                  I hereby authorize DormTel Management to process my move-out and refund as indicated above.
                  I confirm that all information provided is true and correct.
                </span>
              </label>
            </div>

            {/* Contact Info */}
            <div>
              <h4 className="text-sm font-bold text-brand-navy uppercase tracking-wider mb-3 border-b pb-1">Contact Information</h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Address</label>
                  <input
                    type="text"
                    value={clearanceForm.address}
                    onChange={(e) => handleClearanceChange('address', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                    placeholder="Current address"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Phone</label>
                  <input
                    type="text"
                    value={clearanceForm.phone}
                    onChange={(e) => handleClearanceChange('phone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                    placeholder="Phone number"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Email</label>
                  <input
                    type="email"
                    value={clearanceForm.email}
                    onChange={(e) => handleClearanceChange('email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                    placeholder="Email address"
                  />
                </div>
              </div>
            </div>

            {/* Signatures */}
            <div>
              <h4 className="text-sm font-bold text-brand-navy uppercase tracking-wider mb-3 border-b pb-1">Signatures</h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Tenant's Signature</label>
                  <div className="print-signature-line border-b border-gray-300 min-h-[48px] flex items-end">
                    <span className="text-gray-300 text-xs print:hidden">Sign here</span>
                  </div>
                  <input
                    type="date"
                    value={clearanceForm.tenantSignatureDate}
                    onChange={(e) => handleClearanceChange('tenantSignatureDate', e.target.value)}
                    className="mt-2 w-full px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-brand-navy no-print"
                  />
                  <span className="hidden print:block text-xs text-gray-500 mt-1">
                    Date: {clearanceForm.tenantSignatureDate ? formatDate(clearanceForm.tenantSignatureDate) : '__________'}
                  </span>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Admin's Signature</label>
                  <div className="print-signature-line border-b border-gray-300 min-h-[48px] flex items-end">
                    <span className="text-gray-300 text-xs print:hidden">Admin sign here</span>
                  </div>
                  <input
                    type="date"
                    value={clearanceForm.adminSignatureDate}
                    onChange={(e) => handleClearanceChange('adminSignatureDate', e.target.value)}
                    className="mt-2 w-full px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-brand-navy no-print"
                  />
                  <span className="hidden print:block text-xs text-gray-500 mt-1">
                    Date: {clearanceForm.adminSignatureDate ? formatDate(clearanceForm.adminSignatureDate) : '__________'}
                  </span>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">DM's Signature</label>
                  <div className="print-signature-line border-b border-gray-300 min-h-[48px] flex items-end">
                    <span className="text-gray-300 text-xs print:hidden">DM sign here</span>
                  </div>
                  <input
                    type="date"
                    value={clearanceForm.dmSignatureDate}
                    onChange={(e) => handleClearanceChange('dmSignatureDate', e.target.value)}
                    className="mt-2 w-full px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-brand-navy no-print"
                  />
                  <span className="hidden print:block text-xs text-gray-500 mt-1">
                    Date: {clearanceForm.dmSignatureDate ? formatDate(clearanceForm.dmSignatureDate) : '__________'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Schedule form / info view
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-gray-900">My Moving-out</h2>

      {!showForm ? (
        <>
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-brand-gold/20 rounded-xl flex items-center justify-center">
                <LogOut size={24} className="text-brand-navy" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900">Ready to Move Out?</h3>
                <p className="text-xs text-gray-500">Here is what to expect</p>
              </div>
            </div>
            <div className="space-y-3 text-sm text-gray-600">
              <div className="flex items-start gap-2">
                <span className="w-5 h-5 bg-brand-navy text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">1</span>
                <p><span className="font-semibold">Submit Request</span> - Schedule your move-out date (minimum 30 days notice)</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-5 h-5 bg-brand-navy text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">2</span>
                <p><span className="font-semibold">Clearance</span> - Room inspection and key return</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-5 h-5 bg-brand-navy text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">3</span>
                <p><span className="font-semibold">Final Billing</span> - Prorated charges for your last month</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-5 h-5 bg-brand-navy text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">4</span>
                <p><span className="font-semibold">Refund</span> - Deposit refund processed within 15 business days</p>
              </div>
            </div>
          </div>
          <Button variant="accent" className="w-full" onClick={() => setShowForm(true)}>
            Schedule Move-Out
          </Button>
        </>
      ) : (
        <div className="bg-white rounded-2xl p-5 shadow-sm space-y-4">
          <h3 className="font-bold text-gray-900">Schedule Your Move-Out</h3>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Move-Out Date</label>
            <div className="relative">
              <Calendar size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="date"
                value={form.requested_date}
                onChange={(e) => setForm({ ...form, requested_date: e.target.value })}
                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Reason</label>
            <select
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy bg-white"
            >
              <option value="">Select a reason</option>
              {reasons.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Forwarding Contact</label>
            <input
              type="text"
              value={form.forwarding_contact}
              onChange={(e) => setForm({ ...form, forwarding_contact: e.target.value })}
              placeholder="Phone or email for refund"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy"
            />
          </div>

          <div className="flex gap-2">
            <Button variant="secondary" className="flex-1" onClick={() => setShowForm(false)}>Cancel</Button>
            <Button variant="accent" className="flex-1" onClick={handleSubmit} disabled={submitting}>
              {submitting ? 'Submitting...' : 'Submit'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
