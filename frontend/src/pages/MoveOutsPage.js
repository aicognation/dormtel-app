import React, { useEffect, useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { Plus, FileCheck, Calculator, CheckCircle2, RefreshCw, Calendar, AlertTriangle, Clock } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import FormField from '../components/ui/FormField';
import StatusBadge from '../components/ui/StatusBadge';
import { listMoveOuts, createMoveOut, generateClearance, finalizeMoveOut, completeMoveOut, extendMoveOut } from '../api/moveouts';
import { MOVEOUT_STATUSES } from '../utils/constants';
import { formatDate, formatCurrency, shortUUID, truncate } from '../utils/formatters';

export default function MoveOutsPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', resident_id: '', year: '', month: '' });
  const [showCreate, setShowCreate] = useState(false);
  const [showExtend, setShowExtend] = useState(false);
  const [extendTarget, setExtendTarget] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({ resident_id: '', requested_date: '', actual_date: '', reason: '', forwarding_contact: '' });
  const [extendForm, setExtendForm] = useState({ extended_date: '', extension_reason: '' });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.resident_id) params.resident_id = filters.resident_id;
      if (filters.year) params.year = Number(filters.year);
      if (filters.month) params.month = Number(filters.month);
      const result = await listMoveOuts(params);
      setData(result);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createMoveOut(form);
      toast.success('Move-out request created');
      setShowCreate(false);
      setForm({ resident_id: '', requested_date: '', actual_date: '', reason: '', forwarding_contact: '' });
      fetchData();
    } finally {
      setSubmitting(false);
    }
  };

  const handleClearance = async (id) => {
    try {
      await generateClearance(id);
      toast.success('Clearance generated with final billing');
      fetchData();
    } catch { /* interceptor */ }
  };

  const handleFinalize = async (id) => {
    try {
      await finalizeMoveOut(id);
      toast.success('Move-out finalized, submitted to accounting');
      fetchData();
    } catch { /* interceptor */ }
  };

  const handleComplete = async (id) => {
    try {
      await completeMoveOut(id);
      toast.success('Move-out completed');
      fetchData();
    } catch { /* interceptor */ }
  };

  const openExtend = (row) => {
    setExtendTarget(row);
    setExtendForm({ extended_date: row.requested_date || '', extension_reason: '' });
    setShowExtend(true);
  };

  const handleExtend = async (e) => {
    e.preventDefault();
    if (!extendTarget) return;
    setSubmitting(true);
    try {
      await extendMoveOut(extendTarget.id, extendForm);
      toast.success('Move-out date extended');
      setShowExtend(false);
      setExtendTarget(null);
      setExtendForm({ extended_date: '', extension_reason: '' });
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to extend move-out';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    {
      key: 'resident_name',
      label: 'Resident',
      render: (r) => (
        <div className="flex flex-col">
          <span className="font-medium">{r.resident_name || shortUUID(r.resident_id)}</span>
          {(r.room_number || r.bed_code) && (
            <span className="text-xs text-gray-500">{r.room_number} {r.bed_code ? `(${r.bed_code})` : ''}</span>
          )}
        </div>
      ),
    },
    {
      key: 'requested_date',
      label: 'Requested Date',
      render: (r) => (
        <div className="flex items-center gap-1">
          <span>{formatDate(r.requested_date)}</span>
          {r.is_end_of_month_flag && (
            <span title="End-of-month move-out" className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700">
              <AlertTriangle className="w-3 h-3 mr-0.5" /> EOM
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'actual_date',
      label: 'Actual Date',
      render: (r) => (
        <span className={r.extended_date ? 'text-blue-600 font-medium' : ''}>
          {formatDate(r.extended_date || r.actual_date || r.requested_date)}
          {r.extended_date && (
            <span className="text-xs text-gray-400 ml-1">(extended)</span>
          )}
        </span>
      ),
    },
    { key: 'reason', label: 'Reason', render: (r) => truncate(r.reason, 30) },
    {
      key: 'refund_amount',
      label: 'Refund',
      render: (r) => r.refund_amount ? formatCurrency(r.refund_amount) : '—',
    },
    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'created_at', label: 'Created', render: (r) => formatDate(r.created_at) },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        <div className="flex gap-1 flex-wrap">
          {(r.status === 'requested' || r.status === 'clearance') && (
            <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); openExtend(r); }}>
              <Clock className="w-3 h-3 mr-1" /> Extend
            </Button>
          )}
          {r.status === 'requested' && (
            <Button size="sm" variant="secondary" onClick={(e) => { e.stopPropagation(); handleClearance(r.id); }}>
              <FileCheck className="w-3 h-3 mr-1" /> Clearance
            </Button>
          )}
          {r.status === 'clearance' && (
            <Button size="sm" variant="primary" onClick={(e) => { e.stopPropagation(); handleFinalize(r.id); }}>
              <Calculator className="w-3 h-3 mr-1" /> Finalize
            </Button>
          )}
          {r.status === 'refund_pending' && (
            <Button size="sm" variant="success" onClick={(e) => { e.stopPropagation(); handleComplete(r.id); }}>
              <CheckCircle2 className="w-3 h-3 mr-1" /> Complete
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Move-Out Settlement"
        subtitle="Clearance, final billing, refund processing, and move-out scheduling"
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4 mr-1" /> New Move-Out
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4 items-end">
        <select
          value={filters.status}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {MOVEOUT_STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <input
          type="text"
          placeholder="Filter by Resident ID..."
          value={filters.resident_id}
          onChange={(e) => setFilters((f) => ({ ...f, resident_id: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm w-56"
        />
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <select
            value={filters.year}
            onChange={(e) => setFilters((f) => ({ ...f, year: e.target.value }))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">All Years</option>
            {Array.from({ length: 5 }, (_, i) => 2024 + i).map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <select
            value={filters.month}
            onChange={(e) => setFilters((f) => ({ ...f, month: e.target.value }))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">All Months</option>
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i + 1} value={i + 1}>
                {new Date(2000, i, 1).toLocaleString('default', { month: 'long' })}
              </option>
            ))}
          </select>
        </div>
        <Button variant="ghost" onClick={fetchData}><RefreshCw className="w-4 h-4" /></Button>
      </div>

      {/* End-of-month alert banner */}
      {data.some((r) => r.is_end_of_month_flag && r.status !== 'completed') && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4 flex items-center gap-2 text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span className="font-medium">Attention:</span>
          <span>{data.filter((r) => r.is_end_of_month_flag && r.status !== 'completed').length} move-out(s) scheduled at end of month.</span>
        </div>
      )}

      <DataTable columns={columns} data={data} loading={loading} emptyMessage="No move-out requests" />

      {/* Create Modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="New Move-Out Request">
        <form onSubmit={handleCreate} className="space-y-4">
          <FormField label="Resident ID" name="resident_id" required value={form.resident_id}
            onChange={(e) => setForm({ ...form, resident_id: e.target.value })} placeholder="UUID of resident" />
          <FormField label="Requested Date" name="requested_date" type="date" required value={form.requested_date}
            onChange={(e) => setForm({ ...form, requested_date: e.target.value })} />
          <FormField label="Actual Move-Out Date (optional)" name="actual_date" type="date" value={form.actual_date}
            onChange={(e) => setForm({ ...form, actual_date: e.target.value })} />
          <FormField label="Reason" name="reason" type="textarea" value={form.reason}
            onChange={(e) => setForm({ ...form, reason: e.target.value })} placeholder="Reason for moving out" />
          <FormField label="Forwarding Contact" name="forwarding_contact" value={form.forwarding_contact}
            onChange={(e) => setForm({ ...form, forwarding_contact: e.target.value })} placeholder="Phone or email for refund" />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button type="submit" loading={submitting}>Submit Request</Button>
          </div>
        </form>
      </Modal>

      {/* Extend Modal */}
      <Modal isOpen={showExtend} onClose={() => { setShowExtend(false); setExtendTarget(null); }} title="Extend Move-Out Date">
        {extendTarget && (
          <form onSubmit={handleExtend} className="space-y-4">
            <p className="text-sm text-gray-600">
              Extending move-out for <strong>{extendTarget.resident_name || shortUUID(extendTarget.resident_id)}</strong>
            </p>
            <div className="bg-gray-50 rounded-md p-3 text-sm space-y-1">
              <p><span className="text-gray-500">Current date:</span> <span className="font-medium">{formatDate(extendTarget.extended_date || extendTarget.actual_date || extendTarget.requested_date)}</span></p>
              {extendTarget.extension_reason && (
                <p><span className="text-gray-500">Previous reason:</span> {extendTarget.extension_reason}</p>
              )}
            </div>
            <FormField label="New Move-Out Date" name="extended_date" type="date" required value={extendForm.extended_date}
              onChange={(e) => setExtendForm({ ...extendForm, extended_date: e.target.value })} />
            <FormField label="Extension Reason" name="extension_reason" type="textarea" value={extendForm.extension_reason}
              onChange={(e) => setExtendForm({ ...extendForm, extension_reason: e.target.value })} placeholder="Why is this being extended?" />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => setShowExtend(false)}>Cancel</Button>
              <Button type="submit" loading={submitting}>Save Extension</Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
