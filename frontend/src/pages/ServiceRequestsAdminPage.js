import React, { useEffect, useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { RefreshCw, UserCheck } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import FormField from '../components/ui/FormField';
import { listServiceRequests, updateServiceRequestStatus, assignServiceRequest } from '../api/serviceRequests';
import { SERVICE_REQUEST_STATUSES, SERVICE_REQUEST_CATEGORIES, SERVICE_REQUEST_PRIORITIES } from '../utils/constants';
import { formatDateTime, truncate, shortUUID } from '../utils/formatters';

export default function ServiceRequestsAdminPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', category: '', priority: '' });
  const [submitting, setSubmitting] = useState(false);
  const [resolveModal, setResolveModal] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [assignModal, setAssignModal] = useState(null);
  const [assigneeName, setAssigneeName] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.category) params.category = filters.category;
      if (filters.priority) params.priority = filters.priority;
      const result = await listServiceRequests(params);
      setData(result);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleStatusChange = async (row, newStatus) => {
    if (newStatus === 'resolved') {
      setResolveModal({ id: row.id, currentStatus: row.status });
      return;
    }

    try {
      await updateServiceRequestStatus(row.id, { status: newStatus });
      toast.success(`Status updated to ${newStatus.replace(/_/g, ' ')}`);
      fetchData();
    } catch {
      // error handled by interceptor
    }
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!resolveModal) return;
    setSubmitting(true);
    try {
      await updateServiceRequestStatus(resolveModal.id, { status: 'resolved', resolution_notes: resolutionNotes });
      toast.success('Status updated to resolved');
      setResolveModal(null);
      setResolutionNotes('');
      fetchData();
    } catch {
      // error handled by interceptor
    } finally {
      setSubmitting(false);
    }
  };

  const openAssignModal = (row) => {
    setAssignModal(row);
    setAssigneeName(row.assigned_to || '');
  };

  const handleAssignSubmit = async (e) => {
    e.preventDefault();
    if (!assignModal) return;
    setSubmitting(true);
    try {
      await assignServiceRequest(assignModal.id, { assigned_to: assigneeName });
      toast.success('Service request assigned');
      setAssignModal(null);
      setAssigneeName('');
      fetchData();
    } catch {
      // error handled by interceptor
    } finally {
      setSubmitting(false);
    }
  };

  const priorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'text-red-600 font-bold';
      case 'high': return 'text-orange-600 font-semibold';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const columns = [
    {
      key: 'created_at',
      label: 'Date',
      render: (r) => formatDateTime(r.created_at),
    },
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
      key: 'category',
      label: 'Category',
      render: (r) => <span className="capitalize">{r.category?.replace(/_/g, ' ') || '—'}</span>,
    },
    {
      key: 'subject',
      label: 'Subject',
      render: (r) => (
        <span title={r.subject} className="cursor-default">{truncate(r.subject, 35)}</span>
      ),
    },
    {
      key: 'priority',
      label: 'Priority',
      render: (r) => <span className={`capitalize ${priorityColor(r.priority)}`}>{r.priority || '—'}</span>,
    },
    {
      key: 'status',
      label: 'Status',
      render: (r) => (
        <select
          value={r.status}
          onChange={(e) => handleStatusChange(r, e.target.value)}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs capitalize"
          onClick={(e) => e.stopPropagation()}
        >
          {SERVICE_REQUEST_STATUSES.filter((s) => s.value).map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      ),
    },
    {
      key: 'location',
      label: 'Location',
      render: (r) => <span className="text-sm text-gray-600">{r.location || '—'}</span>,
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        <div className="flex flex-wrap gap-1">
          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); openAssignModal(r); }}>
            <UserCheck className="w-3 h-3 mr-1" /> Assign
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Service Requests"
        subtitle="Manage maintenance, repairs, and resident service requests"
        actions={
          <Button onClick={fetchData}>
            <RefreshCw className="w-4 h-4 mr-1" /> Refresh
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={filters.status}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {SERVICE_REQUEST_STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <select
          value={filters.category}
          onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {SERVICE_REQUEST_CATEGORIES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <select
          value={filters.priority}
          onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {SERVICE_REQUEST_PRIORITIES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <Button variant="ghost" onClick={fetchData}><RefreshCw className="w-4 h-4" /></Button>
      </div>

      <DataTable columns={columns} data={data} loading={loading} emptyMessage="No service requests found" />

      {/* Resolve Modal */}
      <Modal isOpen={!!resolveModal} onClose={() => { setResolveModal(null); setResolutionNotes(''); }} title="Resolve Service Request">
        {resolveModal && (
          <form onSubmit={handleResolveSubmit} className="space-y-4">
            <p className="text-sm text-gray-600">
              You are marking this service request as <strong>resolved</strong>. Please enter resolution notes below.
            </p>
            <FormField
              label="Resolution Notes"
              name="resolution_notes"
              type="textarea"
              required
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Describe how the issue was resolved..."
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => { setResolveModal(null); setResolutionNotes(''); }}>Cancel</Button>
              <Button type="submit" loading={submitting}>Mark Resolved</Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Assign Modal */}
      <Modal isOpen={!!assignModal} onClose={() => { setAssignModal(null); setAssigneeName(''); }} title="Assign Service Request">
        {assignModal && (
          <form onSubmit={handleAssignSubmit} className="space-y-4">
            <p className="text-sm text-gray-600">
              Assigning service request for <strong>{assignModal.subject}</strong>
            </p>
            <FormField
              label="Assign To"
              name="assigned_to"
              type="text"
              required
              value={assigneeName}
              onChange={(e) => setAssigneeName(e.target.value)}
              placeholder="Staff name or ID"
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => { setAssignModal(null); setAssigneeName(''); }}>Cancel</Button>
              <Button type="submit" loading={submitting}>Assign</Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
