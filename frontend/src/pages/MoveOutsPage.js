import React, { useEffect, useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import {
  Plus, FileCheck, Calculator, CheckCircle2, RefreshCw, Calendar, AlertTriangle, Clock,
  ChevronDown, ChevronUp, User, GraduationCap, Building2, FileText, Tag,
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import FormField from '../components/ui/FormField';
import StatusBadge from '../components/ui/StatusBadge';
import {
  listMoveOuts, createMoveOut, generateClearance, finalizeMoveOut, completeMoveOut, extendMoveOut,
} from '../api/moveouts';
import { MOVEOUT_STATUSES } from '../utils/constants';
import { formatDate, formatCurrency, shortUUID, truncate } from '../utils/formatters';

function ResidentDetailCard({ r }) {
  return (
    <div className="bg-gray-50 border-t border-gray-200 p-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
        <div className="space-y-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5" /> Identification
          </h4>
          <p className="text-gray-600"><span className="text-gray-400">Type:</span> {r.id_type || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Number:</span> {r.id_number || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Address:</span> {r.address || '—'}</p>
        </div>
        <div className="space-y-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <GraduationCap className="w-3.5 h-3.5" /> Academic / Professional
          </h4>
          <p className="text-gray-600"><span className="text-gray-400">School:</span> {r.school || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Course:</span> {r.course || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Review Center:</span> {r.review_center || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Board Exam:</span> {r.board_exam_type || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Exam Date:</span> {r.exam_date || '—'}</p>
        </div>
        <div className="space-y-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5" /> Profile
          </h4>
          <p className="text-gray-600"><span className="text-gray-400">Source:</span> {r.source || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Location:</span> {r.location || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Dormer Type:</span> {r.dormer_type ? r.dormer_type.replace('_', ' ') : '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Lease Term:</span> {r.lease_term_months ? `${r.lease_term_months} month(s)` : '—'}</p>
        </div>
        <div className="space-y-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5" /> Accommodation
          </h4>
          <p className="text-gray-600"><span className="text-gray-400">Room Type:</span> {r.room_type || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Bed Type:</span> {r.bed_type || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Monthly Rate:</span> {r.monthly_rate ? `₱${Number(r.monthly_rate).toLocaleString()}` : '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Deposit Paid:</span> {r.deposit_paid ? `₱${Number(r.deposit_paid).toLocaleString()}` : '—'}</p>
        </div>
        <div className="space-y-2 sm:col-span-2 lg:col-span-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" /> Dates
          </h4>
          <div className="flex flex-wrap gap-x-6 gap-y-1">
            <p className="text-gray-600"><span className="text-gray-400">Move-in:</span> {r.move_in_date || '—'}</p>
            <p className="text-gray-600"><span className="text-gray-400">Contract End:</span> {r.contract_end_date || '—'}</p>
            <p className="text-gray-600"><span className="text-gray-400">Requested:</span> {r.requested_date || '—'}</p>
            <p className="text-gray-600"><span className="text-gray-400">Actual:</span> {r.actual_date || '—'}</p>
            <p className="text-gray-600"><span className="text-gray-400">Created:</span> {r.created_at ? new Date(r.created_at).toLocaleDateString('en-PH') : '—'}</p>
          </div>
        </div>
      </div>
      {r.reason && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-sm text-gray-600"><span className="text-gray-400">Reason:</span> {r.reason}</p>
        </div>
      )}
      {r.forwarding_contact && (
        <div className="mt-2">
          <p className="text-sm text-gray-600"><span className="text-gray-400">Forwarding Contact:</span> {r.forwarding_contact}</p>
        </div>
      )}
    </div>
  );
}

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
  const [expandedId, setExpandedId] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.resident_id) params.resident_id = filters.resident_id;
      if (filters.year) params.year = Number(filters.year);
      if (filters.month) params.month = Number(filters.month);
      const result = await listMoveOuts(params);
      setData(Array.isArray(result) ? result : []);
    } catch {
      toast.error('Failed to load move-outs');
      setData([]);
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
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to create move-out request';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleClearance = async (id) => {
    try {
      await generateClearance(id);
      toast.success('Clearance generated with final billing');
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate clearance';
      toast.error(msg);
    }
  };

  const handleFinalize = async (id) => {
    try {
      await finalizeMoveOut(id);
      toast.success('Move-out finalized, submitted to accounting');
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to finalize move-out';
      toast.error(msg);
    }
  };

  const handleComplete = async (id) => {
    try {
      await completeMoveOut(id);
      toast.success('Move-out completed');
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to complete move-out';
      toast.error(msg);
    }
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

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

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

      {/* Data Table with expandable rows */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading move-outs...</div>
        ) : data.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No move-out requests</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3 text-left">Resident</th>
                  <th className="px-4 py-3 text-left">Requested Date</th>
                  <th className="px-4 py-3 text-left">Actual Date</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Refund</th>
                  <th className="px-4 py-3 text-left">Actions</th>
                  <th className="px-4 py-3 text-left w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((r) => (
                  <React.Fragment key={r.id}>
                    <tr
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => toggleExpand(r.id)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600">
                            <User className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{r.resident_name || shortUUID(r.resident_id)}</p>
                            <p className="text-xs text-gray-500">
                              {r.dormer_type ? r.dormer_type.replace('_', ' ') : ''}
                              {r.dormer_type && r.school ? ' · ' : ''}
                              {r.school || ''}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <span>{formatDate(r.requested_date)}</span>
                          {r.is_end_of_month_flag && (
                            <span title="End-of-month move-out" className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700">
                              <AlertTriangle className="w-3 h-3 mr-0.5" /> EOM
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={r.extended_date ? 'text-blue-600 font-medium' : ''}>
                          {formatDate(r.extended_date || r.actual_date || r.requested_date)}
                          {r.extended_date && (
                            <span className="text-xs text-gray-400 ml-1">(extended)</span>
                          )}
                        </span>
                      </td>
                      <td className="px-4 py-3"><StatusBadge status={r.status} /></td>
                      <td className="px-4 py-3">
                        {r.refund_amount ? formatCurrency(r.refund_amount) : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1 flex-wrap" onClick={(e) => e.stopPropagation()}>
                          {(r.status === 'requested' || r.status === 'clearance') && (
                            <Button size="sm" variant="ghost" onClick={() => openExtend(r)}>
                              <Clock className="w-3 h-3 mr-1" /> Extend
                            </Button>
                          )}
                          {r.status === 'requested' && (
                            <Button size="sm" variant="secondary" onClick={() => handleClearance(r.id)}>
                              <FileCheck className="w-3 h-3 mr-1" /> Clearance
                            </Button>
                          )}
                          {r.status === 'clearance' && (
                            <Button size="sm" variant="primary" onClick={() => handleFinalize(r.id)}>
                              <Calculator className="w-3 h-3 mr-1" /> Finalize
                            </Button>
                          )}
                          {r.status === 'refund_pending' && (
                            <Button size="sm" variant="success" onClick={() => handleComplete(r.id)}>
                              <CheckCircle2 className="w-3 h-3 mr-1" /> Complete
                            </Button>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {expandedId === r.id ? (
                          <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                      </td>
                    </tr>
                    {expandedId === r.id && (
                      <tr>
                        <td colSpan={7} className="p-0">
                          <ResidentDetailCard r={r} />
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

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
