import React, { useEffect, useState, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import {
  RefreshCw, Link2, TrendingUp, ArrowRightLeft,
  Search, Printer, Eye, CreditCard, AlertCircle, CheckCircle2,
  FileText
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import FormField from '../components/ui/FormField';
import StatusBadge from '../components/ui/StatusBadge';
import {
  getDSR, getUnmatched, reconcilePayments, matchPayment,
  getDormerLedger, getAllLedgers,
} from '../api/payments';
import { formatCurrency, formatDate, shortUUID } from '../utils/formatters';
import { useProperty } from '../contexts/PropertyContext';

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'paid', label: 'Paid' },
  { value: 'partial', label: 'Partial' },
  { value: 'unpaid', label: 'Unpaid' },
  { value: 'no_bills', label: 'No Bills' },
];

const STATUS_COLORS = {
  paid: 'bg-green-100 text-green-700',
  partial: 'bg-yellow-100 text-yellow-700',
  unpaid: 'bg-red-100 text-red-700',
  no_bills: 'bg-gray-100 text-gray-600',
};

const STATUS_LABELS = {
  paid: 'Paid',
  partial: 'Partial',
  unpaid: 'Unpaid',
  no_bills: 'No Bills',
};

export default function PaymentsPage() {
  const { propertyCode } = useProperty();
  const [tab, setTab] = useState('reconciliation');

  // Reconciliation tab state
  const [dsr, setDsr] = useState(null);
  const [unmatched, setUnmatched] = useState([]);
  const [recLoading, setRecLoading] = useState(true);
  const [showMatch, setShowMatch] = useState(false);
  const [matchTarget, setMatchTarget] = useState(null);
  const [matchForm, setMatchForm] = useState({ resident_id: '', billing_id: '' });
  const [submitting, setSubmitting] = useState(false);

  // Ledgers tab state
  const [ledgers, setLedgers] = useState([]);
  const [ledgersLoading, setLedgersLoading] = useState(false);
  const [ledgerSearch, setLedgerSearch] = useState('');
  const [ledgerStatus, setLedgerStatus] = useState('');
  const [showLedgerModal, setShowLedgerModal] = useState(false);
  const [ledgerData, setLedgerData] = useState(null);
  const [ledgerLoading, setLedgerLoading] = useState(false);

  const printRef = useRef(null);

  const fetchRecData = useCallback(async () => {
    setRecLoading(true);
    try {
      const [dsrResult, unmatchedResult] = await Promise.allSettled([getDSR(), getUnmatched()]);
      if (dsrResult.status === 'fulfilled') setDsr(dsrResult.value);
      if (unmatchedResult.status === 'fulfilled') {
        setUnmatched(Array.isArray(unmatchedResult.value) ? unmatchedResult.value : []);
      }
    } catch {
      toast.error('Failed to load reconciliation data');
      setUnmatched([]);
    } finally {
      setRecLoading(false);
    }
  }, [propertyCode]);

  const fetchLedgers = useCallback(async () => {
    setLedgersLoading(true);
    try {
      const params = {};
      if (ledgerSearch) params.search = ledgerSearch;
      if (ledgerStatus) params.status = ledgerStatus;
      const result = await getAllLedgers(params);
      setLedgers(Array.isArray(result) ? result : []);
    } catch {
      toast.error('Failed to load ledgers');
      setLedgers([]);
    } finally {
      setLedgersLoading(false);
    }
  }, [ledgerSearch, ledgerStatus, propertyCode]);

  useEffect(() => { fetchRecData(); }, [fetchRecData]);

  useEffect(() => {
    if (tab === 'ledgers') {
      fetchLedgers();
    }
  }, [tab, fetchLedgers]);

  const handleReconcile = async () => {
    setSubmitting(true);
    try {
      const result = await reconcilePayments();
      toast.success(`Reconciled ${result?.reconciled_count ?? 0} payment(s)`);
      fetchRecData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to reconcile payments';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleMatch = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await matchPayment(matchTarget.id, matchForm);
      toast.success('Payment matched successfully');
      setShowMatch(false);
      setMatchTarget(null);
      setMatchForm({ resident_id: '', billing_id: '' });
      fetchRecData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to match payment';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const openLedger = async (residentId) => {
    setLedgerLoading(true);
    setShowLedgerModal(true);
    try {
      const result = await getDormerLedger(residentId);
      setLedgerData(result);
    } catch {
      toast.error('Failed to load ledger');
      setShowLedgerModal(false);
    } finally {
      setLedgerLoading(false);
    }
  };

  const handlePrint = () => {
    if (!printRef.current) return;
    const printContents = printRef.current.innerHTML;
    const printWindow = window.open('', '_blank', 'width=900,height=700');
    printWindow.document.write(`
      <html>
        <head>
          <title>Dormer Ledger</title>
          <style>
            body { font-family: Arial, sans-serif; font-size: 12px; color: #333; margin: 20px; }
            h2 { font-size: 16px; margin-bottom: 4px; }
            h3 { font-size: 13px; margin-top: 16px; margin-bottom: 6px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
            .header-row { display: flex; justify-content: space-between; margin-bottom: 16px; }
            .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 24px; margin-bottom: 12px; }
            .info-grid div { display: flex; justify-content: space-between; }
            .info-grid .label { color: #666; }
            .info-grid .value { font-weight: 600; }
            table { width: 100%; border-collapse: collapse; margin-top: 6px; }
            th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }
            th { background: #f5f5f5; font-weight: 600; }
            .text-right { text-align: right; }
            .text-center { text-align: center; }
            .summary { margin-top: 12px; display: flex; gap: 24px; font-weight: 600; }
            .footer { margin-top: 24px; display: flex; justify-content: space-between; font-size: 11px; color: #666; }
            @media print { body { margin: 0; } }
          </style>
        </head>
        <body>
          ${printContents}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
  };

  const unmatchedColumns = [
    { key: 'amount', label: 'Amount', render: (r) => <span className="font-bold">{formatCurrency(r.amount)}</span> },
    { key: 'method', label: 'Method', render: (r) => <span className="capitalize">{r.method}</span> },
    { key: 'gateway_ref', label: 'Gateway Ref', render: (r) => r.gateway_ref || '—' },
    { key: 'resident_id', label: 'Resident', render: (r) => shortUUID(r.resident_id) },
    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'created_at', label: 'Date', render: (r) => formatDate(r.created_at) },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        <Button size="sm" variant="primary" onClick={(e) => { e.stopPropagation(); setMatchTarget(r); setShowMatch(true); }}>
          <Link2 className="w-3 h-3 mr-1" /> Match
        </Button>
      ),
    },
  ];

  const ledgerColumns = [
    {
      key: 'resident_name',
      label: 'Dormer',
      render: (r) => (
        <div className="flex flex-col">
          <span className="font-medium">{r.resident_name}</span>
          <span className="text-xs text-gray-500">{r.room_number} {r.bed_code ? `(${r.bed_code})` : ''}</span>
        </div>
      ),
    },
    { key: 'monthly_rate', label: 'Rate', render: (r) => formatCurrency(r.monthly_rate) },
    {
      key: 'total_billed',
      label: 'Total Billed',
      render: (r) => <span className="font-medium">{formatCurrency(r.total_billed)}</span>,
    },
    {
      key: 'total_paid',
      label: 'Total Paid',
      render: (r) => <span className="text-green-600 font-medium">{formatCurrency(r.total_paid)}</span>,
    },
    {
      key: 'balance_due',
      label: 'Balance Due',
      render: (r) => (
        <span className={`font-bold ${r.balance_due > 0 ? 'text-red-600' : 'text-gray-400'}`}>
          {formatCurrency(r.balance_due)}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (r) => (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[r.status] || 'bg-gray-100 text-gray-600'}`}>
          {STATUS_LABELS[r.status] || r.status}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); openLedger(r.resident_id); }}>
            <Eye className="w-3 h-3 mr-1" /> View
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Payment Gateway & Reconciliation"
        subtitle="Daily sales, unmatched payments, dormer ledgers, and reconciliation"
        actions={
          <Button variant="accent" onClick={handleReconcile} loading={submitting}>
            <ArrowRightLeft className="w-4 h-4 mr-1" /> Reconcile All
          </Button>
        }
      />

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-4">
        {[
          { key: 'reconciliation', label: 'Reconciliation' },
          { key: 'ledgers', label: 'Dormer Ledgers' },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Reconciliation Tab */}
      {tab === 'reconciliation' && (
        <div className="space-y-6">
          {/* DSR Card */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-5 h-5 text-brand-navy" />
              <h3 className="text-sm font-semibold text-gray-600 uppercase">Daily Sales Report</h3>
            </div>
            {dsr ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-3">
                <div>
                  <p className="text-xs text-gray-500">Date</p>
                  <p className="text-lg font-semibold">{formatDate(dsr.date)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Total Revenue</p>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(dsr.total_amount)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Transactions</p>
                  <p className="text-lg font-semibold">{dsr.total_transactions}</p>
                </div>
              </div>
            ) : (
              <p className="text-gray-400 text-sm mt-2">Loading...</p>
            )}
          </div>

          {/* Unmatched Payments */}
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-800">Unmatched Payments</h3>
            <Button variant="ghost" onClick={fetchRecData}><RefreshCw className="w-4 h-4" /></Button>
          </div>
          <DataTable columns={unmatchedColumns} data={unmatched} loading={recLoading} emptyMessage="No unmatched payments" />
        </div>
      )}

      {/* Ledgers Tab */}
      {tab === 'ledgers' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3 items-end">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search dormer, room, bed..."
                value={ledgerSearch}
                onChange={(e) => setLedgerSearch(e.target.value)}
                className="rounded-md border border-gray-300 pl-9 pr-3 py-2 text-sm w-64"
              />
            </div>
            <select
              value={ledgerStatus}
              onChange={(e) => setLedgerStatus(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
            <Button variant="secondary" onClick={fetchLedgers}>
              <RefreshCw className="w-4 h-4 mr-1" /> Refresh
            </Button>
          </div>

          <DataTable
            columns={ledgerColumns}
            data={ledgers}
            loading={ledgersLoading}
            emptyMessage="No dormer ledgers found"
          />
        </div>
      )}

      {/* Ledger Detail Modal */}
      <Modal
        isOpen={showLedgerModal}
        onClose={() => { setShowLedgerModal(false); setLedgerData(null); }}
        title="Dormer Ledger"
        size="xl"
      >
        {ledgerLoading ? (
          <div className="text-center py-8 text-gray-500">Loading ledger...</div>
        ) : ledgerData ? (
          <div className="space-y-4">
            {/* Print Button */}
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={handlePrint}>
                <Printer className="w-4 h-4 mr-1" /> Print Ledger
              </Button>
            </div>

            {/* Printable Content */}
            <div ref={printRef} className="space-y-4">
              {/* Header */}
              <div className="header-row">
                <div>
                  <h2 className="text-lg font-bold">DORMER'S LEDGER</h2>
                  <p className="text-sm text-gray-500">DormTel Management Portal</p>
                </div>
                <div className="text-right text-sm text-gray-500">
                  <p>Printed: {new Date().toLocaleDateString()}</p>
                </div>
              </div>

              {/* Resident Info */}
              <div className="bg-gray-50 rounded-md p-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-gray-500">Dormer's Name</p>
                    <p className="font-semibold">{ledgerData.resident_name}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Room Number</p>
                    <p className="font-semibold">{ledgerData.room_number || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Bed</p>
                    <p className="font-semibold">{ledgerData.bed_letter || ledgerData.bed_code || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Rate</p>
                    <p className="font-semibold">{formatCurrency(ledgerData.monthly_rate)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Room Type</p>
                    <p className="font-semibold">{ledgerData.room_type || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Bed Type</p>
                    <p className="font-semibold capitalize">{ledgerData.bed_type ? ledgerData.bed_type.replace(/_/g, ' ') : '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Move-In Date</p>
                    <p className="font-semibold">{ledgerData.move_in_date ? formatDate(ledgerData.move_in_date) : '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Move-Out Date</p>
                    <p className="font-semibold">{ledgerData.move_out_date ? formatDate(ledgerData.move_out_date) : '—'}</p>
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-white border rounded-md p-3 text-center">
                  <p className="text-xs text-gray-500">Total Billed</p>
                  <p className="text-lg font-bold">{formatCurrency(ledgerData.total_billed)}</p>
                </div>
                <div className="bg-white border rounded-md p-3 text-center">
                  <p className="text-xs text-gray-500">Total Paid</p>
                  <p className="text-lg font-bold text-green-600">{formatCurrency(ledgerData.total_paid)}</p>
                </div>
                <div className="bg-white border rounded-md p-3 text-center">
                  <p className="text-xs text-gray-500">Balance Due</p>
                  <p className={`text-lg font-bold ${ledgerData.balance_due > 0 ? 'text-red-600' : 'text-gray-400'}`}>
                    {formatCurrency(ledgerData.balance_due)}
                  </p>
                </div>
              </div>

              {/* Payment Ledger */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <CreditCard className="w-4 h-4" /> Payment Ledger
                </h3>
                {ledgerData.payments.length === 0 ? (
                  <p className="text-sm text-gray-400 py-2">No payments recorded.</p>
                ) : (
                  <div className="overflow-x-auto border rounded-md">
                    <table className="min-w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">Date Paid</th>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">Method</th>
                          <th className="px-3 py-2 text-right font-medium text-gray-700">Amount</th>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">OR/PR No.</th>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">Gateway Ref</th>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {ledgerData.payments.map((p) => (
                          <tr key={p.id}>
                            <td className="px-3 py-2">{formatDate(p.created_at)}</td>
                            <td className="px-3 py-2 capitalize">{p.method}</td>
                            <td className="px-3 py-2 text-right font-medium">{formatCurrency(p.amount)}</td>
                            <td className="px-3 py-2">{p.receipt_no || p.sales_invoice_no || '—'}</td>
                            <td className="px-3 py-2 text-xs">{p.gateway_ref || '—'}</td>
                            <td className="px-3 py-2"><StatusBadge status={p.status} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Billing Breakdown */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <FileText className="w-4 h-4" /> Monthly Billing Breakdown
                </h3>
                {ledgerData.billings.length === 0 ? (
                  <p className="text-sm text-gray-400 py-2">No billings generated.</p>
                ) : (
                  <div className="overflow-x-auto border rounded-md">
                    <table className="min-w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">Period</th>
                          <th className="px-3 py-2 text-right font-medium text-gray-700">Rent</th>
                          <th className="px-3 py-2 text-right font-medium text-gray-700">Electric</th>
                          <th className="px-3 py-2 text-right font-medium text-gray-700">Water</th>
                          <th className="px-3 py-2 text-right font-medium text-gray-700">Others</th>
                          <th className="px-3 py-2 text-right font-medium text-gray-700">Total</th>
                          <th className="px-3 py-2 text-right font-medium text-gray-700">Paid</th>
                          <th className="px-3 py-2 text-right font-medium text-gray-700">Balance</th>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {ledgerData.billings.map((b) => (
                          <tr key={b.id} className={b.balance_due > 0 ? 'bg-red-50' : ''}>
                            <td className="px-3 py-2 font-medium">{b.billing_period}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(b.rent_amount)}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(b.electric_charge)}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(b.water_charge)}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(b.other_charges)}</td>
                            <td className="px-3 py-2 text-right font-bold">{formatCurrency(b.total_amount)}</td>
                            <td className="px-3 py-2 text-right text-green-600">{formatCurrency(b.payments_total)}</td>
                            <td className="px-3 py-2 text-right">
                              <span className={b.balance_due > 0 ? 'text-red-600 font-bold' : 'text-gray-400'}>
                                {formatCurrency(b.balance_due)}
                              </span>
                            </td>
                            <td className="px-3 py-2"><StatusBadge status={b.status} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Unpaid Alert */}
              {ledgerData.balance_due > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3 flex items-center gap-2 text-red-700">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    Outstanding balance of {formatCurrency(ledgerData.balance_due)} is still unpaid.
                  </span>
                </div>
              )}
              {ledgerData.balance_due <= 0 && ledgerData.total_billed > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-md p-3 flex items-center gap-2 text-green-700">
                  <CheckCircle2 className="w-4 h-4" />
                  <span className="text-sm font-medium">All bills are fully paid.</span>
                </div>
              )}

              {/* Print-only footer */}
              <div className="hidden print-footer">
                <div className="footer">
                  <div>
                    <p>Prepared By:</p>
                    <p className="mt-6 border-t border-gray-400 w-32">Admin Assistant</p>
                  </div>
                  <div>
                    <p>Checked By:</p>
                    <p className="mt-6 border-t border-gray-400 w-32">Dorm Manager</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No ledger data available.</div>
        )}
      </Modal>

      {/* Match Modal */}
      <Modal isOpen={showMatch} onClose={() => { setShowMatch(false); setMatchTarget(null); }} title="Match Payment">
        {matchTarget && (
          <form onSubmit={handleMatch} className="space-y-4">
            <p className="text-sm text-gray-600">
              Matching payment of <strong>{formatCurrency(matchTarget.amount)}</strong> via {matchTarget.method}
            </p>
            <FormField label="Resident ID" name="resident_id" required value={matchForm.resident_id}
              onChange={(e) => setMatchForm({ ...matchForm, resident_id: e.target.value })}
              placeholder="UUID of resident" />
            <FormField label="Billing ID" name="billing_id" required value={matchForm.billing_id}
              onChange={(e) => setMatchForm({ ...matchForm, billing_id: e.target.value })}
              placeholder="UUID of billing record" />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => setShowMatch(false)}>Cancel</Button>
              <Button type="submit" loading={submitting}>Match Payment</Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
